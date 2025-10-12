import cv2
import numpy as np

class VideoSynchronizer:
    def __init__(self):
        self.cap_rgb = cv2.VideoCapture("../../data/processed/rgb_video.mp4")
        self.cap_thermal = cv2.VideoCapture("../../data/processed/thermal_video.mp4")

    def readFrame(self):
        ret1, frame_rgb = self.cap_rgb.read()
        ret2, frame_thermal = self.cap_thermal.read()

        if (ret1 == True)&(ret2 == True):
            return frame_rgb, frame_thermal 

    def resizeThermalFrame(self, frame_thermal, frame_rgb):
        return cv2.resize(frame_thermal, (frame_rgb.shape[1], frame_rgb.shape[0]))

    def showImg(self, img):
        cv2.imshow("IMG", img)
        cv2.waitKey(2000)          # 2s 
        cv2.destroyAllWindows()

    def combineTwoImg(self, img1, img2): # needs to be same img size 
        return np.hstack((img1, img2))
    
    def detectEdges(self, img_type):
        rgb, thermal = self.readFrame()

        if img_type == "rgb":
            grey = self.toGrayScale(rgb)
            return cv2.Canny(grey, 500, 700)
            
        elif img_type == "thermal":
            grey = self.toGrayScale(thermal)
            blurred = self.gaussianBlur(grey)
            return cv2.Canny(blurred, 10, 40)
    
    def toGrayScale(self, img):
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    def gaussianBlur(self, img):
        return cv2.GaussianBlur(img, (5,5), 0)

if __name__ == "__main__":
    vs = VideoSynchronizer()

    rgb, thermal = vs.readFrame()

    edge_rgb = vs.detectEdges("thermal")

    #rgb_grayscaled = vs.toGrayScale(rgb)

    #resized_thermal = vs.resizeThermalFrame(thermal, rgb)
    #combined = vs.combineTwoImg(rgb, resized_thermal)

    vs.showImg(edge_rgb)
