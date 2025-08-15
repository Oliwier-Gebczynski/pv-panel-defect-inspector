cmake_minimum_required(VERSION 3.30)
project(pv_panel_defect_inspector)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(glad CONFIG REQUIRED)
find_package(imgui CONFIG REQUIRED)
find_package(glfw3 CONFIG REQUIRED)

find_package(Threads REQUIRED)

add_executable(${PROJECT_NAME} 
    src/core/main.cpp
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    glfw
    glad::glad
    imgui::imgui
    Threads::Threads
)

target_include_directories(${PROJECT_NAME} PRIVATE
    ${GTK3_INCLUDE_DIRS}
)

target_compile_options(${PROJECT_NAME} PRIVATE
    ${GTK3_CFLAGS_OTHER}
)