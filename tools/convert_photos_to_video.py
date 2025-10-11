import cv2
import glob
import numpy as np
import os

class VideoCreator:
    def __init__(self, rgb_dir=None, thermal_dir=None, out_dir="output", fps=25):
        self.rgb_dir = rgb_dir
        self.thermal_dir = thermal_dir
        self.out_dir = out_dir
        self.fps = fps

        os.makedirs(self.out_dir, exist_ok=True)

    def _sort_frames(self, path_pattern):
        files = glob.glob(path_pattern)
        files = sorted(files, key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))
        return files

    def _create_video(self, files, out_path, is_thermal=False):
        if not files:
            print(f"Brak plików wejściowych dla {out_path}")
            return

        # Ustal rozmiar klatki
        frame = cv2.imread(files[0], cv2.IMREAD_UNCHANGED)
        if is_thermal:
            # termowizja może być 16-bitowa – normalizujemy
            frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
            frame = np.uint8(frame)
            frame = cv2.applyColorMap(frame, cv2.COLORMAP_INFERNO)

        height, width = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(out_path, fourcc, self.fps, (width, height))

        for i, f in enumerate(files):
            frame = cv2.imread(f, cv2.IMREAD_UNCHANGED)
            if is_thermal:
                frame = cv2.normalize(frame, None, 0, 255, cv2.NORM_MINMAX)
                frame = np.uint8(frame)
                frame = cv2.applyColorMap(frame, cv2.COLORMAP_INFERNO)

            video.write(frame)
            print(f"[{i+1}/{len(files)}] Zapisano klatkę: {f}")

        video.release()
        print(f"Zapisano wideo: {out_path}")

    def create_rgb_video(self, output_name="rgb_video.mp4"):
        if not self.rgb_dir:
            print("Nie ustawiono ścieżki do folderu RGB.")
            return
        rgb_files = self._sort_frames(os.path.join(self.rgb_dir, "*.jpg"))
        out_path = os.path.join(self.out_dir, output_name)
        self._create_video(rgb_files, out_path, is_thermal=False)

    def create_thermal_video(self, output_name="thermal_video.mp4"):
        if not self.thermal_dir:
            print("Nie ustawiono ścieżki do folderu termowizji.")
            return
        thermal_files = self._sort_frames(os.path.join(self.thermal_dir, "*.tiff"))
        out_path = os.path.join(self.out_dir, output_name)
        self._create_video(thermal_files, out_path, is_thermal=True)

if __name__ == "__main__":
    vc = VideoCreator(
        rgb_dir="../data/raw/rgb",
        thermal_dir="../data/raw/thermal",
        out_dir="../data/processed/",
        fps=25
    )

    vc.create_rgb_video()        
    vc.create_thermal_video()  
