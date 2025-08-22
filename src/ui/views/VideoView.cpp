#include "VideoView.h"
#include "imgui.h"
#include "../FontManager.h"

void VideoView::DrawVideoView() {
    ImGui::SetNextWindowSize(ImVec2(305, 700));
    ImGui::SetNextWindowPos(ImVec2(965, 10));

    ImGui::Begin("Video View");
    ImGui::Text("Video View");
    ImGui::End();
}