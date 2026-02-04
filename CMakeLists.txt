cmake_minimum_required(VERSION 3.14)
project(my_ftxui_app)

include(FetchContent)
FetchContent_Declare(ftxui
  GIT_REPOSITORY https://github.com/ArthurSonzogni/FTXUI
  GIT_TAG main
)
FetchContent_MakeAvailable(ftxui)

add_executable(QB-Player
    src/main.cpp
    src/components/MainMenu.cpp
    src/components/TrainMenu.cpp
)
target_include_directories(QB-Player PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(QB-Player PRIVATE ftxui::component ftxui::dom ftxui::screen)