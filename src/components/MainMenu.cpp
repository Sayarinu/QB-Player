#include "MainMenu.hpp"
#include <ftxui/dom/elements.hpp>

using namespace ftxui;

Component MakeMainMenu(AppState& state, std::function<void()> quit) {
    auto playButton = Button("Play", [&state] { state.tab_index = 2; });
    auto trainInitButton = Button("Train", [&state] { state.tab_index = 1; });
    auto quitButton = Button("Quit", quit);

    auto component = Container::Horizontal({
        playButton,
        trainInitButton,
        quitButton,
    });

    return Renderer(component, [=] {
        auto bottom_menu = hbox({
            playButton->Render() | flex,
            trainInitButton->Render() | flex,
            quitButton->Render() | flex,
        });

        return vbox({
            text("Queen's Blood Player") | bold | center | border,
            
            vbox({
                filler(),
                text("This Application is for running a simulated environment for Queen's Blood from Final Fantasy VII Rebirth."),
                text("This features the following functionality:"),
                text("      - Train an AI Model to Play Queen's Blood"),
                text("      - Allow you to view two models Playing Queen's Blood vs each other"),
                text("      - Allow you to have a model play Queen's Blood matches for you in Final Fantasy VII Rebirth"),
                filler(),
            }) | flex | border,

            bottom_menu | size(HEIGHT, EQUAL, 3)
        }) | flex;
    });
}
