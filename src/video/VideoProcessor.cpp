#include "VideoProcessor.h"
#include <iostream>
#include <fstream>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

VideoProcessor::VideoProcessor() = default;

VideoProcessor::~VideoProcessor() {
    closeVideo();
}

bool VideoProcessor::openVideoFromConfig(const std::string& configPath) {
    if (!parseConfig(configPath)) {
        return false;
    }

    if (!cap.open(this->videoPath)) {
        std::cerr << "Error: Could not open video file: " << this->videoPath << std::endl;
        return false;
    }

    return true;
}

bool VideoProcessor::parseConfig(const std::string& configPath) {
    std::ifstream configFile(configPath);
    if (!configFile.is_open()) {
        std::cerr << "Error: Could not open config file: " << configPath << std::endl;
        return false;
    }

    try {
        json config;
        configFile >> config;
        this->videoPath = config["video_path"];
    } catch (json::parse_error& e) {
        std::cerr << "Error: Could not parse config file: " << e.what() << std::endl;
        return false;
    }

    return true;
}

void VideoProcessor::closeVideo() {
    if (cap.isOpened()) {
        cap.release();
    }
}

bool VideoProcessor::isVideoOpened() const {
    return cap.isOpened();
}

bool VideoProcessor::readNextFrame() {
    if (isVideoOpened()) {
        return cap.read(frame);
    }
    return false;
}

cv::Mat& VideoProcessor::getFrame() {
    return frame;
}