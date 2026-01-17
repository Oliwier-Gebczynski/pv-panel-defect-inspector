from ultralytics import YOLO
import cv2
import os

from tools.normalize_filenames import FOLDER_PATH

class PanelDetector:
    """A class to detect and track panels in videos and images."""

    def __init__(self, model_path, output_dir="../../data/processed/after_detection/output",
                 cropped_dir="../../data/processed/cropped_panel"):
        """Initializes the PanelDetector.

        Args:
            model_path: The path to the YOLO model file.
            output_dir: The directory to save annotated videos and images.
            cropped_dir: The directory to save cropped panel images.
        """
        self.model = YOLO(model_path)

        self.output_dir = output_dir
        self.cropped_dir = cropped_dir

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cropped_dir, exist_ok=True)

    def annotate_frame(self, frame, boxes, track_ids, confs):
        """Annotates a frame with bounding boxes, track IDs, and confidences.

        Args:
            frame: The input frame.
            boxes: A list of bounding boxes.
            track_ids: A list of track IDs.
            confs: A list of confidences.

        Returns:
            The annotated frame.
        """
        annotated = frame.copy()

        for box, track_id, conf in zip(boxes, track_ids, confs):
            x1, y1, x2, y2 = map(int, box)
            confidence = float(conf)

            cv2.putText(annotated, f"ID: {int(track_id)} ({confidence:.2f})",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 255, 0), 2)
        return annotated

    def save_crop(self, frame, box, track_id, confidence, frame_idx):
        """Saves a cropped image of a detected panel.

        Args:
            frame: The input frame.
            box: The bounding box of the panel.
            track_id: The track ID of the panel.
            confidence: The confidence of the detection.
            frame_idx: The index of the frame.
        """
        x1, y1, x2, y2 = map(int, box)
        cropped = frame[y1:y2, x1:x2]

        if cropped.size == 0:
            return

        filename = os.path.join(
            self.cropped_dir,
            f"panel_{frame_idx}_id{track_id}_conf{confidence:.2f}.jpg"
        )
        cv2.imwrite(filename, cropped)

    def detect_from_video(self, video_path, conf_threshold=0.75):
        """Detects and tracks panels in a video.

        Args:
            video_path: The path to the input video file.
            conf_threshold: The confidence threshold for saving cropped panels.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Cannot open video file: {video_path}")
            return

        output_path = os.path.join(self.output_dir, "tracked_output.mp4")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_idx = 0
        saved = 0

        print(f"Starting detection on video: {video_path}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = self.model.track(source=frame, conf=0.5, persist=True, verbose=False)
            boxes = results[0].boxes.xyxy
            track_ids = results[0].boxes.id
            confs = results[0].boxes.conf

            if track_ids is not None:
                annotated = self.annotate_frame(frame, boxes, track_ids, confs)

                for box, track_id, conf in zip(boxes, track_ids, confs):
                    confidence = float(conf)

                    if confidence >= conf_threshold:
                        self.save_crop(frame, box, int(track_id), confidence, frame_idx)
                        saved += 1
            else:
                annotated = frame

            out.write(annotated)
            cv2.imshow("Panel Tracking", annotated)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            frame_idx += 1

        cap.release()
        out.release()
        cv2.destroyAllWindows()

        print(f"Saved {saved} crops.")
        print(f"Output video: {output_path}")

    def detect_from_folder(self, folder_path, conf_threshold=0.75):
        """Detects panels in images in a folder.

        Args:
            folder_path: The path to the folder containing the images.
            conf_threshold: The confidence threshold for saving cropped panels.
        """
        print(f"Running detection on images in folder: {folder_path}")

        images = [f for f in os.listdir(folder_path)
                  if f.lower().endswith((".jpg", ".png", ".jpeg"))]

        saved = 0
        idx = 0

        for img_name in images:
            img_path = os.path.join(folder_path, img_name)
            frame = cv2.imread(img_path)

            if frame is None:
                continue

            results = self.model.predict(frame, conf=0.5)
            boxes = results[0].boxes.xyxy
            confs = results[0].boxes.conf
            ids = range(len(boxes))

            annotated = self.annotate_frame(frame, boxes, ids, confs)

            for box, conf, track_id in zip(boxes, confs, ids):
                confidence = float(conf)

                if confidence >= conf_threshold:
                    self.save_crop(frame, box, track_id, confidence, idx)
                    saved += 1

            save_path = os.path.join(self.output_dir, f"annotated_{img_name}")
            cv2.imwrite(save_path, annotated)

            idx += 1

        print(f"Folder detection complete. Saved {saved} crops.")


# if __name__ == "__main__":
#     FOLDER_PATH = "../../data/raw/rgb/poli"
#     detector = PanelDetector("models/panel_detector_gpu/weights/best.pt")

#     detector.detect_from_folder(FOLDER_PATH)
