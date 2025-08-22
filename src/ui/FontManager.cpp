#include "FontManager.h"
#include "imgui.h"
#include <iostream>

namespace {
    ImFont* s_LargeFont = nullptr;
}

void FontManager::LoadFonts() {
    ImGuiIO& io = ImGui::GetIO();
    io.Fonts->AddFontDefault();

    const char* font_path = "resources/Roboto-Black.ttf";
    const float font_size = 26.0f;

    s_LargeFont = io.Fonts->AddFontFromFileTTF(font_path, font_size);

    if (s_LargeFont == nullptr) {
        std::cerr << "Failed to load font" << std::endl;
    }else {
        std::cout << font_path << std::endl;
    }
}

ImFont* FontManager::GetLargeFont() {
    return s_LargeFont;
}