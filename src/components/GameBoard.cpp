#include "GameBoard.hpp"
#include <ftxui/dom/elements.hpp>
#include <vector>

using namespace ftxui;

Component MakeGameBoard(AppState& state) {
    auto backButton = Button("Back", [&state] { state.tab_index = 0; });

    return Renderer(backButton, [=] {
        // Create a 3x5 grid (3 rows, 5 columns)
        // Similar to the actual Queen's Blood board layout
        std::vector<Elements> rows;
        for(int r = 0; r < 3; ++r) {
             std::vector<Element> cols;
             for(int c = 0; c < 5; ++c) {
                 cols.push_back(
                     vbox({
                         text(" ") | size(HEIGHT, EQUAL, 2), 
                         text("Empty") | center, 
                         text(" ") | size(HEIGHT, EQUAL, 2)
                     }) 
                     | size(WIDTH, EQUAL, 10) 
                     | size(HEIGHT, EQUAL, 6) 
                     | border
                 );
             }
             rows.push_back(cols);
        }

        auto board = gridbox(rows) | borderDouble | center;

        return vbox({
            text("Queen's Blood Arena") | bold | center | border,
            filler(),
            board | flex,
            filler(),
            backButton->Render() | align_right | size(HEIGHT, EQUAL, 3)
        }) | flex;
    });
}
