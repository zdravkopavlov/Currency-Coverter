# settings.py

import os
import sys
import json

DEFAULT_SETTINGS = {
    "start_with_windows": False,
    "start_minimized": True,
    "always_on_top": True,
    "theme": 2,
    "auto_check_updates": True,
    "auto_copy_result": True,
    "remember_last_direction": True,
    "last_direction_bgn_to_eur": True,
    "x": None,
    "y": None,
    "minimal_mode": False
}

def get_user_settings_path():
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    settings_folder = os.path.join(appdata, "BGN_EUR_Converter")
    if not os.path.exists(settings_folder):
        os.makedirs(settings_folder)
    return os.path.join(settings_folder, "settings.json")

def load_settings():
    path = get_user_settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    path = get_user_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f)
    except Exception:
        pass

def get_theme(settings):
    idx = settings.get("theme", 2)
    if idx == 2:
        if sys.platform == "win32":
            try:
                import winreg
                key = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as regkey:
                    val, _ = winreg.QueryValueEx(regkey, "AppsUseLightTheme")
                return "light" if val == 1 else "dark"
            except Exception:
                return "light"
        return "light"
    return "light" if idx == 0 else "dark"
