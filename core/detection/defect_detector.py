import cv2
import os
import math
import json
import numpy as np
from ultralytics import YOLO

class ThermalDefectDetector:
    def __init__(self,
                 panel_model_path: str,
                 panel_model_rgb_path: str,
                 defect_model_path: str,
                 calibration_path: str = None,
                 output_dir: str = "output",
                 conf_threshold: float = 0.5):
        """
        Initializes the ThermalDefectDetector.

        Args:
            panel_model_path (str): Path to the thermal panel detection model.
            panel_model_rgb_path (str): Path to the RGB panel detection model.
            defect_model_path (str): Path to the defect detection model.
            calibration_path (str, optional): Path to the calibration JSON file. Defaults to None.
            output_dir (str, optional): Directory to save output files. Defaults to "output".
            conf_threshold (float, optional): Confidence threshold for YOLO models. Defaults to 0.5.
        """
        self.output_dir = output_dir
        self.crops_dir = os.path.join(self.output_dir, "crops")
        self.conf_threshold = conf_threshold
        self.recent_defects = []
        self.DUPLICATE_DIST_THRESHOLD = 250
        self.DUPLICATE_FRAME_LIMIT = 60
        self.MATCH_DIST_THRESHOLD = 200
        self.calibration = None
        if calibration_path and os.path.exists(calibration_path):
            try:
                with open(calibration_path, 'r') as f:
                    self.calibration = json.load(f)
                print(f"[INIT] Loaded calibration: {self.calibration}")
            except Exception as e:
                print(f"[ERROR] Failed to load calibration file: {e}")
        else:
            if calibration_path:
                print(f"[WARNING] Calibration file not found: {calibration_path}")

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.crops_dir, exist_ok=True)

        print(f"[INIT] Loading Thermal Panel model: {panel_model_path}")
        self.panel_model = YOLO(panel_model_path)

        print(f"[INIT] Loading RGB Panel model: {panel_model_rgb_path}")
        self.panel_model_rgb = YOLO(panel_model_rgb_path)

        print(f"[INIT] Loading Defect model: {defect_model_path}")
        self.defect_model = YOLO(defect_model_path)

    def _is_duplicate(self, current_center, current_frame_idx):
        """
        Checks if a detected defect is a duplicate of a recent detection.

        Args:
            current_center (tuple): The (x, y) coordinates of the center of the current defect.
            current_frame_idx (int): The index of the current frame.

        Returns:
            bool: True if the defect is a duplicate, False otherwise.
        """
        cx, cy = current_center
        self.recent_defects = [d for d in self.recent_defects
                               if current_frame_idx - d['frame_idx'] < self.DUPLICATE_FRAME_LIMIT]

        for defect in self.recent_defects:
            dcx, dcy = defect['center']
            distance = math.sqrt((cx - dcx) ** 2 + (cy - dcy) ** 2)
            if distance < self.DUPLICATE_DIST_THRESHOLD:
                return True
        return False

    def _project_point_to_rgb(self, x, y):
        """
        Projects a point from the thermal coordinate system to the RGB coordinate system.

        Args:
            x (int): The x-coordinate in the thermal system.
            y (int): The y-coordinate in the thermal system.

        Returns:
            tuple: The (x, y) coordinates in the RGB system.
        """
        if not self.calibration:
            return x, y

        scale = self.calibration.get("scale_factor", 1.0)
        off_x = self.calibration.get("offset_x", 0)
        off_y = self.calibration.get("offset_y", 0)

        rx = int(x * scale + off_x)
        ry = int(y * scale + off_y)

        return rx, ry

    def _find_matching_rgb_panel(self, target_center_rgb, rgb_boxes):
        """
        Finds the RGB panel that is closest to a target point.

        Args:
            target_center_rgb (tuple): The (x, y) coordinates of the target point in the RGB system.
            rgb_boxes (list): A list of dictionaries, where each dictionary represents an RGB panel.

        Returns:
            dict: The dictionary of the best matching RGB panel, or None if no match is found.
        """
        if not rgb_boxes:
            return None

        tx, ty = target_center_rgb
        best_match = None
        min_dist = float('inf')

        for box_data in rgb_boxes:
            rcx, rcy = box_data['center']
            dist = math.sqrt((tx - rcx) ** 2 + (ty - rcy) ** 2)

            if dist < min_dist:
                min_dist = dist
                best_match = box_data

        if min_dist < self.MATCH_DIST_THRESHOLD:
            return best_match
        else:
            return None

    def process_image(self, image_path: str):
        """
        Processes a single thermal image for defect detection.

        Args:
            image_path (str): The path to the image file.
        """
        if not os.path.exists(image_path):
            print(f"[ERROR] Image file does not exist: {image_path}")
            return

        image = cv2.imread(image_path)
        if image is None: return

        print(f"[IMAGE] Processing: {image_path}")
        height, width = image.shape[:2]
        image_out = image.copy()

        results = self.panel_model(image, conf=self.conf_threshold, verbose=False)[0]
        panels_with_defects = 0
        filename = os.path.splitext(os.path.basename(image_path))[0]

        if results.boxes is not None:
            for i, box in enumerate(results.boxes):
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(width, x2), min(height, y2)

                panel_crop = image[y1:y2, x1:x2]
                if panel_crop.size == 0: continue

                defect_results = self.defect_model(panel_crop, conf=0.65, verbose=False)[0]

                if len(defect_results.boxes) > 0:
                    panels_with_defects += 1
                    cv2.rectangle(image_out, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(image_out, "Defect", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                    for d_box in defect_results.boxes:
                        dx1, dy1, dx2, dy2 = map(int, d_box.xyxy[0])
                        gx1, gy1 = x1 + dx1, y1 + dy1
                        gx2, gy2 = x1 + dx2, y1 + dy2
                        cv2.rectangle(image_out, (gx1, gy1), (gx2, gy2), (0, 0, 255), 2)

                    save_name = f"{filename}_panel_{i}_defect_thermal.jpg"
                    cv2.imwrite(os.path.join(self.crops_dir, save_name), panel_crop)

        output_image_path = os.path.join(self.output_dir, f"{filename}_processed.jpg")
        cv2.imwrite(output_image_path, image_out)
        print(f"[IMAGE] Finished. Panels with defects: {panels_with_defects}")

    def process_video(self, video_path: str, rgb_video_path: str = None, override_fps: float = None):
        """
        Processes a thermal video for defect detection, with optional RGB video for matching.

        Args:
            video_path (str): The path to the thermal video file.
            rgb_video_path (str, optional): The path to the RGB video file. Defaults to None.
            override_fps (float, optional): The frames per second to use for the output video. Defaults to None.
        """
        if not os.path.exists(video_path):
            print(f"[ERROR] Thermal video file does not exist: {video_path}")
            return

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("[ERROR] Cannot open thermal video stream.")
            return

        cap_rgb = None
        if rgb_video_path:
            if os.path.exists(rgb_video_path):
                cap_rgb = cv2.VideoCapture(rgb_video_path)
                if not cap_rgb.isOpened():
                    print(f"[WARNING] Cannot open RGB video: {rgb_video_path}. RGB logic disabled.")
                    cap_rgb = None
                else:
                    print(f"[INFO] RGB Video loaded: {rgb_video_path}")
            else:
                print(f"[WARNING] RGB video path does not exist.")

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        file_fps = cap.get(cv2.CAP_PROP_FPS)

        fps = override_fps if override_fps is not None else (file_fps if file_fps > 0 else 30)
        if override_fps: print(f"[INFO] Overwriting FPS to: {fps}")

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_video_path = os.path.join(self.output_dir, f"{video_name}_processed.mp4")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

        print(f"[VIDEO] Processing: {video_path}")
        self.recent_defects.clear()

        frame_idx = 0
        total_saved_crops = 0

        while True:
            ret, frame = cap.read()
            if not ret: break

            frame_rgb = None
            rgb_panels_data = []

            if cap_rgb:
                ret_rgb, frame_rgb_temp = cap_rgb.read()
                if ret_rgb:
                    frame_rgb = frame_rgb_temp
                    rgb_h, rgb_w = frame_rgb.shape[:2]
                    rgb_results = self.panel_model_rgb(frame_rgb, conf=self.conf_threshold, verbose=False)[0]

                    if rgb_results.boxes is not None:
                        for rbox in rgb_results.boxes:
                            rx1, ry1, rx2, ry2 = map(int, rbox.xyxy[0])
                            rx1, ry1 = max(0, rx1), max(0, ry1)
                            rx2, ry2 = min(rgb_w, rx2), min(rgb_h, ry2)

                            if rx2 <= rx1 or ry2 <= ry1: continue

                            rcx = (rx1 + rx2) // 2
                            rcy = (ry1 + ry2) // 2
                            rgb_panels_data.append({
                                'center': (rcx, rcy),
                                'xyxy': (rx1, ry1, rx2, ry2),
                                'crop': frame_rgb[ry1:ry2, rx1:rx2]
                            })

            height, width = frame.shape[:2]
            frame_out = frame.copy()
            results = self.panel_model.track(frame, persist=True, tracker="bytetrack.yaml", conf=self.conf_threshold,
                                             verbose=False)[0]

            if results.boxes is not None:
                for box in results.boxes:
                    if box.id is None: continue
                    track_id = int(box.id.item())

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(width, x2), min(height, y2)

                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2

                    panel_crop = frame[y1:y2, x1:x2]
                    if panel_crop.size == 0: continue
                    
                    defect_results = self.defect_model(panel_crop, conf=0.5, verbose=False)[0]

                    if len(defect_results.boxes) > 0:
                        label = f"ID: {track_id} (DEFECT)"
                        cv2.putText(frame_out, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        cv2.rectangle(frame_out, (x1, y1), (x2, y2), (255, 0, 0), 2)

                        for d_box in defect_results.boxes:
                            dx1, dy1, dx2, dy2 = map(int, d_box.xyxy[0])
                            gx1, gy1 = x1 + dx1, y1 + dy1
                            gx2, gy2 = x1 + dx2, y1 + dy2
                            cv2.rectangle(frame_out, (gx1, gy1), (gx2, gy2), (0, 0, 255), 2)

                        id_already_seen = any(d['id'] == track_id for d in self.recent_defects)

                        if not id_already_seen:
                            is_spatial_duplicate = self._is_duplicate((center_x, center_y), frame_idx)

                            if not is_spatial_duplicate:
                                total_saved_crops += 1
                                save_name_th = f"frame_{frame_idx:04d}_ID_{track_id}_thermal.jpg"
                                cv2.imwrite(os.path.join(self.crops_dir, save_name_th), panel_crop)

                                if frame_rgb is not None and len(rgb_panels_data) > 0:
                                    target_rgb_x, target_rgb_y = self._project_point_to_rgb(center_x, center_y)
                                    matched_rgb_panel = self._find_matching_rgb_panel((target_rgb_x, target_rgb_y),
                                                                                      rgb_panels_data)

                                    if matched_rgb_panel:
                                        save_name_rgb = f"frame_{frame_idx:04d}_ID_{track_id}_rgb.jpg"
                                        cv2.imwrite(os.path.join(self.crops_dir, save_name_rgb),
                                                    matched_rgb_panel['crop'])
                                        print(f"   >>> Matched RGB panel found for ID: {track_id}")
                                    else:
                                        print(f"   >>> No matching RGB panel found within threshold for ID: {track_id}")

                                self.recent_defects.append({
                                    'id': track_id, 'center': (center_x, center_y), 'frame_idx': frame_idx
                                })
                                print(f"   >>> New unique defect logged! ID: {track_id}")

                        for d in self.recent_defects:
                            if d['id'] == track_id:
                                d['frame_idx'] = frame_idx
                                d['center'] = (center_x, center_y)

            out.write(frame_out)

            frame_idx += 1
            if frame_idx % 20 == 0: print(f" -> Processed {frame_idx} frames...")

        cap.release()
        if cap_rgb: cap_rgb.release()
        out.release()
        print(f"[VIDEO] Finished. Saved {total_saved_crops} unique defects.")
