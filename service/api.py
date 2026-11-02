"""Stateless HTTP boundary; all inference remains in main.py and core/."""

import json
import logging
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Annotated, Literal
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask

ROOT = Path(__file__).resolve().parents[1]
MODEL_FILES = tuple(
    ROOT / "core/detection/models" / name / "weights/best.pt"
    for name in ("panel_detector_gpu_thermal", "panel_detector_gpu", "panel_defect_thermal")
)
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "100")) * 1024 * 1024
PROCESS_TIMEOUT_SECONDS = int(os.getenv("PROCESS_TIMEOUT_SECONDS", "900"))
# One inference per container. Scale containers rather than loading many model sets.
PROCESS_SLOT = threading.BoundedSemaphore(1)
LOGGER = logging.getLogger("uvicorn.error")
Mode = Literal["photo-thermal", "photo-rgb-thermal", "video-thermal", "video-rgb-thermal"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

app = FastAPI(title="PV Panel Defect Inspector", version="1.0.0")


def missing_models() -> list[str]:
    return [str(path.relative_to(ROOT)) for path in MODEL_FILES if not path.is_file()]


@app.get("/health")
def health():
    """Liveness only; /ready additionally checks the model mount."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    missing = missing_models()
    return JSONResponse(
        {"status": "not_ready" if missing else "ready", "missing_models": missing},
        status_code=503 if missing else 200,
    )


def save_upload(upload: UploadFile, directory: Path, name: str, video: bool) -> Path:
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in (VIDEO_EXTENSIONS if video else IMAGE_EXTENSIONS):
        raise HTTPException(422, f"Unsupported file extension for {name}.")
    # Never use the client filename as a filesystem path or command argument.
    target = directory / f"{name}{extension}"
    with target.open("wb") as output:
        shutil.copyfileobj(upload.file, output, length=1024 * 1024)
    validate_media(target, video)
    return target


def validate_media(path: Path, video: bool):
    import cv2

    if video:
        capture = cv2.VideoCapture(str(path))
        try:
            valid, frame = capture.read()
            valid = valid and frame is not None
        finally:
            capture.release()
    else:
        valid = cv2.imread(str(path)) is not None
    if not valid:
        raise HTTPException(422, f"Cannot decode media: {path.name}.")


def save_calibration(upload: UploadFile, directory: Path) -> Path:
    try:
        data = json.load(upload.file)
        for key in ("scale_factor", "offset_x", "offset_y"):
            value = data[key]
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(key)
        if data["scale_factor"] <= 0:
            raise ValueError("scale_factor")
    except (ValueError, KeyError, TypeError, OverflowError) as error:
        raise HTTPException(422, "Invalid calibration JSON; expected finite scale_factor > 0, offset_x, offset_y.") from error
    target = directory / "calibration.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    return target


def run_analysis(command: list[str], output: Path, video: bool, rgb: bool, log_path: Path):
    with log_path.open("wb") as log:
        try:
            result = subprocess.run(
                command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                timeout=PROCESS_TIMEOUT_SECONDS, check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise HTTPException(504, "Analysis exceeded the processing time limit.") from error
    if result.returncode:
        raise HTTPException(500, "Analysis failed; see the container logs using the request ID.")

    # The original CLI sometimes prints an error and exits with code zero.
    # Check its artifacts rather than treating that exit code as success.
    expected = output / "detection" / ("5fps_thermal_processed.mp4" if video else "thermal_processed.jpg")
    artifacts = [expected]
    if rgb:
        artifacts.append(output / ("overlay.mp4" if video else "overlay.jpg"))
    for path in artifacts:
        if not path.is_file() or path.stat().st_size == 0:
            raise HTTPException(500, "Analysis did not produce the expected output.")
        try:
            validate_media(path, video)
        except HTTPException as error:
            raise HTTPException(500, "Analysis produced unreadable output.") from error
    crops = list((output / "detection/crops").glob("*thermal.jpg"))
    if crops and not (output / "report.pdf").is_file():
        raise HTTPException(500, "Analysis found defects but did not generate the PDF report.")


@app.post(
    "/inspect", response_class=FileResponse,
    responses={200: {"content": {"application/zip": {}}, "description": "ZIP with result.json and generated artifacts"}},
)
def inspect(
    thermal: Annotated[UploadFile, File(description="Thermal image or video")],
    mode: Annotated[Mode, Form()] = "photo-thermal",
    rgb: Annotated[UploadFile | None, File()] = None,
    calibration: Annotated[UploadFile | None, File()] = None,
):
    use_rgb = "rgb" in mode
    video = mode.startswith("video-")
    if use_rgb and (rgb is None or calibration is None):
        raise HTTPException(422, "RGB modes require both rgb and calibration files.")
    if not use_rgb and (rgb is not None or calibration is not None):
        raise HTTPException(422, "Use an RGB mode when supplying rgb or calibration files.")
    uploads = [upload for upload in (thermal, rgb, calibration) if upload is not None]
    if any(not upload.size for upload in uploads):
        raise HTTPException(422, "Input files must not be empty.")
    if sum(upload.size for upload in uploads) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Combined input files exceed MAX_UPLOAD_MB.")
    missing = missing_models()
    if missing:
        raise HTTPException(503, {"message": "Model weights are missing.", "missing_models": missing})
    if not PROCESS_SLOT.acquire(blocking=False):
        raise HTTPException(503, "Container is busy; retry later.", headers={"Retry-After": "5"})

    workspace = None
    request_id = uuid4().hex
    started = time.monotonic()
    try:
        workspace = Path(tempfile.mkdtemp(prefix="pv-inspection-"))
        output = workspace / "output"
        output.mkdir()
        thermal_path = save_upload(thermal, workspace, "thermal", video)
        command = [
            sys.executable, str(ROOT / "main.py"), "process", "--mode", mode,
            "--thermal-input", str(thermal_path), "--output-dir", str(output),
            "--calibration-file", str(workspace / "calibration.json"),
        ]
        if use_rgb:
            rgb_path = save_upload(rgb, workspace, "rgb", video)
            save_calibration(calibration, workspace)
            command.extend(["--rgb-input", str(rgb_path)])
        log_path = workspace / "processing.log"
        try:
            run_analysis(command, output, video, use_rgb, log_path)
        finally:
            if log_path.exists():
                LOGGER.info("Inspection %s CLI output:\n%s", request_id, log_path.read_text(errors="replace"))

        files = sorted(path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file())
        crops = [name for name in files if name.startswith("detection/crops/") and name.endswith("thermal.jpg")]
        manifest = {
            "schema_version": 1,
            "request_id": request_id,
            "status": "completed",
            "mode": mode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "saved_defect_panels": len(crops),
            "report": "report.pdf" if "report.pdf" in files else None,
            "files": files,
        }
        (output / "result.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        archive = workspace / "results.zip"
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
            for path in sorted(output.rglob("*")):
                if path.is_file():
                    bundle.write(path, path.relative_to(output).as_posix())
        return FileResponse(
            archive, media_type="application/zip", filename=f"inspection-{request_id}.zip",
            headers={"X-Request-ID": request_id},
            background=BackgroundTask(shutil.rmtree, workspace),
        )
    except Exception as error:
        if workspace is not None:
            shutil.rmtree(workspace, ignore_errors=True)
        LOGGER.exception("Inspection %s failed", request_id)
        if isinstance(error, HTTPException):
            error.headers = {**(error.headers or {}), "X-Request-ID": request_id}
        raise
    finally:
        PROCESS_SLOT.release()
