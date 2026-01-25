import ctypes
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


def lighten_color_subtract(hex_color, amount=40):
    """
    Затемняет цвет вычитанием значения из каждого канала
    amount: значение от 0 до 255
    """
    hex_color = hex_color.lstrip('#')

    r = min(255, int(hex_color[0:2], 16) + amount)
    g = min(255, int(hex_color[2:4], 16) + amount)
    b = min(255, int(hex_color[4:6], 16) + amount)

    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_color):
    """Конвертирует HEX в RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Конвертирует HSV в RGB используя QColor"""
    r, g, b = rgb
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def log_error(path=os.path.join(os.path.expanduser("~"), "Desktop"), error="", method_prefix="", song=""):
    """Простой метод логирования ошибок"""
    try:
        # Путь к файлу на рабочем столе
        log_file = os.path.join(path, "logs.txt")

        # Создаем файл если не существует
        if not os.path.exists(log_file):
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("=== Лог ошибок плеера ===\n\n")

        # Формируем запись
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_type = type(error).__name__
        stacktrace = traceback.format_exc()

        log_entry = f"[{timestamp}] | МЕТОД: {method_prefix} | ПЕСНЯ: {song} | {error_type}: {str(error)}\n{stacktrace}\n"

        # Записываем в файл
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(log_entry)
            f.write("=" * 60 + "\n\n")

    except Exception as log_e:
        print(f"Ошибка при логировании: {log_e}")


def get_resource_path(relative_path):
    """
    Получает абсолютный путь к ресурсу
    """
    if hasattr(sys, '_MEIPASS'):
        # Режим .exe (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # Режим локального запуска
        base_path = Path(__file__).parent.parent

    return os.path.join(base_path, relative_path)


# ЧИТАЕМ НАСТРОЙКИ ИЗ ПАПКИ APPDATA И СОЗДАЕМ, ЕСЛИ ИХ НЕТ
def check_settings():
    appdata_dir = Path(os.getenv('APPDATA')) / "WorkClock"
    appdata_dir.mkdir(parents=True, exist_ok=True)

    file_path = appdata_dir / "settings.json"
    if not file_path.exists():
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                "x": "1500",
                "y": "100",
                "work_interval": "30",
                "rest_interval": "5",
                "music_path": "",
                "random": False,
                "background_color": "#333333",
                "first_gradient_color": "#FB06AD",
                "second_gradient_color": "#FF8C00",
                "lock_window": True,
                "background_transparency": "99",
                "current_color_scheme": 1,
                "volume":50,
                "scheme_1_first_color": "#FB06AD",
                "scheme_1_second_color": "#FF8C00",
                "scheme_2_first_color": "#72ffd8",
                "scheme_2_second_color": "#052d0e",
                "scheme_3_first_color": "#FF9900",
                "scheme_3_second_color": "#573400",
                "scheme_4_first_color": "#FF59F7",
                "scheme_4_second_color": "#5E0C5A",
                "scheme_5_first_color": "#659AFC",
                "scheme_5_second_color": "#06245E",
                "time_font": "PT Mono"
            }, f, indent=4)


# ВОЗВРАЩАЕТ НАСТРОЙКИ ИЗ APPDATA
def load_settings():
    appdata = os.getenv('APPDATA')
    app_dir = Path(appdata) / "WorkClock" / 'settings.json'
    try:
        with open(app_dir, "r", encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Файл настроек не найден или поврежден")
        return None


def getPathString(folder_path):
    folder_name = os.path.basename(folder_path)
    parent_path = os.path.dirname(folder_path)
    parent_name = os.path.basename(parent_path) if parent_path else ""

    if parent_name:
        return f"{parent_name} › {folder_name}"
    else:
        return folder_name


def check_exists(file_path):
    return file_path and os.path.exists(file_path)
