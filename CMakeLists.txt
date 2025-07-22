cmake_minimum_required(VERSION 3.30)
project(pv_panel_defect_inspector)

set(CMAKE_TOOLCHAIN_FILE "${CMAKE_CURRENT_SOURCE_DIR}/vcpkg/scripts/buildsystems/vcpkg.cmake"
        CACHE STRING "vcpkg toolchain file")

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)

find_package(glad CONFIG REQUIRED)
find_package(glfw3 CONFIG REQUIRED)
find_package(imgui CONFIG REQUIRED)

add_executable(inspector)
file(GLOB_RECURSE inspector_SOURCES CONFIGURE_DEPENDS
        "${CMAKE_CURRENT_SOURCE_DIR}/src/core/*.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/core/*.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/core/*.hpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/detection/*.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/detection/*.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/detection/*.hpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/ui/*.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/ui/*.h"
        "${CMAKE_CURRENT_SOURCE_DIR}/src/ui/*.hpp"
)

target_sources(inspector PRIVATE ${inspector_SOURCES})

target_include_directories(inspector PRIVATE 
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_compile_definitions(inspector PRIVATE
        MY_TEST_DEFINE
)

target_link_libraries(inspector PRIVATE
        glad::glad
        glfw
        imgui::imgui
)

set_property(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY VS_STARTUP_PROJECT inspector)

source_group(TREE "${CMAKE_CURRENT_SOURCE_DIR}/src" PREFIX "Source Files" FILES ${inspector_SOURCES})

set_property(GLOBAL PROPERTY USE_FOLDERS ON)
