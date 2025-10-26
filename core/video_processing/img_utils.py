import cv2
import numpy as np

class ImageUtils:

    @staticmethod
    def to_gray_scale(img):
        if len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img

    @staticmethod
    def gaussian_blur(img):
        return cv2.GaussianBlur(img, (5,5), 1.0)

    @staticmethod
    def canny(img, min_val=50, max_val=150):
        return cv2.Canny(img, min_val, max_val)

    @staticmethod
    def show_img(img):
        cv2.imshow("IMG", img)
        #cv2.waitKey(5000)
        cv2.waitKey(200000)        # 200s
        cv2.destroyAllWindows()