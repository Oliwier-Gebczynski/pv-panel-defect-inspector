from ultralytics import YOLO

def train_model():
    """Trains a YOLO model on a custom dataset."""
    model = YOLO()
    model.train(
        data="data.yaml",
        epochs=100,
        imgsz=640,
        batch=4,
        device=0,
        workers=2,
        cache=False,
        project="models",
        name="panel_defect_thermal"
    )

if __name__ == "__main__":
    train_model()