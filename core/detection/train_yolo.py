from ultralytics import YOLO

def train_model():
    model = YOLO("yolov8s.pt")
    model.train(
        data="dataset.yaml",
        epochs=100,
        imgsz=640,
        batch=4,
        device=0,  # GPU nr 0
        workers=2,
        cache=False,
        project="models",
        name="panel_detector_gpu"
    )

if __name__ == "__main__":
    train_model()
