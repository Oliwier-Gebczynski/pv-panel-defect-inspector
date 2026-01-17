import subprocess
import json
import cv2
import os
import sys

class FPSReducer:
    """A class to reduce the FPS of a video to a target FPS.
    
    This class selects the best frames from a video based on their timestamp and
    frame type (I, P, B) to create a new video with a lower FPS.
    """

    TARGET_FPS = 5.0
    TIME_INTERVAL = 1.0 / TARGET_FPS
    PRIORITY_ORDER = {'I': 3, 'P': 2, 'B': 1}

    def __init__(self, input_path: str, json_path: str, grayscale: bool = False):
        """Initializes the FPSReducer.

        Args:
            input_path: The path to the input video file.
            json_path: The path to the JSON file containing frame metadata.
            grayscale: Whether to convert the output video to grayscale.
        """

        self.input_path = input_path
        self.grayscale = grayscale
        self.processed_frames = []
        self.duration = 0.0

        self._read_metadata(json_path)

    def _read_metadata(self, json_path: str):
        """Reads frame metadata from a JSON file.

        Args:
            json_path: The path to the JSON file.

        Returns:
            True if the metadata was read successfully, False otherwise.
        """

        if not os.path.exists(json_path):
            print(f"File not found: {json_path}")

        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            self.processed_frames = data
            self.duration = float(data[-1]['time'])

            print(data)
            return True

        except (IOError, json.JSONDecodeError, ValueError) as error:
            print(f"Error loading or parsing JSON: {error}")
            return False

    def _select_best_frames(self):
        """Selects the best frames from the video to match the target FPS.

        This method selects frames based on their proximity to the target
        timestamp and their frame type (I-frames are preferred).

        Returns:
            A list of selected frame IDs.
        """

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

        return selected_frame_id

    def _write_video(self, output_path: str, selected_frame_id: list):
        """Writes the selected frames to a new video file.

        Args:
            output_path: The path to the output video file.
            selected_frame_id: A list of frame IDs to include in the new video.

        Returns:
            True if the video was written successfully, False otherwise.
        """

        cap = cv2.VideoCapture(self.input_path)

        if not cap.isOpened():
            print(f"Error: Could not open video: {self.input_path}")
            return False

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        print(output_path)

        is_color = not self.grayscale
        out = cv2.VideoWriter(output_path, fourcc, self.TARGET_FPS, (frame_width, frame_height), isColor=is_color)

        if not out.isOpened():
            print(f"Error: Could not create VideoWriter")
            cap.release()
            return False

        for frame_id in selected_frame_id:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id - 1)

            ret, frame = cap.read()

            if ret:
                if self.grayscale:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                out.write(frame)
            else:
                print(f"Warning: Failed to read frame ID {frame_id}. Skipping.")

        cap.release()
        out.release()
        return True

    def  generate_5fps_video(self, output_path: str):
        """Generates a new video with a target FPS of 5.

        Args:
            output_path: The path to the output video file.

        Returns:
            True if the video was generated successfully, False otherwise.
        """
        
        selected_id = self._select_best_frames()

        if not selected_id:
            print(f"No frames were selected. Aborting video genereation")
            return False

        return self._write_video(output_path, selected_id)