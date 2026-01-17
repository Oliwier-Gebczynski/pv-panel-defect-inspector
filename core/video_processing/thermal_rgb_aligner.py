import cv2
import numpy as np
import json

class ThermalRGBAligner:
    """A class to align thermal and RGB images.

    This class provides methods to calibrate the alignment between thermal and
    RGB images using template matching, and then to overlay the aligned
    thermal image on the RGB image.
    """

    def __init__(self):
        """Initializes the ThermalRGBAligner."""
        self.is_calibrated = False
        self.scale_factor = None
        self.offset_x = None
        self.offset_y = None

    def calibrate_with_template(self, thermal, rgb):
        """Calibrates the alignment using template matching.

        This method allows the user to select a region of interest (ROI) on both
        the RGB and thermal images. It then calculates the scale factor and
        offsets required to align the thermal image with the RGB image.

        Args:
            thermal: The thermal image.
            rgb: The RGB image.

        Returns:
            A tuple containing the scale factor, x-offset, and y-offset.
        """

        print("=== CALIBRATION WITH TEMPLATE MATCHING ===")

        print("Select the panel on the RGB image (press ENTER after selection)")
        rgb_roi = cv2.selectROI("Select panel on RGB", rgb, False)
        cv2.destroyWindow("Select panel on RGB")

        x, y, w, h = rgb_roi
        rgb_template = rgb[y:y + h, x:x + w]

        print("Select THE SAME panel on the thermal image")
        thermal_roi = cv2.selectROI("Select panel on THERMAL", thermal, False)
        cv2.destroyWindow("Select panel on THERMAL")

        tx, ty, tw, th = thermal_roi

        self.scale_factor = w / tw

        rgb_center_x = x + w / 2
        rgb_center_y = y + h / 2
        thermal_center_x = tx + tw / 2
        thermal_center_y = ty + th / 2

        scaled_thermal_center_x = thermal_center_x * self.scale_factor
        scaled_thermal_center_y = thermal_center_y * self.scale_factor

        self.offset_x = int(rgb_center_x - scaled_thermal_center_x)
        self.offset_y = int(rgb_center_y - scaled_thermal_center_y)

        self.is_calibrated = True

        print(f"Calibration finished:")
        print(f"  Scale factor: {self.scale_factor:.3f}")
        print(f"  Offset: ({self.offset_x}, {self.offset_y})")

        return self.scale_factor, self.offset_x, self.offset_y

    def scale_thermal(self, thermal):
        """Scales the thermal image.

        Args:
            thermal: The thermal image.

        Returns:
            The scaled thermal image.
        """

        h, w = thermal.shape[:2]
        new_w = int(w * self.scale_factor)
        new_h = int(h * self.scale_factor)
        scaled = cv2.resize(thermal, (new_w, new_h))
        return scaled

    def align_and_overlay(self, rgb, thermal, alpha=0.4):
        """Aligns and overlays the thermal image on the RGB image.

        Args:
            rgb: The RGB image.
            thermal: The thermal image.
            alpha: The transparency of the overlay.

        Returns:
            The RGB image with the thermal image overlaid.
        """

        h, w = thermal.shape[:2]

        if len(thermal.shape) == 3:
            thermal_gray = cv2.cvtColor(thermal, cv2.COLOR_BGR2GRAY)
        else:
            thermal_gray = thermal

        thermal_colored = cv2.applyColorMap(thermal_gray, cv2.COLORMAP_JET)

        new_w = int(w * self.scale_factor)
        new_h = int(h * self.scale_factor)
        scaled_thermal = cv2.resize(thermal_colored, (new_w, new_h))

        M = np.float32([[1, 0, self.offset_x], [0, 1, self.offset_y]])
        aligned = cv2.warpAffine(scaled_thermal, M, (rgb.shape[1], rgb.shape[0]))

        overlay = cv2.addWeighted(rgb, 1 - alpha, aligned, alpha, 0)
        return overlay

    def load_calibration_from_json(self, path="calibration.json"):
        """Loads calibration data from a JSON file.

        Args:
            path: The path to the JSON file.

        Returns:
            True if the calibration was loaded successfully, False otherwise.
        """

        try:
            with open(path, "r") as f:
                data = json.load(f)

            self.scale_factor = data["scale_factor"]
            self.offset_x = data["offset_x"]
            self.offset_y = data["offset_y"]
            self.is_calibrated = True

            print(f"Calibration loaded from file: {path}")
            return True
        except FileNotFoundError:
            print(f"Calibration file '{path}' not found.")
            return False
        except Exception as e:
            print(f"Error reading calibration file: {e}")
            return False

    def save_calibration_to_json(self, path="calibration.json"):
        """Saves calibration data to a JSON file.

        Args:
            path: The path to the JSON file.
        """
        
        if not self.is_calibrated:
            raise RuntimeError("Cannot save calibration - it has not been performed!")

        data = {
            "scale_factor": float(self.scale_factor),
            "offset_x": int(self.offset_x),
            "offset_y": int(self.offset_y)
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Calibration saved to file: {path}")
