import json
import os
import sys
from pathlib import Path
import keyboard
from PyQt5.QtCore import QPointF, QEasingCurve, QRect, QThread, pyqtSignal
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QConicalGradient, QIcon, QFontDatabase
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication, QVBoxLayout, QLineEdit, QLabel, QHBoxLayout, QSlider, \
    QFileDialog, QSystemTrayIcon, QMenu, QAction

from components.checkbox import CheckboxWidget
from components.color_scheme_square import ColorSchemeSquare
from components.flip_window import FlipCard
from components.intelval_widget import IntervalInputWidget
from components.play_button import PlayButton
from components.player import AudioPlayerThread
from components.service_button import ServiceButton
from components.pick_music_folder_button import PickMusicFolderButton
from components.slider import Slider
from components.time_label import TimeLabel
from components.utils import getPathString, get_resource_path, check_settings, load_settings
from components.utils import lighten_color_subtract



class GlobalKeyListener(QThread):
    """Поток для отслеживания глобальных нажатий клавиш"""
    key_pressed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        """Основной цикл потока"""
        # Обработка всех нажатий
        keyboard.hook(self.on_key_event)

    def on_key_event(self, event):
        """Обработчик события клавиатуры"""
        key_name = event.name
        if event.event_type == keyboard.KEY_UP:
            # Отправляем сигнал в главный поток только когда клавиша отпускается
            self.key_pressed.emit(key_name)

    def stop(self):
        """Остановка потока"""
        keyboard.unhook_all()
        self.quit()


