#pragma once

#ifndef PV_PANEL_DEFECT_INSPECTOR_VIDEOPROCESSOR_H
#define PV_PANEL_DEFECT_INSPECTOR_VIDEOPROCESSOR_H

#include <opencv2/opencv.hpp>
#include <string>

class VideoProcessor {
public:
    VideoProcessor();
    ~VideoProcessor();

    bool openVideoFromConfig(const std::string& configPath);
    void closeVideo();
    bool isVideoOpened() const;
    bool readNextFrame();
    cv::Mat& getFrame();

private:
    bool parseConfig(const std::string& configPath);

    cv::VideoCapture cap;
    cv::Mat frame;
    std::string videoPath;
};

#endif //PV_PANEL_DEFECT_INSPECTOR_VIDEOPROCESSOR_H
