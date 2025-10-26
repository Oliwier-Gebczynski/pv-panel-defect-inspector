import cv2
import numpy as np
from img_utils import ImageUtils

class ThermalRGBAligner:
    def __init__(self):
        self.is_calibrated = False
        self.scale_factor = None
        self.offset_x = None
        self.offset_y = None

    def calibrate_with_template(self, thermal, rgb):
        print("=== KALIBRACJA Z TEMPLATE MATCHING ===")

        print("Wybierz panel na obrazie RGB (naciśnij ENTER po wyborze)")
        rgb_roi = cv2.selectROI("Wybierz panel na RGB", rgb, False)
        cv2.destroyWindow("Wybierz panel na RGB")

        x, y, w, h = rgb_roi
        rgb_template = rgb[y:y + h, x:x + w]

        print("Wybierz TEN SAM panel na obrazie thermal")
        thermal_roi = cv2.selectROI("Wybierz panel na THERMAL", thermal, False)
        cv2.destroyWindow("Wybierz panel na THERMAL")

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

        print(f"Kalibracja zakończona:")
        print(f"  Scale factor: {self.scale_factor:.3f}")
        print(f"  Offset: ({self.offset_x}, {self.offset_y})")

        return self.scale_factor, self.offset_x, self.offset_y

    def scale_thermal(self, thermal):
        h, w = thermal.shape[:2]

        new_w = int(w * self.scale_factor)
        new_h = int(h * self.scale_factor)

        scaled = cv2.resize(thermal, (new_w, new_h))

        return scaled

    def align_and_overlay(self, rgb, thermal, alpha=0.4):
        h, w = thermal.shape[:2]
        new_w = int(w * self.scale_factor)
        new_h = int(h * self.scale_factor)
        scaled_thermal = cv2.resize(thermal, (new_w, new_h))

        M = np.float32([[1, 0, self.offset_x], [0, 1, self.offset_y]])

        aligned = cv2.warpAffine(scaled_thermal, M, (rgb.shape[1], rgb.shape[0]))

        overlay = cv2.addWeighted(rgb, 1 - alpha, aligned, alpha, 0)

        return overlay

