#pragma once

#ifndef PV_PANEL_DEFECT_INSPECTOR_FONTMANAGER_H
#define PV_PANEL_DEFECT_INSPECTOR_FONTMANAGER_H

#include "imgui.h"

class FontManager {
public:
    static void LoadFonts();
    static ImFont* GetLargeFont();
};

#endif //PV_PANEL_DEFECT_INSPECTOR_FONTMANAGER_H