#pragma once

#ifndef PV_PANEL_DEFECT_INSPECTOR_DRAWTRIANGLE_H
#define PV_PANEL_DEFECT_INSPECTOR_DRAWTRIANGLE_H
#include <vector>
#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <iostream>
#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"

class DrawTriangle {
public:
    unsigned int VBO;
    unsigned int VAO;
    unsigned int EBO;
    unsigned int vertexShader;
    unsigned int fragmentShader;
    unsigned int shaderProgram;
    DrawTriangle();

    void createBuffer();
    void createShaderProgram();

    void createVertexShader();
    void createFragmentShader();

    void updateColor();

    void drawTriangle();

private:
    std::vector<float> vertices;
    std::vector<unsigned int> indices;
    const char *vertexShaderSource = "#version 330 core\n"
    "layout (location = 0) in vec3 aPos;\n"
    "layout (location = 1) in vec3 aColor;\n"
    "out vec3 ourColor;\n"
    "void main()\n"
    "{\n"
    "   gl_Position = vec4(aPos, 1.0);\n"
    "   ourColor = aColor;\n"
    "}\0";

    const char *fragmentShaderSource = "#version 330 core\n"
    "out vec4 FragColor;\n"
    "in vec3 ourColor;\n"
    "void main()\n"
    "{\n"
    "   FragColor = vec4(ourColor, 1.0f);\n"
    "}\n\0";
};


#endif //PV_PANEL_DEFECT_INSPECTOR_DRAWTRIANGLE_H