#include <ftxui/component/screen_interactive.hpp>
#include "components/State.hpp"
#include "components/MainMenu.hpp"
#include "components/TrainMenu.hpp"
#include "components/GameBoard.hpp"

using namespace ftxui;

// [SYNTAX] Entry Point: 'main' is where C++ execution begins.
int main()
{
  // [SYNTAX] Stack Allocation: 'screen' is created on the stack.
  // It will be automatically destroyed (destructor called) when 'main' exits.
  auto screen = ScreenInteractive::Fullscreen();

  // [SYNTAX] Default Initialization: Creates an AppState object with default values (false, true, etc).
  AppState state;

  // Create our components, passing 'state' by reference so they all share the same data.
  auto home_component = MakeMainMenu(state, screen.ExitLoopClosure());
  auto train_component = MakeTrainMenu(state);
  auto game_component = MakeGameBoard(state);

  // [FTXUI] Container::Tab: A switcher container.
  // It shows only ONE of its children at a time, based on the index pointed to by the second argument.
  // [SYNTAX] '&state.tab_index': Address-of operator. We pass a *pointer* to the integer
  // so the Tab container can read AND write to it.
  auto tab_container = Container::Tab({
                                          home_component,
                                          train_component,
                                          game_component,
                                      },
                                      &state.tab_index);

  // Start the main event loop. This blocks until ExitLoopClosure is called.
  screen.Loop(tab_container);
  return 0;
}