class ClockWindow(QMainWindow):
    def __init__(self, _version):
        super().__init__()
        self.close_setting_touch_area = False  # ФЛАГ ЧТО КУРСОР НАЖАТ В ОБЛАСТИ ЗАКРЫТИЯ (>650)
        self.settings_closed = True  # ФЛАГ ЧТО НАСТРОЙКИ ЗАКРЫТЫ
        self.closing = False  # ФЛАГ ЧТО НАСТРОЙКИ РАСТЯГИВАЮТСЯ ДЛЯ ЗАКРЫТИЯ В ДАННЫЙ МОМЕНТ
        self.initial_pos = None
        self.original_height = 650
        app_directory = Path(__file__).parent  # Ищет родительский каталог проекта
        resource_path = app_directory / 'resources'
        self.version = _version
        self.settings = load_settings()
        self.time_font = self.settings['time_font']
        self.background_color = self.settings['background_color']
        self.first_gradient_color = self.settings['first_gradient_color']
        self.second_gradient_color = self.settings['second_gradient_color']
        self.x_value = int(self.settings['x'])
        self.y_value = int(self.settings['y'])
        self.lock_window = self.settings['lock_window']
        self.background_transparency = self.settings['background_transparency']
        self.current_color_scheme = self.settings['current_color_scheme']
        self.volume = int(self.settings['volume'])

        self.scheme_1_first_color = self.settings['scheme_1_first_color']
        self.scheme_1_second_color = self.settings['scheme_1_second_color']
        self.scheme_2_first_color = self.settings['scheme_2_first_color']
        self.scheme_2_second_color = self.settings['scheme_2_second_color']
        self.scheme_3_first_color = self.settings['scheme_3_first_color']
        self.scheme_3_second_color = self.settings['scheme_3_second_color']
        self.scheme_4_first_color = self.settings['scheme_4_first_color']
        self.scheme_4_second_color = self.settings['scheme_4_second_color']
        self.scheme_5_first_color = self.settings['scheme_5_first_color']
        self.scheme_5_second_color = self.settings['scheme_5_second_color']

        self.color_schemes_list = {}

        self.drag_pos = None
        self.set_window_flags(self.lock_window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # БЕЗ ФОНА
        self.setGeometry(self.x_value, self.y_value, 330, 900)

        # ПЕРЕМЕННАЯ ВЕЛИЧИНА СДВИГА ИНДИКАТОРА
        self.start_dash = 1.0

        # ПЕРИОДЫ ТАЙМЕРА (в секундах)
        self.rest_interval = int(self.settings['rest_interval']) * 60  # 5 минут перерыв
        self.work_interval = int(self.settings['work_interval']) * 60  # 25 минут работа

        # Состояние таймера
        self.is_running = False
        self.is_rest_period = False  # False = работа, True = перерыв
        self.remaining_time = 0  # Сколько секунд осталось до конца периода

        # ГЛАВНЫЙ КОНТЕЙНЕР
        self.root_container = QWidget(self)
        self.inner_total_x = 15
        self.inner_total_y = 15
        self.root_container.setGeometry(self.inner_total_x, self.inner_total_y, 300, 120)
        self.root_container.setStyleSheet(f"""
                       QWidget{{
                       background-color: #{self.background_transparency}1E1F22;
                       border-radius: 60px;
                       padding: 0px;
                       }}""")

        delete_label = QLabel(self.root_container)
        delete_label.setGeometry(15, 11, 250, 90)
        delete_label.setText("Удалить")
        delete_label.setStyleSheet("""
                       QLabel {
                           padding: 0px;
                           font-size: 40px;
                           font-weight: bold;
                           font-family: 'PT Mono';
                           color: #00FFFFFF;
                           background-color: transparent;
                       }
                       """)

        # Таймер
        self.tick_timer = QTimer()
        self.tick_timer.timeout.connect(self.tick_tack)
        self.tick_timer.setInterval(1000)  # Обновление каждую секунду

        # Основной layout для корневого контейнера
        main_layout = QVBoxLayout(self.root_container)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # КНОПКА PLAY И VBOX
        top_widget = QWidget()
        main_layout.addWidget(top_widget, alignment=Qt.AlignTop)
        top_widget.setStyleSheet("""
                       QWidget{
                       background-color: transparent;
                       border-radius: 60px;
                       padding: 0px;
                       }""")

        hbox = QHBoxLayout(top_widget)
        hbox.setSpacing(0)
        hbox.setContentsMargins(0, 0, 0, 0)

        # VBOX - ВРЕМЯ И КНОПКА "ОТКРЫТЬ"
        self.time_widget = QWidget()
        self.time_widget.setStyleSheet("""
                       QWidget{
                       background-color: transparent;
                       border-radius: 60px;
                       padding: 0px;
                       }""")
        self.vbox = QVBoxLayout(self.time_widget)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.setSpacing(0)
        self.timer_label = TimeLabel(self.time_font)
        self.timer_label.fontChanged.connect(self.save_settings)

        # ПЛЕЕР МУЗЫКИ
        self.audio_player = AudioPlayerThread(self.volume)
        self.audio_player.start()
        self.audio_player.set_music_folder(self.settings['music_path'])
        self.audio_player.random = self.settings['random']

        # КНОПКА ОТКРЫТЬ
        self.open_button = ServiceButton('▼', 120)
        self.open_button.clicked.connect(self.open_settings)
        self.vbox.addWidget(self.timer_label, alignment=Qt.AlignHCenter)
        self.vbox.addWidget(self.open_button, alignment=Qt.AlignHCenter)

        # КНОПКА PLAY
        play_button_layout = QHBoxLayout(top_widget)
        play_button_layout.setAlignment(Qt.AlignLeft)

        self.play_button = PlayButton(self.volume, self.time_widget, delete_label)
        self.play_button.volume_change.connect(lambda value:{
            self.save_settings(),
            self.audio_player.set_volume(value/100)
        })
        self.play_button.left_clicked.connect(self.play_pause)
        self.play_button.next.connect(self.audio_player.play_next_track)
        self.play_button.back.connect(self.audio_player.play_previous_track)
        self.play_button.delete_track.connect(self.audio_player.delete_current_track)

        hbox.addWidget(self.play_button)
        hbox.addWidget(self.time_widget)

        # КОНТЕЙНЕР НАСТРОЕК
        self.flip_card = FlipCard(self.first_gradient_color)
        self.audio_player.update_song_history.connect(self.flip_card.update_song_history)
        main_layout.addWidget(self.flip_card, alignment=Qt.AlignBottom)
        self.bottom_widget = QWidget()
        self.flip_card.set_front_widget(self.bottom_widget)
        self.bottom_widget.setStyleSheet("""
                         QWidget{
                        background-color: transparent;
                        border: none;
                        border-radius: 30px;
                        padding: 0px;
                        }
                        """)
        self.flip_card.hide()  # Изначально скрываем нижнюю часть
        settings_vbox = QVBoxLayout(self.bottom_widget)
        settings_vbox.setContentsMargins(0, 0, 0, 0)
        settings_vbox.setSpacing(20)
        settings_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ПЕРВЫЕ 2 ПОЛЯ: ВВОД РАБОЧЕГО ПЕРИОДА И ПЕРИОДА ОТДЫХА
        first_settings_widget = QWidget()
        first_settings_widget.setStyleSheet("""
                 QWidget{
                background-color: transparent;
                border: none;
                 padding: 0px;
                }
                """)
        first_settings_hbox = QHBoxLayout(first_settings_widget)
        first_settings_hbox.setContentsMargins(0, 0, 0, 0)
        first_settings_hbox.setSpacing(10)

        # ВВОД РАБОЧЕГО ПЕРИОДА
        self.work_interval_widget = IntervalInputWidget(self, self.work_interval, "Рабочий интервал", "work.svg")
        self.work_interval_widget.textChanged.connect(lambda text: {
            self.handle_text_input(text, self.work_interval_widget)
        })
        first_settings_hbox.addWidget(self.work_interval_widget)

        # ВВОД ПЕРИОДА ОТДЫХА
        self.rest_interval_widget = IntervalInputWidget(self, self.rest_interval, "Интервал отдыха", "rest.svg")
        self.rest_interval_widget.textChanged.connect(lambda text: {
            self.handle_text_input(text, self.rest_interval_widget)
        })

        first_settings_hbox.addWidget(self.rest_interval_widget)
        settings_vbox.addWidget(first_settings_widget, alignment=Qt.AlignCenter)

        # ВТОРЫЕ 2 ПОЛЯ: КНОПКА РАНДОМА И НАСТРОЙКА ФОНА
        second_settings_widget = QWidget()
        second_settings_widget.setStyleSheet("""
                         QWidget{
                        background-color: transparent;
                        padding: 0px;
                        }
                        """)
        second_settings_hbox = QHBoxLayout(second_settings_widget)
        second_settings_hbox.setContentsMargins(0, 0, 0, 0)
        second_settings_hbox.setSpacing(10)

        # КНОПКА РАНДОМА
        random_widget = CheckboxWidget(self, "Случайное воспроизведение", "random.svg", self.settings['random'])
        random_widget.stateChanged.connect(lambda state: {
            self.audio_player.switch_random(state),
            self.save_settings(),
        })
        second_settings_hbox.addWidget(random_widget)

        # КНОПКА БЛОКИРОВКИ ОКНА
        lock_window_widget = CheckboxWidget(self, "Поверх всех окон", "lock.svg", self.lock_window)
        lock_window_widget.stateChanged.connect(lambda state: {
            self.set_window_flags(state),
            self.save_settings()
        })
        second_settings_hbox.addWidget(lock_window_widget)
        settings_vbox.addWidget(second_settings_widget, alignment=Qt.AlignCenter)

        # СЛАЙДЕР ПРОЗРАЧНОСТИ ФОНА
        self.background_transparent_slider = Slider(self, "Прозрачность фона", self.first_gradient_color)
        self.background_transparent_slider.setRange(1, 100)
        self.background_transparent_slider.setValue(
            int(self.background_transparency) if self.background_transparency != '' else 100)
        self.background_transparent_slider.valueChanged.connect(self.change_background_color)

        settings_vbox.addWidget(self.background_transparent_slider, alignment=Qt.AlignmentFlag.AlignCenter)

        # ТРЕТЬИ 2 ПОЛЯ: НАСТРОЙКА ПЕРВОГО И ВТОРОГО ЦВЕТА
        third_settings_widget = QWidget()
        third_settings_widget.setStyleSheet("""
                                QWidget{
                               background-color: transparent;
                               border: none;
                               }
                               """)
        third_settings_hbox = QHBoxLayout(third_settings_widget)
        third_settings_hbox.setSpacing(0)

        for i in range(1, 6):
            color_scheme = ColorSchemeSquare(self, i, self.settings[f'scheme_{i}_first_color'],
                                             self.settings[f'scheme_{i}_second_color'])
            color_scheme.clicked.connect(lambda number, first_color, second_color: {
                self.set_gradient_color(number, first_color, second_color),
            })
            if i == self.current_color_scheme:
                color_scheme.set_is_current(True)
            self.color_schemes_list[i] = color_scheme
            third_settings_hbox.addWidget(color_scheme)
        settings_vbox.addWidget(third_settings_widget)

        # КНОПКА ВЫБОРА ПАПКИ С МУЗЫКОЙ
        self.music_widget = QWidget()
        settings_vbox.addWidget(self.music_widget)

        self.music_hbox = QHBoxLayout(self.music_widget)
        self.music_hbox.setContentsMargins(0, 0, 0, 0)
        self.select_folder_button = PickMusicFolderButton(self,
                                                          getPathString(self.settings['music_path']) if self.settings[
                                                                                                            'music_path'] != '' else 'Музыка',
                                                          250, "Папка с музыкой")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.music_hbox.addWidget(self.select_folder_button)

        # СЛАЙДЕР ВРЕМЕНИ
        self.time_slider = Slider(self, "Перемотка времени", self.first_gradient_color)
        self.time_slider.valueChanged.connect(self.set_remain_time)
        settings_vbox.addWidget(self.time_slider, alignment=Qt.AlignmentFlag.AlignCenter)


        # АНИМАЦИЯ ОТКРЫТИЯ
        self.open_settings_animation = QPropertyAnimation(self.root_container, b"geometry")
        self.open_settings_animation.setStartValue(QRect(self.inner_total_x, self.inner_total_y, 300, 120))
        self.open_settings_animation.setEndValue(
            QRect(self.inner_total_x, self.inner_total_y, 300, self.original_height))
        self.open_settings_animation.setDuration(1200)
        self.open_settings_animation.setEasingCurve(QEasingCurve.Type.OutElastic)
        # АНИМАЦИЯ ЗАКРЫТИЯ
        self.close_settings_animation = QPropertyAnimation(self.root_container, b"geometry")
        self.close_settings_animation.setStartValue(
            QRect(self.inner_total_x, self.inner_total_y, 300, self.original_height))
        self.close_settings_animation.setEndValue(QRect(self.inner_total_x, self.inner_total_y, 300, 120))
        self.close_settings_animation.setDuration(550)
        self.close_settings_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # АНИМАЦИЯ ПРУЖИНКИ
        self.bounce_settings_animation = QPropertyAnimation(self.root_container, b"geometry")
        self.bounce_settings_animation.setDuration(200)
        self.bounce_settings_animation.setEasingCurve(QEasingCurve.Type.OutBounce)

        self.key_listener = GlobalKeyListener()
        self.key_listener.key_pressed.connect(self.on_key_pressed)
        self.key_listener.start()

        self.reset_timer()
        self.init_tray()
        self.load_fonts()

    # ОБРАБОТКА КЛАВИШ ДЛЯ ПЕРЕКЛЮЧЕНИЯ ТРЕКОВ
    def on_key_pressed(self, key_name):
        if key_name == 'page up':
            self.audio_player.play_previous_track()
        elif key_name == 'page down':
            self.audio_player.play_next_track()

    def handle_text_input(self, text, field):
        if len(text) < 4:
            if len(text) == 3:
                field.setStyle("""
                        QLineEdit{
                            border: none;
                            padding: 0px;
                            color: #E6E6E6;
                            font-size: 20px;
                             font-weight: bold;
                            font-family: 'PT Mono';
                            background-color: transparent;
                        }""")
            if len(text) == 2:
                field.setStyle("""
                        QLineEdit{
                            border: none;
                            padding: 0px;
                            color: #E6E6E6;
                            font-size: 25px;
                             font-weight: bold;
                            font-family: 'PT Mono';
                            background-color: transparent;
                        }""")
            self.save_settings()
        else:
            field.setText("30")

    def set_window_flags(self, state):
        self.lock_window = state
        # Сохраняем текущую позицию и размер
        current_geometry = self.geometry()
        is_visible = self.isVisible()

        if self.lock_window:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                                Qt.WindowType.WindowStaysOnTopHint |
                                Qt.Tool |
                                Qt.X11BypassWindowManagerHint)
        else:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                                Qt.Tool |
                                Qt.X11BypassWindowManagerHint)

        # Восстанавливаем геометрию и показываем окно
        self.setGeometry(current_geometry)
        if is_visible:
            self.show()

    def change_background_color(self, value):
        value_string = str(value)
        transparency = value_string if len(value_string) == 2 else "0" + value_string if len(value_string) < 2 else ""
        self.background_transparency = transparency
        self.root_container.setStyleSheet(f"""
                               QWidget{{
                               background-color: #{transparency}1E1F22;
                               border-radius: 60px;
                               }}""")

    def set_gradient_color(self, index, first_color, second_color):
        for key, schema in self.color_schemes_list.items():
            if key != index:
                schema.set_is_current(False)
            else:
                self.current_color_scheme = key
                schema.set_is_current(True)
                setattr(self, f'scheme_{key}_first_color', first_color)
                setattr(self, f'scheme_{key}_second_color', second_color)

        self.flip_card.set_font_color(first_color)
        self.background_transparent_slider.set_color(first_color)
        self.time_slider.set_color(first_color)
        self.first_gradient_color = first_color
        self.play_button.set_first_gradient_color(first_color)

        self.second_gradient_color = second_color
        self.play_button.set_second_gradient_color(second_color)

        self.save_settings()

    def update_button_style(self, button, color):
        """Обновляет стиль кнопки с новым цветом"""
        button.setStyleSheet(f"""
            QPushButton{{
                background-color: {color};
                border: 1px solid {lighten_color_subtract(color, 40)};
                border-radius: 20px;
            }}
            QPushButton::hover{{
                border: 3px solid {lighten_color_subtract(color, 40)};
                border-radius: 20px;
            }}
        """)

    # ЗАГРУЖАЕТ ШРИФТЫ В ЛОКАЛЬНУЮ БАЗУ
    def load_fonts(self):
        font_db = QFontDatabase()
        fonts = [
            "PTMono.ttf",
            "HYWenHei.ttf",
            "Stengazeta.ttf",
            "Ringus-Regular.otf"
        ]
        for font_file in fonts:
            font_path = get_resource_path(font_file)
            font_db.addApplicationFont(str(font_path))

    def init_tray(self):
        # Создаем иконку в системном трее
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(get_resource_path("resources/icon2.ico")))
        self.tray_icon.setToolTip(f"WorkClock v{self.version} - Нажмите дважды, чтобы скрыть")
        # Создаем контекстное меню для трея
        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
               /* Основное меню */
               QMenu {
                   background-color: #2c3e50;
                   border: 1px solid #34495e;
                   border-radius: 0px;
                   padding: 5px;
                   color: #ecf0f1;
                   font-family: 'Segoe UI', sans-serif;
                   font-size: 15px;
               }

               /* Пункты меню */
               QMenu::item {
                   background-color: transparent;
                   border-radius: 8px;
                   padding: 8px 16px;
                   margin: 2px;
                   min-width: 150px;
               }

               /* Пункты меню при наведении */
               QMenu::item:selected {
                   background-color: #3498db;
                   color: white;
               }


               /* Разделитель */
               QMenu::separator {
                   height: 1px;
                   background-color: #34495e;
               }

               /* Иконка в меню */
               QMenu::icon {
                   padding-left: 16px;
               }

           """)

        pause_song_action = QAction("Пауза/Играть", self)
        pause_song_action.setIcon(QIcon(get_resource_path("resources/play.ico")))
        pause_song_action.triggered.connect(self.tray_stop_pause)
        tray_menu.addAction(pause_song_action)
        tray_menu.addSeparator()

        next_song_action = QAction("Следующий трек", self)
        next_song_action.setIcon(QIcon(get_resource_path("resources/next.ico")))
        next_song_action.triggered.connect(self.audio_player.play_next_track)
        tray_menu.addAction(next_song_action)
        tray_menu.addSeparator()

        previous_song_action = QAction("Предыдущий трек", self)
        previous_song_action.setIcon(QIcon(get_resource_path("resources/prev.ico")))
        previous_song_action.triggered.connect(self.audio_player.play_previous_track)
        tray_menu.addAction(previous_song_action)
        tray_menu.addSeparator()

        quit_action = QAction("Закрыть", self)
        quit_action.setIcon(QIcon(get_resource_path("resources/quit.ico")))
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_stop_pause(self):
        self.play_pause()
        self.play_button.is_playing = not self.play_button.is_playing

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()

    # СОХРАНЯЕТ НАСТРОЙКИ
    def save_settings(self):
        settings = {
            'x': self.x_value,
            'y': self.y_value,
            'work_interval': self.work_interval_widget.text() if self.work_interval_widget.text() != "" else "30",
            'rest_interval': self.rest_interval_widget.text() if self.rest_interval_widget.text() != "" else "5",
            'music_path': self.audio_player.path_to_music,
            'random': self.audio_player.random,
            'background_color': self.background_color,
            "first_gradient_color": self.first_gradient_color,
            "second_gradient_color": self.second_gradient_color,
            "lock_window": self.lock_window,
            "background_transparency": self.background_transparency,
            "current_color_scheme": self.current_color_scheme,
            "volume":self.play_button.getVolume(),
            "scheme_1_first_color": self.scheme_1_first_color,
            "scheme_1_second_color": self.scheme_1_second_color,
            "scheme_2_first_color": self.scheme_2_first_color,
            "scheme_2_second_color": self.scheme_2_second_color,
            "scheme_3_first_color": self.scheme_3_first_color,
            "scheme_3_second_color": self.scheme_3_second_color,
            "scheme_4_first_color": self.scheme_4_first_color,
            "scheme_4_second_color": self.scheme_4_second_color,
            "scheme_5_first_color": self.scheme_5_first_color,
            "scheme_5_second_color": self.scheme_5_second_color,
            "time_font": self.timer_label.get_time_font()
        }
        appdata = os.getenv('APPDATA')
        app_dir = Path(appdata) / "WorkClock" / 'settings.json'

        with open(str(app_dir), "w", encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

    def select_folder(self):
        # Открываем диалог выбора папки
        folder_path = QFileDialog.getExistingDirectory(self, 'Выберите папку с песнями')
        # Если пользователь выбрал папку
        if folder_path:
            self.select_folder_button.setText(getPathString(folder_path))
            self.audio_player.set_music_folder(folder_path)
            self.save_settings()

    def set_remain_time(self, value):
        if self.is_rest_period:
            self.remaining_time = self.rest_interval - value
        else:
            self.remaining_time = self.work_interval - value
        self.update_timer()

    def play_pause(self):
        # Запуск/пауза музыки
        self.audio_player.switch_play_pause()

        # Запуск/пауза таймера
        if not self.is_running:
            self.start_timer()
        else:
            self.pause_timer()

    def start_timer(self):
        """Запуск таймера"""
        if not self.is_running:
            self.is_running = True
            self.tick_timer.start()

    def pause_timer(self):
        """Пауза таймера"""
        if self.is_running:
            self.is_running = False
            self.tick_timer.stop()

    def tick_tack(self):
        # ОБНОВЛЯЕМ СЛАЙДЕР
        # self.update_time_slider()
        self.update_timer()

    def update_timer(self):
        """Обновление таймера каждую секунду"""
        self.remaining_time -= 1

        # Обновляем отображение времени
        if not self.play_button.is_deleting:
            minutes = self.remaining_time // 60
            seconds = self.remaining_time % 60
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

        # Обновляем индикатор обводки
        self.update_progress_indicator()

        if self.remaining_time == 4:
            self.audio_player.play_alarm()
            if not self.is_rest_period:
                self.audio_player.stop_music(5000)
                self.audio_player.set_background_volume(5)

        # Если время вышло
        if self.remaining_time <= 0:
            if self.is_rest_period:
                self.audio_player.play_music()
                self.audio_player.set_background_volume(1)
            self.switch_period()

    def update_time_slider(self):
        if self.is_rest_period:
            self.time_slider.setValue(self.rest_interval - self.remaining_time)
        else:
            self.time_slider.setValue(self.work_interval - self.remaining_time)

    def update_progress_indicator(self):
        """Обновление индикатора прогресса (обводки)"""
        if self.is_rest_period:

            # Для перерыва: от 0.98 до 0 по мере уменьшения времени
            total_time = self.rest_interval
            elapsed = total_time - self.remaining_time

            progress = elapsed / total_time
            self.start_dash = 1 - (progress * 0.99)
        else:

            # Для работы: от 0.98 до 0 по мере уменьшения времени
            total_time = self.work_interval
            elapsed = total_time - self.remaining_time

            progress = elapsed / total_time
            self.start_dash = 1 - (progress * 0.99)

        # Ограничиваем значение в пределах 0-0.98
        self.start_dash = max(0.0, min(1, self.start_dash))

        # Обновляем отрисовку
        self.update()

    def switch_period(self):
        """Переключение между работой и перерывом"""
        if self.is_rest_period:
            # Завершился перерыв, начинаем работу
            self.is_rest_period = False
            self.remaining_time = self.work_interval
        else:
            # Завершилась работа, начинаем перерыв
            self.is_rest_period = True
            self.remaining_time = self.rest_interval

        # Сбрасываем индикатор
        self.start_dash = 1

        self.time_slider.setValue(0)
        self.time_slider.setRange(0, self.remaining_time - 6)

    def reset_timer(self):
        """Сброс таймера"""
        self.pause_timer()
        self.is_rest_period = False
        self.remaining_time = self.work_interval
        self.start_dash = 1  # Полная обводка

        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

        self.play_button.is_playing = False
        self.time_slider.setValue(0)
        self.time_slider.setRange(0, self.remaining_time - 8)
        self.update()

    def open_settings(self):
        """Открывает настройки - показываем нижнюю часть и увеличиваем контейнер"""
        if self.settings_closed:
            self.settings_closed = False
            self.flip_card.show()
            self.open_button.hide()
            self.open_settings_animation.start()

    def close_settings(self):
        """Закрывает настройки - скрываем нижнюю часть и уменьшаем контейнер"""
        if not self.is_rest_period:
            if self.work_interval_widget.text().isdigit() and int(self.work_interval_widget.text()) > 0 and int(
                    self.work_interval_widget.text()) < 99:
                new_work_interval = int(self.work_interval_widget.text()) * 60
                if self.work_interval != new_work_interval:
                    self.work_interval = new_work_interval
                    self.time_slider.setRange(0, self.work_interval - 8)
                    self.time_slider.setValue(self.work_interval - self.remaining_time)

        if self.is_rest_period:
            if self.rest_interval_widget.text().isdigit() and int(self.rest_interval_widget.text()) > 0 and int(
                    self.rest_interval_widget.text()) < 99:
                new_rest_interval = int(self.rest_interval_widget.text()) * 60
                if self.rest_interval != new_rest_interval:
                    self.rest_interval = new_rest_interval
                    self.time_slider.setRange(0, self.rest_interval - 8)
                    self.time_slider.setValue(self.rest_interval - self.remaining_time)

        self.flip_card.hide()
        self.open_button.show()
        self.close_settings_animation.start()
        self.settings_closed = True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ГРАДИЕНТНАЯ ЦВЕТНАЯ ОБВОДКА
        gradient = QConicalGradient()  # Конический градиент
        gradient.setCenter(QPointF(self.root_container.rect().center()))
        gradient.setAngle(90)  # Текущий угол анимации
        painter.setBrush(QBrush(QColor("transparent")))

        if not self.is_rest_period:
            gradient.setColorAt(1.00, QColor(self.first_gradient_color))
            gradient.setColorAt(0.999, QColor("transparent"))
            gradient.setColorAt(self.start_dash, QColor("transparent"))
            gradient.setColorAt(self.start_dash - 0.01, QColor(self.second_gradient_color))
            gradient.setColorAt(0.00, QColor(self.first_gradient_color))
        else:
            gradient.setColorAt(1.00, QColor(self.first_gradient_color))
            gradient.setColorAt(0.999, QColor(self.first_gradient_color))
            gradient.setColorAt(self.start_dash, QColor(self.second_gradient_color))
            gradient.setColorAt(self.start_dash - 0.01, QColor("transparent"))
            gradient.setColorAt(0.00, QColor("transparent"))

        pen = QPen(QBrush(gradient), 10)
        painter.setPen(pen)
        painter.drawRoundedRect(self.inner_total_x - 10, self.inner_total_y - 10, self.root_container.width() + 20,
                                self.root_container.height() + 20, 69, 69)

        self.update()

    # СРАБАТЫВАЕТ ПРИ НАЖАТИИ
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
            if not self.settings_closed:
                self.initial_pos = event.pos()
                if self.initial_pos.y() > 600 + self.inner_total_y:
                    self.close_setting_touch_area = True
                else:
                    self.close_setting_touch_area = False

    # СРАБАТЫВАЕТ ПРИ ПЕРЕМЕЩЕНИИ
    def mouseMoveEvent(self, event):
        if self.drag_pos is not None and event.buttons() == Qt.LeftButton:
            if not self.close_setting_touch_area:
                self.move(self.pos() + event.globalPos() - self.drag_pos)
                self.drag_pos = event.globalPos()
            else:
                if not self.settings_closed and self.initial_pos:
                    # Вычисляем разницу в положении курсора
                    delta = event.pos().y() - self.initial_pos.y()
                    # Вычисляем новую высоту
                    new_height = self.original_height + delta
                    # Ограничиваем минимальную высоту
                    if new_height < self.original_height:
                        new_height = self.original_height
                    # Ограничиваем максимальную высоту
                    if new_height > self.original_height + 50:
                        new_height = self.original_height + 50
                    # Обновляем геометрию изображения
                    self.root_container.setGeometry(
                        self.root_container.x(),
                        self.root_container.y(),
                        self.root_container.width(),
                        new_height
                    )
                    self.update()
                    if self.original_height + 50 >= new_height > self.original_height + 45:
                        self.closing = True
                    else:
                        self.closing = False

    # СРАБАТЫВАЕТ ПРИ ОТПУСКАНИИ
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.settings_closed:
                if self.close_setting_touch_area:
                    if self.closing:
                        self.close_settings()
                    else:
                        self.bounce_settings_animation.setStartValue(
                            QRect(self.inner_total_x, self.inner_total_y, 300, self.root_container.height()))
                        self.bounce_settings_animation.setEndValue(
                            QRect(self.inner_total_x, self.inner_total_y, 300, self.original_height))
                        self.bounce_settings_animation.start()
            self.close_setting_touch_area = False
            self.closing = False
            self.x_value = self.pos().x()
            self.y_value = self.pos().y()
            self.save_settings()
            self.drag_pos = None
            self.initial_pos = None


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        check_settings()
        version = "2.0.5"
        window = ClockWindow(version)
        window.show()
        app.exec()
    except Exception as e:
        print("ОШИБКА в основном методе: ", e)

