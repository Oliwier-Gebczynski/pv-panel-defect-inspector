import cv2
import numpy as np

class ImageUtils:
    """A utility class for common image processing operations."""

    @staticmethod
    def to_gray_scale(img):
        """Converts an image to grayscale.

        Args:
            img: The input image.

        Returns:
            The grayscale image.
        """

        if len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img

    @staticmethod
    def gaussian_blur(img):
        """Applies Gaussian blur to an image.

        Args:
            img: The input image.

        Returns:
            The blurred image.
        """

        return cv2.GaussianBlur(img, (5,5), 1.0)

    @staticmethod
    def canny(img, min_val=50, max_val=150):
        """Applies the Canny edge detection algorithm to an image.

        Args:
            img: The input image.
            min_val: The minimum threshold for edge detection.
            max_val: The maximum threshold for edge detection.

        Returns:
            The image with detected edges.
        """

        return cv2.Canny(img, min_val, max_val)

    @staticmethod
    def show_img(img):
        """Displays an image in a window.

        Args:
            img: The image to display.
        """
        
        cv2.imshow("IMG", img)
        cv2.waitKey(200000)        # 200s
        cv2.destroyAllWindows()