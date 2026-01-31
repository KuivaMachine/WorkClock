import json
import os
import sys
import traceback
from datetime import datetime

from getpass import getuser
from pathlib import Path
import platform

import psutil
import requests
from dotenv import load_dotenv
from pyexpat.errors import messages
from screeninfo import screeninfo

LOG_FILE_NAME = "FocusTimer - logs"


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
        log_file = os.path.join(path, LOG_FILE_NAME)

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


def check_settings(version):
    if hasattr(sys, '_MEIPASS'):
        # Режим .exe
        base_path = sys._MEIPASS
    else:
        # Режим локального запуска
        base_path = Path(__file__).parent.parent
    env_path = os.path.join(base_path, 'resources', '.env')
    load_dotenv(env_path)

    # Определяем пути
    appdata_dir = Path(os.getenv('APPDATA')) / "FocusTimer"
    appdata_dir.mkdir(parents=True, exist_ok=True)

    file_path = appdata_dir / "settings.json"

    # Определяем стандартные настройки по умолчанию
    default_settings = {
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
        "volume": 50,
        "scheme_1_first_color": "#ffd700",
        "scheme_1_second_color": "#ff00a5",
        "scheme_2_first_color": "#ffffff",
        "scheme_2_second_color": "#ff3ea8",
        "scheme_3_first_color": "#46ff35",
        "scheme_3_second_color": "#053100",
        "scheme_4_first_color": "#303030",
        "scheme_4_second_color": "#000000",
        "time_font": "PT Mono",
        "current_version": version,
        "need_to_send": True,
    }

    # Если файла нет - создаем с настройками по умолчанию
    if not file_path.exists():
        success = send_statistic("настройки записаны с нуля", os.getenv("apple"), os.getenv("kiwi"), version)
        default_settings["need_to_send"] = False if success else True
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, indent=4, ensure_ascii=False)
        return

    # Если файл существует - читаем и проверяем
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            existing_settings = json.load(f)

        # Флаг для отслеживания изменений
        settings_updated = False

        # Проверяем каждый ключ из стандартных настроек
        for key, default_value in default_settings.items():
            # Проверяем текущий номер версии
            if key == "current_version" and key in existing_settings and existing_settings[key] != version:
                existing_settings[key] = version
                success = send_statistic("установлена новая версия поверх старой", os.getenv("apple"), os.getenv("kiwi"), version)
                existing_settings["need_to_send"] = False if success else True
                settings_updated = True

            if key not in existing_settings:
                # Добавляем отсутствующий ключ со значением по умолчанию
                existing_settings[key] = default_value
                settings_updated = True
                print(f"Добавлен отсутствующий ключ: {key} = {default_value}")

        # Проверяем, нужно ли отправить статистику
        if existing_settings["need_to_send"]:
            success = send_statistic("не было интернета (или ключа 'need_to_send')", os.getenv("apple"), os.getenv("kiwi"), version)
            existing_settings["need_to_send"] = False if success else True
            settings_updated = True

        # Если были добавлены новые ключи - сохраняем обновленный файл
        if settings_updated:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_settings, f, indent=4, ensure_ascii=False)
            print("Настройки обновлены - добавлены новые параметры")

    except json.JSONDecodeError:
        # Если файл поврежден, создаем новый
        print("Файл настроек поврежден. Создаю новый...")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(default_settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        log_error(error=str(e), method_prefix="check_settings")
        print(f"Ошибка при чтении настроек: {e}")


# ВОЗВРАЩАЕТ НАСТРОЙКИ ИЗ APPDATA
def load_settings():
    appdata = os.getenv('APPDATA')
    app_dir = Path(appdata) / "FocusTimer" / 'settings.json'
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


def send_statistic(message, apple, kiwi, version):
    try:
        # Основные данные
        main_info = f"""
        <b>🚀 Запущен FocusTimer v{version}</b>
    
        <b>📝 Событие:</b> {message}
        <b>⏰ Время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        <b>👤 Пользователь:</b> {getuser()}
        <b>💻 Система:</b> {platform.system()} {platform.release()}
        <b>👋 Имя ПК:</b> {platform.node()}
        <b>⚙️ Архитектура:</b> {platform.processor()} / {platform.architecture()[0]}
        <b>🧬 Ядра CPU:</b> {psutil.cpu_count(logical=False)}/{psutil.cpu_count(logical=True)}. Загружено - {psutil.cpu_percent(interval=0.1)}%
        <b>💾 Память:</b> ОЗУ - {psutil.virtual_memory().total // (1024 ** 3)} GB, HARD - {psutil.disk_usage('/').free // (1024 ** 3)} свободно из {psutil.disk_usage('/').total // (1024 ** 3)}GB
        <b>🖥️ Мониторы:</b> {(
            f"{len(screeninfo.get_monitors())}шт ({screeninfo.get_monitors()[0].width}x{screeninfo.get_monitors()[0].height})"
            if hasattr(screeninfo, 'get_monitors') and len(screeninfo.get_monitors()) > 0
            else 'N/A'
        )}
        <b>🔋 Питание:</b> {(
            f"{psutil.sensors_battery().percent}%{' 🔌' if psutil.sensors_battery().power_plugged else ' 🔋'}"
            if hasattr(psutil, 'sensors_battery') and psutil.sensors_battery()
            else '🔌'
        )}
            """
        payload = {
            "chat_id": kiwi,
            "text": main_info,
            "parse_mode": "HTML"
        }

        response = requests.post(apple, json=payload)
        return response.status_code == 200
    except Exception:
        return False

