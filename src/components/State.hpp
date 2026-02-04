// [SYNTAX] Include Guards: Prevents this file from being included multiple times in a single compilation unit.
// Without this, you might get "redefinition" errors.
#ifndef APP_STATE_HPP
#define APP_STATE_HPP

// [SYNTAX] struct: A collection of variables under one name.
// In C++, struct and class are almost identical, but structs default to 'public' access.
struct AppState
{
  // [SYNTAX] Member Initialization: We can provide default values directly here.
  bool enable_gpu = false;
  bool enable_logging = true;
  bool auto_save = false;

  int num_iterations = 1000;
  int games_per_iteration = 100;
  int update_frequency = 10;
  int evaluation_frequency = 50;
  std::string save_path = "queens_blood_model.pth";
  std::string league_path = "league_checkpoints/";
  int num_envs = 12;
  int num_steps = 128;

  double learning_rate = 0.0003;
  double gamma = 0.99;
  double gae_lambda = 0.95;
  double clip_epsilon = 0.2;
  double entropy_coef = 0.01;
  double value_loss_coef = 0.5;
  double epochs = 10;

  std::vector<int> hidden_dims = { 256, 256 };
  std::string activation = "relu";

  std::string reward_type = "dense";
  int max_turns = 100;

  // Navigation
  int tab_index = 0;
};

#endif // APP_STATE_HPP
