#ifndef MAIN_MENU_HPP
#define MAIN_MENU_HPP

#include <ftxui/component/component.hpp>
#include "State.hpp"
#include <functional>

ftxui::Component MakeMainMenu(AppState& state, std::function<void()> quit);

#endif // MAIN_MENU_HPP
