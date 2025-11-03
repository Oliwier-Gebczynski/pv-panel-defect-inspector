from ultralytics import YOLO
import cv2


def detect_on_video(video_path, model_path="models/panel_detector_gpu/weights/best.pt"):
    model = YOLO(model_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video file: {video_path}")
        return

    print("Starting detection... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(source=frame, conf=0.5, verbose=False)
        annotated_frame = results[0].plot()

        cv2.imshow("Panel Detector", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Detection finished.")


if __name__ == "__main__":
    detect_on_video("../../data/processed/5fps/5fps_rgb.mp4")
