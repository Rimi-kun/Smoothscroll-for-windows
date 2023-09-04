import easing_functions
from win32con import VK_SHIFT

from smoothscroll import (SmoothScroll,
                          SmoothScrollConfig, AppConfig, ScrollConfig)

def import_settings_from_file(file_path):
    with open(file_path, 'r') as file:
        settings = {}
        for line in file:
            key, value = line.strip().split('=')
            settings[key] = value

    return settings

if __name__ == '__main__':
    file_path = 'settings.txt'
    imported_settings = import_settings_from_file(file_path)

    scroll_config = SmoothScrollConfig(
        app_config=[
            AppConfig(
                regexp=r'.*',
                scroll_config=ScrollConfig(
                    distance=int(imported_settings.get('distance', 120)),
                    acceleration=float(imported_settings.get('acceleration', 1.0)),
                    opposite_acceleration=float(imported_settings.get('opposite_acceleration', 1.2)),
                    acceleration_delta=int(imported_settings.get('acceleration_delta', 70)),
                    acceleration_max=int(imported_settings.get('acceleration_max', 14)),
                    duration=int(imported_settings.get('duration', 650)),
                    pulse_scale=int(imported_settings.get('pulse_scale', 7)),
                    ease=easing_functions.LinearInOut,
                    inverted=False,
                    horizontal_scroll_key=VK_SHIFT,
                ),
            ),
            AppConfig(
                path='C:/Windows/explorer.exe',
                enabled=False
            ),
        ]
    )

    smooth_scroll = SmoothScroll(config=scroll_config)
    smooth_scroll.start(is_block=True)
