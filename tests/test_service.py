import io
import json
from pathlib import Path
import subprocess
import threading
from zipfile import ZipFile

from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest

from service import api


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "missing_models", lambda: [])
    monkeypatch.setattr(api, "validate_media", lambda *args: None)
    monkeypatch.setattr(api, "PROCESS_SLOT", threading.BoundedSemaphore(1))
    monkeypatch.setattr(api.tempfile, "tempdir", str(tmp_path))
    with TestClient(api.app) as client:
        yield client
    assert list(tmp_path.iterdir()) == [], "Request workspace was not cleaned up"


def fake_analysis(command, output, video, rgb, log_path):
    (output / "detection/crops").mkdir(parents=True)
    name = "5fps_thermal_processed.mp4" if video else "thermal_processed.jpg"
    (output / "detection" / name).write_bytes(b"processed media")
    if rgb:
        (output / ("overlay.mp4" if video else "overlay.jpg")).write_bytes(b"overlay")


def files(rgb=False):
    result = {"thermal": ("../../thermal.JPG", b"thermal", "image/jpeg")}
    if rgb:
        result.update({
            "rgb": ("rgb.jpg", b"rgb", "image/jpeg"),
            "calibration": ("calibration.json", json.dumps({"scale_factor": 1.75, "offset_x": 82, "offset_y": -93}), "application/json"),
        })
    return result


def test_archive_contract_and_isolation(client, monkeypatch):
    commands = []

    def analysis(command, *args):
        commands.append(command)
        fake_analysis(command, *args)

    monkeypatch.setattr(api, "run_analysis", analysis)
    ids = []
    for _ in range(2):
        response = client.post("/inspect", files=files())
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        with ZipFile(io.BytesIO(response.content)) as bundle:
            manifest = json.loads(bundle.read("result.json"))
            assert manifest["report"] is None
            assert manifest["saved_defect_panels"] == 0
            assert manifest["status"] == "completed"
            assert manifest["files"] == ["detection/thermal_processed.jpg"]
            assert set(bundle.namelist()) == {"result.json", *manifest["files"]}
            assert response.headers["x-request-id"] == manifest["request_id"]
            ids.append(manifest["request_id"])
    assert ids[0] != ids[1]
    paths = [Path(command[command.index("--thermal-input") + 1]) for command in commands]
    assert paths[0].parent != paths[1].parent
    assert all(path.name == "thermal.jpg" for path in paths)


def test_rgb_and_report(client, monkeypatch):
    def analysis(command, output, *args):
        assert "--rgb-input" in command
        calibration = Path(command[command.index("--calibration-file") + 1])
        assert json.loads(calibration.read_text())["scale_factor"] == 1.75
        fake_analysis(command, output, *args)
        (output / "detection/crops/thermal_panel_0_defect_thermal.jpg").write_bytes(b"crop")
        (output / "report.pdf").write_bytes(b"%PDF")

    monkeypatch.setattr(api, "run_analysis", analysis)
    response = client.post("/inspect", data={"mode": "photo-rgb-thermal"}, files=files(rgb=True))
    assert response.status_code == 200
    with ZipFile(io.BytesIO(response.content)) as bundle:
        result = json.loads(bundle.read("result.json"))
        assert result["saved_defect_panels"] == 1
        assert result["report"] == "report.pdf"
        assert "overlay.jpg" in result["files"]


@pytest.mark.parametrize("mode", ["video-thermal", "video-rgb-thermal"])
def test_video_modes(client, monkeypatch, mode):
    monkeypatch.setattr(api, "run_analysis", fake_analysis)
    uploads = files(rgb="rgb" in mode)
    uploads["thermal"] = ("thermal.mp4", b"video", "video/mp4")
    if "rgb" in mode:
        uploads["rgb"] = ("rgb.mp4", b"video", "video/mp4")
    response = client.post("/inspect", data={"mode": mode}, files=uploads)
    assert response.status_code == 200


@pytest.mark.parametrize("mode,rgb", [("unknown", False), ("photo-rgb-thermal", False), ("photo-thermal", True)])
def test_invalid_mode_or_missing_inputs(client, mode, rgb):
    assert client.post("/inspect", data={"mode": mode}, files=files(rgb=rgb)).status_code == 422


@pytest.mark.parametrize("payload", [b"not-json", b"[]", b"{}", b'{"scale_factor":0,"offset_x":0,"offset_y":0}', b'{"scale_factor":1,"offset_x":NaN,"offset_y":0}'])
def test_bad_calibration(client, payload):
    uploads = files(rgb=True)
    uploads["calibration"] = ("calibration.json", payload)
    assert client.post("/inspect", data={"mode": "photo-rgb-thermal"}, files=uploads).status_code == 422


def test_upload_limits_and_extension(client, monkeypatch):
    monkeypatch.setattr(api, "MAX_UPLOAD_BYTES", 3)
    assert client.post("/inspect", files=files()).status_code == 413
    monkeypatch.setattr(api, "MAX_UPLOAD_BYTES", 1000)
    assert client.post("/inspect", files={"thermal": ("bad.exe", b"bad")}).status_code == 422
    assert client.post("/inspect", files={"thermal": ("empty.jpg", b"")}).status_code == 422


def test_model_readiness(client, monkeypatch):
    monkeypatch.setattr(api, "missing_models", lambda: ["missing.pt"])
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 503
    assert client.post("/inspect", files=files()).status_code == 503


def test_busy_container(client):
    with api.PROCESS_SLOT:
        response = client.post("/inspect", files=files())
    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"


def test_failure_cleanup_and_next_request(client, monkeypatch):
    def fail(*args):
        raise HTTPException(504, "timeout")

    monkeypatch.setattr(api, "run_analysis", fail)
    response = client.post("/inspect", files=files())
    assert response.status_code == 504
    assert "x-request-id" in response.headers
    monkeypatch.setattr(api, "run_analysis", fake_analysis)
    assert client.post("/inspect", files=files()).status_code == 200


@pytest.mark.parametrize("failure", ["timeout", "exit", "missing", "missing_report"])
def test_cli_failure_detection(monkeypatch, tmp_path, failure):
    def run(*args, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired("main.py", 1)
        return subprocess.CompletedProcess([], 1 if failure == "exit" else 0)

    monkeypatch.setattr(api.subprocess, "run", run)
    monkeypatch.setattr(api, "validate_media", lambda *args: None)
    if failure == "missing_report":
        (tmp_path / "detection/crops").mkdir(parents=True)
        (tmp_path / "detection/thermal_processed.jpg").write_bytes(b"media")
        (tmp_path / "detection/crops/panel_0_thermal.jpg").write_bytes(b"crop")
    with pytest.raises(HTTPException) as error:
        api.run_analysis(["fake-cli"], tmp_path, False, False, tmp_path / "processing.log")
    assert error.value.status_code == (504 if failure == "timeout" else 500)
