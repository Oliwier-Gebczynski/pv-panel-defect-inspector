FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    YOLO_CONFIG_DIR=/tmp/ultralytics \
    MPLCONFIGDIR=/tmp/matplotlib \
    OMP_NUM_THREADS=1

WORKDIR /app

# ffprobe is used by the existing video pipeline; OpenCV needs these libraries.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# CPU variant avoids downloading CUDA libraries and runs without an NVIDIA GPU.
RUN pip install --no-cache-dir torch==2.7.0 torchvision==0.22.0 \
    --index-url https://download.pytorch.org/whl/cpu
COPY service/requirements.txt /app/service/requirements.txt
RUN pip install --no-cache-dir -r service/requirements.txt

COPY main.py /app/main.py
COPY core /app/core
COPY service /app/service

RUN useradd --uid 10001 --create-home inspector \
    && mkdir -p /app/core/detection/models
USER inspector

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"

CMD ["uvicorn", "service.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
