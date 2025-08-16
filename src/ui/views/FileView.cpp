#include "FileView.h"
#include "imgui.h"

void FileView::DrawFileView() {
    ImGui::SetNextWindowSize(ImVec2(305, 700));
    ImGui::SetNextWindowPos(ImVec2(10, 10));

    ImGui::Begin("File View");
    ImGui::Text("File View");
    ImGui::End();
}
