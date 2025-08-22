#include "FileView.h"
#include "imgui.h"
#include "../FontManager.h"

void FileView::DrawFileView() {
    ImGui::SetNextWindowSize(ImVec2(305, 700));
    ImGui::SetNextWindowPos(ImVec2(10, 10));

    ImGui::Begin("File View");

    ImFont* large_font = FontManager::GetLargeFont();

    if (large_font) {
        ImGui::PushFont(large_font);
    }

    const char* title = "CHOOSE FILES";
    ImVec2 text_size = ImGui::CalcTextSize(title);
    ImVec2 window_size = ImGui::GetWindowSize();

    float pos_x = (window_size.x - text_size.x) / 2;

    ImGui::SetCursorPosX(pos_x);
    ImGui::TextUnformatted(title);

    if (large_font) {
        ImGui::PopFont();
    }

    ImGui::End();
}
