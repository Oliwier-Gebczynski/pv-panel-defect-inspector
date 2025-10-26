import cv2
import numpy as np
from scipy.signal import correlate
import os
from img_utils import ImageUtils
from thermal_rgb_aligner import ThermalRGBAligner

class VideoSynchronizer:
    def __init__(self):
        self.cap_rgb = cv2.VideoCapture("../../data/processed/rgb_video.mp4")
        self.cap_thermal = cv2.VideoCapture("../../data/processed/thermal_video.mp4")
        self.fps = 5

    def read_frame(self):
        ret1, frame_rgb = self.cap_rgb.read()
        ret2, frame_thermal = self.cap_thermal.read()

        if (ret1 == True)&(ret2 == True):
            return frame_rgb, frame_thermal 

    def resize_thermal_frame(self, frame_thermal, frame_rgb):
        return cv2.resize(frame_thermal, (frame_rgb.shape[1], frame_rgb.shape[0]))

    def combine_two_img(self, img1, img2): # needs to be same img size 
        return np.hstack((img1, img2))

    # def detect_edges(self, img_type, resized):
    #     rgb, thermal = self.read_frame()
    #
    #     if resized == True:
    #         thermal = self.resize_thermal_frame(thermal, rgb)
    #
    #     if img_type == "rgb":
    #         gray = self.to_gray_scale(rgb)
    #         return cv2.Canny(gray, 500, 700)
    #
    #     elif img_type == "thermal": # Sprobowac Sobela
    #         gray = self.to_gray_scale(thermal)
    #         gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    #         gray = np.uint8(gray)
    #
    #         clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8,8))
    #         eq = clahe.apply(gray)
    #
    #         denoised = cv2.bilateralFilter(eq, 1, 100, 100)
    #
    #         _, mask = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    #
    #         kernel = np.ones((5,5), np.uint8)
    #         clean = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    #         clean = cv2.morphologyEx(clean, cv2.MORPH_OPEN, kernel)
    #
    #         return cv2.Canny(clean, 500, 700)

    # def match_rgb_thermal_features(self, rgb, thermal): # needs to be same img size
    #     orb = cv2.ORB_create()
    #     clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    #
    #     rgb_eq = clahe.apply(self.to_gray_scale(rgb))
    #     thermal_eq = clahe.apply(self.to_gray_scale(thermal))
    #
    #     kp1, des1 = orb.detectAndCompute(rgb_eq, None)
    #     kp2, des2 = orb.detectAndCompute(thermal_eq, None)
    #
    #     img_rgb_kp = cv2.drawKeypoints(rgb, kp1, None, color=(0, 255, 0))
    #     img_thermal_kp = cv2.drawKeypoints(thermal, kp2, None, color=(0, 255, 0))
    #
    #     combined = self.combine_two_img(img_rgb_kp, img_thermal_kp)
    #
    #     self.show_img(combined)
    #     # bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    #
    #     # matches = bf.match(des1, des2)
    #     # matches = sorted(matches, key=lambda x: x.distance)
    #
    #     # img_matches = cv2.drawMatches(rgb, kp1, thermal, kp2, matches[:20], None, flags=2)
        # return img_matches

if __name__ == "__main__":
    vs = VideoSynchronizer()
    tra = ThermalRGBAligner()

    rgb, thermal = vs.read_frame()

    tra.calibrate_with_template(thermal, rgb)
    aligned = tra.align_and_overlay(rgb, thermal)
    ImageUtils.show_img(aligned)


