#include "GameBoard.hpp"
#include <ftxui/dom/elements.hpp>
#include <vector>

using namespace ftxui;

// [SYNTAX] Factory Function: A common pattern where a function creates and configures an object (Component).
Component MakeGameBoard(AppState &state)
{
  // [SYNTAX] '[&state]': Capture 'state' by reference.
  // This allows the button callback to modify the original 'state' variable (changing tab_index).
  auto backButton = Button("Back", [&state]
                          { state.tab_index = 0; });

  return Renderer(backButton, [=]
                  {
        // [SYNTAX] std::vector: A dynamic array that can change size.
        // We accumulate rows of elements here.
        std::vector<Element> rows;

        // [SYNTAX] for-loop: Standard C++ loop.
        for(int r = 0; r < 3; ++r) {
            std::vector<Element> cols;
            for(int c = 0; c < 5; ++c) {
                // [SYNTAX] push_back: Adds a new item to the end of the vector.
                cols.push_back(
                    vbox({
                        filler(),
                        text("Empty") | center, 
                        filler()
                    }) 
                    | size(WIDTH, GREATER_THAN, 12)  // Enforce min width
                    | size(HEIGHT, GREATER_THAN, 6)  // Enforce min height
                    | border 
                    | flex // Allow it to expand to fill available space
                );
            }
            // [FTXUI] hbox(cols): Creates a horizontal layout from a vector of elements.
            rows.push_back(hbox(cols) | flex);
        }

        // [FTXUI] vbox(rows): Creates a vertical stack from our vector of rows.
        auto board = vbox(rows) | borderDouble | center;

        return vbox({
            text("Queen's Blood Arena") | bold | center | border,
            board | flex, // Board takes all remaining space
            backButton->Render() | align_right | size(HEIGHT, EQUAL, 3)
        }) | flex; });
}
