#include <ftxui/component/component.hpp>
#include <ftxui/component/screen_interactive.hpp>
#include "components/State.hpp"
#include "components/MainMenu.hpp"
#include "components/TrainMenu.hpp"
#include "components/GameBoard.hpp"

using namespace ftxui;

int main() {
  auto screen = ScreenInteractive::Fullscreen();
  AppState state;

  auto home_component = MakeMainMenu(state, screen.ExitLoopClosure());
  auto train_component = MakeTrainMenu(state);
  auto game_component = MakeGameBoard(state);

  auto tab_container = Container::Tab({
      home_component,
      train_component,
      game_component,
  }, &state.tab_index);

  screen.Loop(tab_container);
  return 0;
}
