import subprocess
import json
import cv2
import os
import sys

from torchgen.api.cpp import return_names


class FPSReducer:
    TARGET_FPS = 5.0
    TIME_INTERVAL = 1.0 / TARGET_FPS
    PRIORITY_ORDER = {'I': 3, 'P': 2, 'B': 1}

    def __init__(self, input_path: str, json_path: str):
        self.input_path = input_path
        self.processed_frames = []
        self.duration = 0.0

        self._read_metadata(json_path)

    def _read_metadata(self, json_path: str):
        if not os.path.exists(json_path):
            print(f"File not found: {json_path}")

        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            self.processed_frames = data
            self.duration = float(data[-1]['time'])

            #print(f"Data laded. Frame counter: {data[-1]['id']}")
            print(data)
            return True

        except (IOError, json.JSONDecodeError, ValueError) as error:
            print(f"Error loading or parsing JSON: {error}")
            return False

    def _select_best_frames(self):
        if not self.processed_frames or self.duration == 0.0:
            return []

        selected_frame_id = []
        current_target_time = 0.0

        while current_target_time < self.duration:
            best_frame = None
            min_time_diff = float('inf')
            best_priority = -1

            for frame in self.processed_frames:
                frame_time = frame.get('time')
                frame_type = frame.get('type')

                if frame_time is None: continue

                time_diff = abs(frame_time - current_target_time)
                priority = self.PRIORITY_ORDER.get(frame_type, 0)

                if time_diff <= self.TIME_INTERVAL / 2.0:

                    if time_diff < min_time_diff - 0.001:
                        min_time_diff = time_diff
                        best_frame = frame
                        best_priority = priority
                    elif abs(time_diff - min_time_diff) <= 0.001 and priority > best_priority:
                        min_time_diff = time_diff
                        best_frame = frame
                        best_priority = priority

            if best_frame and best_frame['id'] not in selected_frame_id:
                selected_frame_id.append(best_frame['id'])

            current_target_time += self.TIME_INTERVAL

        #print(f"Selected frames: {selected_frame_id}")
        return selected_frame_id

    def _write_video(self, output_path: str, selected_frame_id: list):
        cap = cv2.VideoCapture(self.input_path)

        if not cap.isOpened():
            print(f"Error: Could not open video: {self.input_path}")
            return False

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        print(output_path)
        out = cv2.VideoWriter(output_path, fourcc, self.TARGET_FPS, (frame_width, frame_height))

        if not out.isOpened():
            print(f"Error: Could not create VideoWriter")
            cap.release()
            return False

        for frame_id in selected_frame_id:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id - 1)

            ret, frame = cap.read()

            if ret:
                out.write(frame)
            else:
                print(f"Warning: Failed to read frame ID {frame_id}. Skipping.")

        cap.release()
        out.release()
        return True

    def  generate_5fps_video(self, output_path: str):
        selected_id = self._select_best_frames()

        if not selected_id:
            print(f"No frames were selected. Aborting video genereation")
            return False

        return self._write_video(output_path, selected_id)

if __name__ == "__main__":
    # rgb video
    # INPUT_VIDEO_PATH = "../../data/processed/rgb_video.mp4"
    # INPUT_JSON_PATH = "../../data/metadata/rgb_frames.json"
    # OUTPUT_VIDEO_PATH = "../../data/processed/5fps/5fps_rgb.mp4"

    # thermal video
    INPUT_VIDEO_PATH = "../../data/processed/rgb_video.mp4"
    INPUT_JSON_PATH = "../../data/metadata/rgb_frames.json"
    OUTPUT_VIDEO_PATH = "../../data/processed/5fps/5fps_rgb.mp4"

    reducer = FPSReducer(INPUT_VIDEO_PATH, INPUT_JSON_PATH)

    reducer.generate_5fps_video(OUTPUT_VIDEO_PATH)