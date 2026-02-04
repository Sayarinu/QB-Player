#include "TrainMenu.hpp"
#include <ftxui/dom/elements.hpp>

using namespace ftxui;

Component MakeTrainMenu(AppState &state)
{
  // [FTXUI] Checkbox: Wraps a boolean.
  // [SYNTAX] '&state.enable_gpu': We pass the *address* of the boolean.
  // The Checkbox component stores this pointer and updates the value directly when toggled.
  // If we passed just 'state.enable_gpu', it would be a copy, and the checkbox wouldn't update our global state.
  auto check_gpu = Checkbox("Enable GPU Acceleration", &state.enable_gpu);
  auto check_logging = Checkbox("Enable Detailed Logging", &state.enable_logging);
  auto check_autosave = Checkbox("Auto-Save Checkpoints", &state.auto_save);

  // [SYNTAX] Lambda Capture: [&state] means we can access 'state' safely inside the function.
  auto backButton = Button("Back", [&state]
                          { state.tab_index = 0; });

  // [SYNTAX] Empty Capture: [] means this lambda doesn't need access to any local variables.
  auto startTrainButton = Button("Start Training", [] { /* Start Training Logic */ });

  auto component = Container::Vertical({
      check_gpu,
      check_logging,
      check_autosave,
      Container::Horizontal({backButton, startTrainButton}),
  });

  return Renderer(component, [=]
                  { return vbox({
                        text("Training Configuration") | bold | center | border,
                        vbox({// .Render() draws the checkbox in its current state (checked/unchecked)
                              check_gpu->Render(),
                              check_logging->Render(),
                              check_autosave->Render(),
                              filler(),
                              hbox({
                                  backButton->Render() | flex,
                                  startTrainButton->Render() | flex,
                              }) | size(HEIGHT, EQUAL, 3)}) |
                            border | flex,
                    }); });
}
