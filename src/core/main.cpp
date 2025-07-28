#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl3.h>
#include <iostream>
#include <cmath>

void framebuffer_size_callback(GLFWwindow* window, int width, int height) {
    glViewport(0, 0, width, height);
}

void processInput(GLFWwindow *window) {
    if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS)
        glfwSetWindowShouldClose(window, true);
}

int main() {
    std::cout << "=== Test bibliotek OpenGL ===" << std::endl;

    if (!glfwInit()) {
        std::cerr << "❌ GLFW initialization failed!" << std::endl;
        return -1;
    }
    std::cout << "✅ GLFW initialized successfully" << std::endl;

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    GLFWwindow* window = glfwCreateWindow(1000, 700, "🚀 Test GLAD + GLFW3 + ImGui", NULL, NULL);
    if (!window) {
        std::cerr << "❌ Failed to create GLFW window" << std::endl;
        glfwTerminate();
        return -1;
    }
    std::cout << "✅ GLFW window created successfully" << std::endl;

    glfwMakeContextCurrent(window);
    glfwSetFramebufferSizeCallback(window, framebuffer_size_callback);

    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        std::cerr << "❌ Failed to initialize GLAD" << std::endl;
        glfwTerminate();
        return -1;
    }
    std::cout << "✅ GLAD initialized successfully" << std::endl;

    std::cout << "📊 OpenGL Version: " << glGetString(GL_VERSION) << std::endl;
    std::cout << "🎮 Graphics Card: " << glGetString(GL_RENDERER) << std::endl;
    std::cout << "🏢 Vendor: " << glGetString(GL_VENDOR) << std::endl;

    glViewport(0, 0, 1000, 700);

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO(); (void)io;
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;

    ImGui::StyleColorsDark();

    if (!ImGui_ImplGlfw_InitForOpenGL(window, true)) {
        std::cerr << "❌ ImGui GLFW initialization failed" << std::endl;
        return -1;
    }

    if (!ImGui_ImplOpenGL3_Init("#version 330")) {
        std::cerr << "❌ ImGui OpenGL3 initialization failed" << std::endl;
        return -1;
    }
    std::cout << "✅ ImGui initialized successfully" << std::endl;
    std::cout << "\n🎉 All libraries working! Starting main loop...\n" << std::endl;

    float time = 0.0f;
    float clearColor[3] = {0.2f, 0.3f, 0.3f};
    bool showDemo = true;
    int counter = 0;

    while (!glfwWindowShouldClose(window)) {
        processInput(window);
        glfwPollEvents();

        time += 0.016f;

        ImGui_ImplOpenGL3_NewFrame();
        ImGui_ImplGlfw_NewFrame();
        ImGui::NewFrame();

        ImGui::Begin("🔧 System Info");
        ImGui::Text("🚀 Application average %.3f ms/frame (%.1f FPS)",
                   1000.0f / ImGui::GetIO().Framerate, ImGui::GetIO().Framerate);
        ImGui::Text("⏰ Time: %.2f seconds", time);
        ImGui::Separator();
        ImGui::Text("📊 OpenGL: %s", glGetString(GL_VERSION));
        ImGui::Text("🎮 GPU: %s", glGetString(GL_RENDERER));
        ImGui::End();

        ImGui::Begin("🎨 Controls");
        ImGui::Text("Background color:");
        ImGui::ColorEdit3("Color", clearColor);

        if (ImGui::Button("Click me!")) {
            counter++;
        }
        ImGui::SameLine();
        ImGui::Text("Clicked %d times", counter);

        ImGui::Checkbox("Show ImGui Demo", &showDemo);

        ImGui::Text("🎯 Press ESC to exit");
        ImGui::End();

        ImGui::Begin("📈 Animation Test");
        float sinValue = sin(time * 2.0f);
        float cosValue = cos(time * 1.5f);

        ImGui::Text("sin(t*2): %.3f", sinValue);
        ImGui::ProgressBar((sinValue + 1.0f) * 0.5f, ImVec2(0.0f, 0.0f));

        ImGui::Text("cos(t*1.5): %.3f", cosValue);
        ImGui::ProgressBar((cosValue + 1.0f) * 0.5f, ImVec2(0.0f, 0.0f));

        ImGui::TextColored(ImVec4(sinValue * 0.5f + 0.5f, cosValue * 0.5f + 0.5f, 0.8f, 1.0f),
                          "🌈 Animated text!");
        ImGui::End();

        if (showDemo) {
            ImGui::ShowDemoWindow(&showDemo);
        }

        float animatedR = clearColor[0] + sin(time) * 0.1f;
        float animatedG = clearColor[1] + cos(time * 0.8f) * 0.1f;
        float animatedB = clearColor[2] + sin(time * 1.2f) * 0.1f;

        glClearColor(animatedR, animatedG, animatedB, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        ImGui::Render();
        ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

        glfwSwapBuffers(window);
    }

    std::cout << "\n🧹 Cleaning up..." << std::endl;

    ImGui_ImplOpenGL3_Shutdown();
    ImGui_ImplGlfw_Shutdown();
    ImGui::DestroyContext();

    glfwTerminate();

    std::cout << "👋 Goodbye!" << std::endl;
    return 0;
}