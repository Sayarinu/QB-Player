#include "MainMenu.hpp"
#include <ftxui/dom/elements.hpp>

// 'using namespace' allows us to use symbols from the 'ftxui' namespace
// without typing 'ftxui::' every time (e.g., 'Button' instead of 'ftxui::Button').
using namespace ftxui;

Component MakeMainMenu(AppState &state, std::function<void()> quit)
{
  // [SYNTAX] 'auto': The compiler deduces the type of 'playButton' automatically (std::shared_ptr<Button>).
  // [SYNTAX] lambda: '[] {}' is an anonymous function.
  //   - '[&state]': "Capture" state by reference so we can modify it inside the function.
  auto playButton = Button("Play", [&state]
                          { state.tab_index = 2; });

  //   - '[&state]': We capture state again to switch tabs.
  auto trainInitButton = Button("Train", [&state]
                                { state.tab_index = 1; });

  //   - 'quit': We pass the 'quit' function object directly.
  auto quitButton = Button("Quit", quit);

  // [FTXUI] Container::Horizontal groups components side-by-side.
  // This handles the *logic* (handling key presses like Left/Right arrows).
  auto component = Container::Horizontal({
      playButton,
      trainInitButton,
      quitButton,
  });

  // [FTXUI] Renderer: Separates Logic (component) from Visuals (drawing).
  // The lambda here tells FTXUI *how* to draw this component every frame.
  // [SYNTAX] '[=]': Capture all local variables (like playButton) by value (copying smart pointers is cheap).
  return Renderer(component, [=]
                  {
        // [FTXUI] 'hbox': Horizontal Box layout element (Visual only, no logic).
        auto bottom_menu = hbox({
            // [FTXUI] Pipe operator '|': Used like Unix pipes to chain modifiers.
            // 'flex': Use remaining space equally.
            playButton->Render() | flex,
            trainInitButton->Render() | flex,
            quitButton->Render() | flex,
        });

        // [FTXUI] 'vbox': Vertical Box layout element.
        return vbox({
            // 'bold', 'center', 'border': Decorators applied via pipe '|'.
            text("Queen's Blood Player") | bold | center | border,
            
            // 'paragraph': Automatically wraps text on whitespace.
            paragraph("This Application is for running a simulated environment for Queen's Blood from Final Fantasy VII Rebirth.\n"
                      "This features the following functionality:\n"
                      "- Train an AI Model to Play Queen's Blood\n"
                      "- Allow you to view two models Playing Queen's Blood vs each other\n"
                      "- Allow you to have a model play Queen's Blood matches for you in Final Fantasy VII Rebirth")
            | flex | border,

            // 'size(HEIGHT, EQUAL, 3)': Forcing the menu to be exactly 3 lines tall.
            bottom_menu | size(HEIGHT, EQUAL, 3)
        }) | flex; });
}
