#include "ResultView.h"
#include "imgui.h"

void ResultView::DrawResultView() {
    ImGui::SetNextWindowSize(ImVec2(630, 700));
    ImGui::SetNextWindowPos(ImVec2(325, 10));

    ImGui::Begin("Result View");
    ImGui::Text("Result View");
    ImGui::End();
}
