import argparse
import cv2
import os
from core.video_processing.thermal_rgb_aligner import ThermalRGBAligner

def load_source(path):
    """Loads an image or the first frame of a video from the given path.

    Args:
        path (str): The path to the image or video file.

    Returns:
        numpy.ndarray: The loaded image or the first frame of the video, or None if loading fails.
    """
    
    if not os.path.exists(path):
        print(f"Error: Path does not exist: {path}")
        return None
    
    cap = cv2.VideoCapture(path)
    
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            print(f"-> Video detected: extracted first frame from {path}")
            return frame

    image = cv2.imread(path)
    if image is not None:
        print(f"-> Static image detected: loaded {path}")
    
    return image

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the interactive calibration process.")
    parser.add_argument("--thermal-input", type=str, required=True, help="Path to the thermal image/video for calibration.")
    parser.add_argument("--rgb-input", type=str, required=True, help="Path to the RGB image/video for calibration.")
    parser.add_argument("--calibration-file", type=str, default="data/metadata/calibration.json", help="Path to save the calibration file.")
    args = parser.parse_args()

    aligner = ThermalRGBAligner()

    print("Processing thermal input...")
    thermal_image = load_source(args.thermal_input)
    
    print("Processing RGB input...")
    rgb_image = load_source(args.rgb_input)

    if thermal_image is None or rgb_image is None:
        print("Error: Could not read one of the calibration inputs (check paths or file formats).")
    else:
        aligner.calibrate_with_template(thermal_image, rgb_image)
        cv2.imshow("Overlay" ,aligner.align_and_overlay(rgb_image, thermal_image))
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        aligner.save_calibration_to_json(args.calibration_file)
        