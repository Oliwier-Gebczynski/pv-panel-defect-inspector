import cv2
from core.video_processing.thermal_rgb_aligner import ThermalRGBAligner


class VideoSynchronizer:
    """A class to synchronize and overlay thermal and RGB videos.

    This class reads frames from both an RGB and a thermal video, and uses a
    ThermalRGBAligner to overlay the thermal video on top of the RGB video.
    """

    def __init__(self, rgb_path, thermal_path, fps=5):
        """Initializes the VideoSynchronizer.

        Args:
            rgb_path: The path to the RGB video file.
            thermal_path: The path to the thermal video file.
            fps: The frames per second of the output video.
        """

        self.rgb_path = rgb_path
        self.thermal_path = thermal_path
        self.fps = fps

        self.cap_rgb = cv2.VideoCapture(rgb_path)
        self.cap_thermal = cv2.VideoCapture(thermal_path)

        if not self.cap_rgb.isOpened() or not self.cap_thermal.isOpened():
            print("Error: Could not open one of the video files.")

    def read_frame(self):
        """Reads a frame from both the RGB and thermal videos.

        Returns:
            A tuple containing the RGB and thermal frames, or (None, None) if
            either frame could not be read.
        """

        ret1, frame_rgb = self.cap_rgb.read()
        ret2, frame_thermal = self.cap_thermal.read()

        if ret1 and ret2:
            return frame_rgb, frame_thermal
        else:
            return None, None

    def release(self):
        # Releases video sources
        self.cap_rgb.release()
        self.cap_thermal.release()

    def get_total_frames(self):
        # Returns the total number of frames.
        
        return int(min(self.cap_rgb.get(cv2.CAP_PROP_FRAME_COUNT),
                       self.cap_thermal.get(cv2.CAP_PROP_FRAME_COUNT)))

    def generate_overlay_video(self, tra: ThermalRGBAligner, output_path: str, alpha=0.4):
        """Generates an overlay video.

        This method reads frames from both videos, overlays the thermal video on
        the RGB video, and saves the result to a new video file.

        Args:
            tra: The ThermalRGBAligner object to use for alignment.
            output_path: The path to save the output video file.
            alpha: The transparency of the overlay.
        """

        total_frames = self.get_total_frames()
        print(f"[INFO] Processing {total_frames} frames...")

        if not tra.is_calibrated:
            print("[ERROR] ThermalRGBAligner is not calibrated. Please calibrate it first.")
            return

        self.cap_rgb.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.cap_thermal.set(cv2.CAP_PROP_POS_FRAMES, 0)
        rgb_first, thermal_first = self.read_frame()
        if rgb_first is None:
            print("Error: Could not read the first frame for setting up the writer.")
            return

        height, width = rgb_first.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (width, height))

        self.cap_rgb.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.cap_thermal.set(cv2.CAP_PROP_POS_FRAMES, 0)

        frame_idx = 0

        while True:
            rgb, thermal = self.read_frame()

            if rgb is None or thermal is None:
                break

            overlay = tra.align_and_overlay(rgb, thermal, alpha=alpha)

            out.write(overlay)

            frame_idx += 1
            if frame_idx % 20 == 0:
                print(f" -> Processed {frame_idx}/{total_frames}")

        self.release()
        out.release()
        print(f"[INFO] Finished! Video saved to: {output_path}")

    def generate_overlay_image(self, tra: ThermalRGBAligner, output_path: str, alpha=0.5):
        """Generates an overlay image from the first frame of the videos.

        Args:
            tra: The ThermalRGBAligner object to use for alignment.
            output_path: The path to save the output image file.
            alpha: The transparency of the overlay.
        """
        
        if not tra.is_calibrated:
            print("[ERROR] ThermalRGBAligner is not calibrated. Please calibrate it first.")
            return
            
        rgb, thermal = self.read_frame()
        if rgb is None or thermal is None:
            print("Error: Could not read frames from the video files.")
            return

        overlay = tra.align_and_overlay(rgb, thermal, alpha=alpha)
        cv2.imwrite(output_path, overlay)
        print(f"[INFO] Finished! Image saved to: {output_path}")
        self.release()
