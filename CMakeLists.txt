cmake_minimum_required(VERSION 3.30)
project(pv_panel_defect_inspector)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(OpenCV_ROOT "${VCPKG_INSTALLED_DIR}/x64-linux/share/opencv4")

find_package(glad CONFIG REQUIRED)
find_package(imgui CONFIG REQUIRED)
find_package(glfw3 CONFIG REQUIRED)
find_package(Threads REQUIRED)
find_package(OpenCV REQUIRED)
find_package(nlohmann_json REQUIRED)

add_executable(${PROJECT_NAME} 
    src/core/main.cpp
        src/ui/views/VideoView.cpp
        src/ui/views/VideoView.h
        src/ui/views/ResultView.cpp
        src/ui/views/ResultView.h
        src/ui/FontManager.cpp
        src/ui/FontManager.h
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    glfw
    glad::glad
    imgui::imgui
    Threads::Threads
        nlohmann_json::nlohmann_json
)

target_include_directories(${PROJECT_NAME} PRIVATE
    ${GTK3_INCLUDE_DIRS}
)

target_compile_options(${PROJECT_NAME} PRIVATE
    ${GTK3_CFLAGS_OTHER}
)

file(GLOB_RECURSE RESOURCE_FILES "${CMAKE_SOURCE_DIR}/resources/*")

file(COPY ${RESOURCE_FILES} DESTINATION "${CMAKE_BINARY_DIR}/resources")