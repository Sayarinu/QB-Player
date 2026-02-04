#include "TrainMenu.hpp"
#include <ftxui/dom/elements.hpp>

using namespace ftxui;

Component MakeTrainMenu(AppState& state) {
    auto check_gpu = Checkbox("Enable GPU Acceleration", &state.enable_gpu);
    auto check_logging = Checkbox("Enable Detailed Logging", &state.enable_logging);
    auto check_autosave = Checkbox("Auto-Save Checkpoints", &state.auto_save);
    auto backButton = Button("Back", [&state] { state.tab_index = 0; });
    auto startTrainButton = Button("Start Training", [] { /* Start Training Logic */ });

    auto component = Container::Vertical({
        check_gpu,
        check_logging,
        check_autosave,
        Container::Horizontal({ backButton, startTrainButton }),
    });

    return Renderer(component, [=] {
        return vbox({
            text("Training Configuration") | bold | center | border,
            vbox({
               check_gpu->Render(),
               check_logging->Render(),
               check_autosave->Render(),
               filler(),
               hbox({
                   backButton->Render() | flex,
                   startTrainButton->Render() | flex,
               }) | size(HEIGHT, EQUAL, 3)
            }) | border | flex,
        });
    });
}
