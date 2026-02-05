#include <ftxui/component/screen_interactive.hpp>
#include "ui/State.hpp"
#include "ui/MainMenu.hpp"
#include "ui/TrainMenu.hpp"
#include "ui/PlayViewer.hpp"

using namespace ftxui;

int main()
{
  ScreenInteractive screen = ScreenInteractive::Fullscreen();
  AppState state;
  Component home_component = MakeMainMenu(state, screen.ExitLoopClosure());
  Component train_component = MakeTrainMenu(state);
  Component game_component = MakePlayViewer(state);
  Component tab_container = Container::Tab({
										  home_component,
										  train_component,
										  game_component,
	},
	&state.tab_index);
  screen.Loop(tab_container);
  return 0;
}
