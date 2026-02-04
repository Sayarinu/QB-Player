#ifndef APP_STATE_HPP
#define APP_STATE_HPP

struct AppState {
    bool enable_gpu = false;
    bool enable_logging = true;
    bool auto_save = false;

    // Navigation
    int tab_index = 0;
};

#endif // APP_STATE_HPP
