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
    unsigned int vertexShader;
    unsigned int fragmentShader;
    unsigned int shaderProgram;
    DrawTriangle();

    void createBuffer();
    void createShader();
    void linkVertexAttrib();
    void errorHandler();
    void vertexArrayObject();

private:
    std::vector<float> vertices;
    const char *vertexShaderSource = "#version 330 core\n"
        "layout (location = 0) in vec3 aPos;\n"
        "void main()\n"
        "{\n"
        " gl_Position = vec4(aPos.x, aPos.y, aPos.z, 1.0);\n"
        "}\0";

    const char *fragmentShaderSource = "#version 330 core\n"
                                       "out vec4 FragColor\n"
                                       "void main()\n"
                                       "{\n"
                                       "FragColor = vec4(1.0f, 0.5f, 0.2f, 1.0f);\n"
                                       "}\0";

};


#endif //PV_PANEL_DEFECT_INSPECTOR_DRAWTRIANGLE_H