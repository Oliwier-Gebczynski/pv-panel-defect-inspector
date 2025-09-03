#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <iostream>
#include "imgui.h"
#include "imgui_impl_glfw.h"
#include "imgui_impl_opengl3.h"

#include "../ui/views/VideoView.h"
#include "../ui/views/ResultView.h"
#include "../ui/FontManager.h"
#include "../sandbox/DrawTriangle.h"

void framebuffer_size_callback(GLFWwindow* window, int width, int height) {
    glViewport(0, 0, width, height);
}

//--------- SANDBOX FUNCTIONS -----------
void processInput(GLFWwindow *window) {
    if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS) {
        glfwSetWindowShouldClose(window, true);
    }
}

int main(){

    // ------------ Working: -------------
    // if (!glfwInit()) {
    //     std::cerr << "GLFW initialization failed" << std::endl;
    //     return -1;
    // }
    //
    // const char *glsl_version = "#version 330";
    // glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    // glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    // glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    //
    // GLFWwindow* window = glfwCreateWindow(1280, 720, "PV Panel Defect Inspector", nullptr, nullptr);
    // if (!window) {
    //     std::cerr << "Failed to create window" << std::endl;
    //     glfwTerminate();
    //     return -1;
    // }
    //
    // glfwMakeContextCurrent(window);
    // glfwSetFramebufferSizeCallback(window, framebuffer_size_callback);
    //
    // if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
    //     std::cerr << "Failed to initializ GLAD" << std::endl;
    //     return -1;
    // }
    //
    // IMGUI_CHECKVERSION();
    // ImGui::CreateContext();
    // ImGuiIO& io = ImGui::GetIO(); (void)io;
    // io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    //
    // FontManager::LoadFonts();
    // ImGui::StyleColorsDark();
    //
    // ImGui_ImplGlfw_InitForOpenGL(window, true);
    // ImGui_ImplOpenGL3_Init(glsl_version);
    //
    // while (!glfwWindowShouldClose(window)) {
    //     if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS) {
    //         glfwSetWindowShouldClose(window, GLFW_TRUE);
    //     }
    //
    //     ImGui_ImplOpenGL3_NewFrame();
    //     ImGui_ImplGlfw_NewFrame();
    //     ImGui::NewFrame();
    //
    //     //VideoView::DrawVideoView();
    //     //ResultView::DrawResultView();
    //     ImGui::Render();
    //
    //     glClearColor(0.2f, 0.3f, 0.3f, 1.0f);
    //     glClear(GL_COLOR_BUFFER_BIT);
    //
    //     ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
    //
    //     glfwSwapBuffers(window);
    //     glfwPollEvents();
    // }
    //
    // glfwDestroyWindow(window);
    // glfwTerminate();

    // --------- SANDBOX ----------- https://learnopengl.com/book/book_pdf.pdf

    glfwInit();
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    GLFWwindow* window = glfwCreateWindow(800, 600, "Sandbox", NULL, NULL);
    if (window == NULL) {
        std::cout << "Failed to create GLFW window" << std::endl;
        glfwTerminate();
        return -1;
    }

    glfwMakeContextCurrent(window);

    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        std::cout << "Failed to initialize GLAD" << std::endl;
        return -1;
    }

    glViewport(0,0,800,600);

    glfwSetFramebufferSizeCallback(window, framebuffer_size_callback);

    DrawTriangle triangle;

    while (!glfwWindowShouldClose(window)) {
        processInput(window);

        glClearColor(0.2f, 0.3f, 0.3f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        triangle.vertexArrayObject();

        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    glfwTerminate();
    return 0;
}
