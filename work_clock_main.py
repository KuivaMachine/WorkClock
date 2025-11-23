import json
import os
import sys
from pathlib import Path

from PyQt5.QtCore import QPointF, QEasingCurve, QRect
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QConicalGradient, QIcon, QFontDatabase
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication, QVBoxLayout, QLineEdit, QLabel, QHBoxLayout, QSlider, \
    QFileDialog, QSystemTrayIcon, QMenu, QAction, QPushButton
from vcolorpicker import ColorPicker

from components.checkbox import CheckboxWidget
from components.flip_window import FlipCard
from components.play_button import PlayButton
from components.player import AudioPlayerThread
from components.service_button import ServiceButton
from components.setting_button import SettingsButton
from components.utils import getPathString, get_resource_path, check_settings, load_settings
from components.utils import lighten_color_subtract, hex_to_rgb, rgb_to_hex


class ClockWindow(QMainWindow):
    def __init__(self, _version):
        super().__init__()
        self.close_setting_touch_area = False   # ФЛАГ ЧТО КУРСОР НАЖАТ В ОБЛАСТИ ЗАКРЫТИЯ (>650)
        self.settings_closed = True             # ФЛАГ ЧТО НАСТРОЙКИ ЗАКРЫТЫ
        self.closing = False                    # ФЛАГ ЧТО НАСТРОЙКИ РАСТЯГИВАЮТСЯ ДЛЯ ЗАКРЫТИЯ В ДАННЫЙ МОМЕНТ
        self.initial_pos = None
        self.original_height = 650
        app_directory = Path(__file__).parent   # Ищет родительский каталог проекта
        resource_path = app_directory / 'resources'
        self.version = _version
        self.settings = load_settings()
        self.background_color = self.settings['background_color']
        self.first_gradient_color = self.settings['first_gradient_color']
        self.second_gradient_color = self.settings['second_gradient_color']
        self.x_value = int(self.settings['x'])
        self.y_value = int(self.settings['y'])
        self.lock_window = self.settings['lock_window']
        self.background_transparency = self.settings['background_transparency']

        self.drag_pos = None
        self.set_window_flags(self.lock_window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # БЕЗ ФОНА
        self.setGeometry(self.x_value, self.y_value, 400, 1000)

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
        self.root_container.setGeometry(50, 50, 300, 120)
        self.root_container.setStyleSheet(f"""
                       QWidget{{
                       background-color: #{self.background_transparency}1E1F22;
                       border-radius: 60px;
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
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(0, 5, 0, 0)

        # КНОПКА PLAY И VBOX
        top_widget = QWidget()
        main_layout.addWidget(top_widget, alignment=Qt.AlignTop)
        top_widget.setStyleSheet("""
         QWidget{
        background-color: transparent;
        }
        """)

        hbox = QHBoxLayout(top_widget)

        # VBOX - ВРЕМЯ И КНОПКА "ОТКРЫТЬ"
        self.time_widget = QWidget()
        self.vbox = QVBoxLayout(self.time_widget)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.timer_label = QLabel("25:00")
        self.timer_label.setStyleSheet("""
                QLabel {
                    padding: 0px;
                    font-size: 45px;
                    font-weight: bold;
                    font-family: 'PT Mono';
                    color: #FFFFFF;
                    background-color: transparent;
                }
                """)

        # ПЛЕЕР МУЗЫКИ
        self.audio_player = AudioPlayerThread()
        self.audio_player.start()
        self.audio_player.set_music_folder(self.settings['music_path'])
        self.audio_player.random = self.settings['random']

        # КНОПКА ОТКРЫТЬ
        self.open_button = ServiceButton('▼', 120)
        self.open_button.clicked.connect(self.open_settings)
        self.vbox.addWidget(self.timer_label, alignment=Qt.AlignHCenter)
        self.vbox.addWidget(self.open_button, alignment=Qt.AlignHCenter)

        # КНОПКА PLAY
        self.play_button = PlayButton(self.time_widget, delete_label)
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
        work_interval_icon = QSvgWidget(str(resource_path / "work.svg"))
        self.work_interval_field = self.initInputField(self.work_interval)
        self.work_interval_field.textChanged.connect(lambda text: {
            self.handle_text_input(text, self.work_interval_field)
        })

        work_interval_widget = QWidget()
        work_interval_widget.setFixedSize(120, 70)
        work_interval_widget.setStyleSheet("""
                                       QWidget{
                                      background-color: transparent;
                                      border: 1px solid #808080;
                                        border-radius: 20px;
                                         padding: 0px 20px;
                                      }
                                       QWidget::hover{
                               background-color: rgba(20, 20, 20, 0.1);
                              border: 2px solid #808080;
                              border-radius: 20px;
                               }
                                      """)
        work_interval_hbox = QHBoxLayout(work_interval_widget)
        work_interval_icon.setStyleSheet("""
        background-color: transparent;
        border: none;
        """)
        work_interval_icon.setFixedSize(50, 50)
        work_interval_hbox.addWidget(self.work_interval_field)
        work_interval_hbox.addWidget(work_interval_icon)
        work_interval_hbox.setSpacing(0)
        first_settings_hbox.addWidget(work_interval_widget)

        # ВВОД ПЕРИОДА ОТДЫХА
        rest_interval_widget = QWidget()
        rest_interval_widget.setFixedSize(120, 70)
        rest_interval_widget.setStyleSheet("""
                                QWidget{
                               background-color: transparent;
                              border: 1px solid #808080;
                              border-radius: 20px;
                               }
                                QWidget::hover{
                                background-color: rgba(20, 20, 20, 0.1);
                              border: 2px solid #808080;
                              border-radius: 20px;
                               }
                               """)
        rest_interval_hbox = QHBoxLayout(rest_interval_widget)
        rest_interval_icon = QSvgWidget(str(resource_path / "rest.svg"))
        rest_interval_icon.setStyleSheet("""
        background-color: transparent;
         border:none;
        """)
        rest_interval_icon.setFixedSize(50, 50)
        self.rest_interval_field = self.initInputField(self.rest_interval)
        self.rest_interval_field.textChanged.connect(lambda text: {
            self.handle_text_input(text, self.rest_interval_field)
        })
        rest_interval_hbox.addWidget(self.rest_interval_field)
        rest_interval_hbox.addWidget(rest_interval_icon)
        rest_interval_hbox.setSpacing(0)
        first_settings_hbox.addWidget(rest_interval_widget)
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
        random_widget = CheckboxWidget("random.svg", self.settings['random'])
        random_widget.stateChanged.connect(lambda state: {
            self.audio_player.switch_random(state),
            self.save_settings(),
        })
        second_settings_hbox.addWidget(random_widget)

        # КНОПКА БЛОКИРОВКИ ОКНА
        lock_window_widget = CheckboxWidget("lock.svg", self.lock_window)
        lock_window_widget.stateChanged.connect(lambda state: {
            self.set_window_flags(state),
            self.save_settings()
        })
        second_settings_hbox.addWidget(lock_window_widget)
        settings_vbox.addWidget(second_settings_widget, alignment=Qt.AlignCenter)

        # СЛАЙДЕР ПРОЗРАЧНОСТИ ФОНА
        self.background_transparent_slider = self.init_slider(self.change_background_color)
        self.background_transparent_slider.setValue(
            int(self.background_transparency) if self.background_transparency else 100)
        self.background_transparent_slider.setRange(1, 100)
        settings_vbox.addWidget(self.background_transparent_slider, alignment=Qt.AlignmentFlag.AlignCenter)

        # ТРЕТЬИ 2 ПОЛЯ: НАСТРОЙКА ПЕРВОГО И ВТОРОГО ЦВЕТА
        third_settings_widget = QWidget()
        third_settings_widget.setStyleSheet("""
                                QWidget{
                               background-color: transparent;
                               border: none;
                                padding: 0px;
                               }
                               """)
        third_settings_hbox = QHBoxLayout(third_settings_widget)
        third_settings_hbox.setContentsMargins(0, 0, 0, 0)
        third_settings_hbox.setSpacing(10)

        # КНОПКА НАСТРОЙКИ ПЕРВОГО ЦВЕТА
        self.first_gradient_color_pick_button = self.create_color_button(self.first_gradient_color,
                                                                         self.change_first_gradient_color)
        third_settings_hbox.addWidget(self.first_gradient_color_pick_button)
        # КНОПКА НАСТРОЙКИ ВТОРОГО ЦВЕТА
        self.second_gradient_color_pick_button = self.create_color_button(self.second_gradient_color,
                                                                          self.change_second_gradient_color)
        third_settings_hbox.addWidget(self.second_gradient_color_pick_button)
        settings_vbox.addWidget(third_settings_widget, alignment=Qt.AlignCenter)

        # КНОПКА ВЫБОРА ПАПКИ С МУЗЫКОЙ
        self.music_widget = QWidget()
        settings_vbox.addWidget(self.music_widget)

        self.music_hbox = QHBoxLayout(self.music_widget)
        self.music_hbox.setContentsMargins(0, 0, 0, 0)
        self.select_folder_button = SettingsButton(
            getPathString(self.settings['music_path']) if self.settings['music_path'] != '' else 'Музыка', 250)
        self.select_folder_button.clicked.connect(self.select_folder)
        self.music_hbox.addWidget(self.select_folder_button)

        # СЛАЙДЕР
        self.time_slider = self.init_slider(self.set_remain_time)
        settings_vbox.addWidget(self.time_slider, alignment=Qt.AlignmentFlag.AlignCenter)

        # АНИМАЦИЯ ОТКРЫТИЯ
        self.open_settings_animation = QPropertyAnimation(self.root_container, b"geometry")
        self.open_settings_animation.setStartValue(QRect(50, 50, 300, 120))
        self.open_settings_animation.setEndValue(QRect(50, 50, 300, self.original_height))
        self.open_settings_animation.setDuration(1200)
        self.open_settings_animation.setEasingCurve(QEasingCurve.Type.OutElastic)
        # АНИМАЦИЯ ЗАКРЫТИЯ
        self.close_settings_animation = QPropertyAnimation(self.root_container, b"geometry")
        self.close_settings_animation.setStartValue(QRect(50, 50, 300, self.original_height))
        self.close_settings_animation.setEndValue(QRect(50, 50, 300, 120))
        self.close_settings_animation.setDuration(550)
        self.close_settings_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # АНИМАЦИЯ ПРУЖИНКИ
        self.bounce_settings_animation = QPropertyAnimation(self.root_container, b"geometry")
        self.bounce_settings_animation.setDuration(200)
        self.bounce_settings_animation.setEasingCurve(QEasingCurve.Type.OutBounce)

        self.reset_timer()
        self.init_tray()
        self.load_fonts()

    def handle_text_input(self, text, field):
        if len(text)<4:
            if len(text)==3:
                field.setStyleSheet("""
                        QLineEdit{
                            border: none;
                            padding: 0px;
                            color: #E6E6E6;
                            font-size: 20px;
                             font-weight: bold;
                            font-family: 'PT Mono';
                            background-color: transparent;
                        }""")
            if len(text)==2:
                field.setStyleSheet("""
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

    def change_first_gradient_color(self):
        self.change_gradient_color(True)

    def change_second_gradient_color(self):
        self.change_gradient_color(False)

    def create_color_button(self, color, handler):
        button = QPushButton()
        button.setFixedSize(120, 70)
        button.setStyleSheet(f"""
            QPushButton{{background-color:{color};border:1px solid {lighten_color_subtract(color, 40)};border-radius:20px;}}
            QPushButton::hover{{border:3px solid {lighten_color_subtract(color, 40)};border-radius:20px;}}
        """)
        button.clicked.connect(handler)
        return button

    def change_gradient_color(self, is_first=True):
        color = ColorPicker()
        color.setFixedSize(420, 330)
        color.move(self.x() - color.width(), self.y() + color.width() // 2)
        current_color = self.first_gradient_color if is_first else self.second_gradient_color
        if hsv_color := color.getColor(hex_to_rgb(current_color)):
            new_color = rgb_to_hex(hsv_color)
            if is_first:
                self.flip_card.set_font_color(new_color)
                self.background_transparent_slider.setStyleSheet(self.set_style_to_slider(new_color))
                self.time_slider.setStyleSheet(self.set_style_to_slider(new_color))

            target_color = 'first_gradient_color' if is_first else 'second_gradient_color'
            setattr(self, target_color, new_color)
            getattr(self.play_button, f'set_{target_color}')(new_color)
            self.update_button_style(getattr(self, f'{target_color}_pick_button'), new_color)
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
            "HYWenHei.ttf"

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
        quit_action = QAction("Закрыть", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

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
            'work_interval': self.work_interval_field.text() if self.work_interval_field.text() != "" else "30",
            'rest_interval': self.rest_interval_field.text() if self.rest_interval_field.text() != "" else "5",
            'music_path': self.audio_player.path_to_music,
            'random': self.audio_player.random,
            'background_color': self.background_color,
            "first_gradient_color": self.first_gradient_color,
            "second_gradient_color": self.second_gradient_color,
            "lock_window": self.lock_window,
            "background_transparency": self.background_transparency
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
                self.audio_player.stop_music(15000)
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
            if self.work_interval_field.text().isdigit() and int(self.work_interval_field.text()) > 0 and int(
                    self.work_interval_field.text()) < 99:
                new_work_interval = int(self.work_interval_field.text()) * 60
                if self.work_interval != new_work_interval:
                    self.work_interval = new_work_interval
                    self.time_slider.setRange(0, self.work_interval - 8)
                    self.time_slider.setValue(self.work_interval - self.remaining_time)

        if self.is_rest_period:
            if self.rest_interval_field.text().isdigit() and int(self.rest_interval_field.text()) > 0 and int(
                    self.rest_interval_field.text()) < 99:
                new_rest_interval = int(self.rest_interval_field.text()) * 60
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
        painter.drawRoundedRect(40, 40, self.root_container.width() + 20, self.root_container.height() + 20, 69, 69)

        self.update()

    # СРАБАТЫВАЕТ ПРИ НАЖАТИИ
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()
            if not self.settings_closed:
                self.initial_pos = event.pos()
                if self.initial_pos.y() > 650:
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
                    if new_height > self.original_height+50:
                        new_height = self.original_height+50
                    # Обновляем геометрию изображения
                    self.root_container.setGeometry(
                        self.root_container.x(),
                        self.root_container.y(),
                        self.root_container.width(),
                        new_height
                    )
                    self.update()
                    if self.original_height+50 >=new_height>self.original_height+45:
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
                        self.bounce_settings_animation.setStartValue(QRect(50, 50, 300, self.root_container.height()))
                        self.bounce_settings_animation.setEndValue(QRect(50, 50, 300, self.original_height))
                        self.bounce_settings_animation.start()
            self.close_setting_touch_area = False
            self.closing = False
            self.x_value = self.pos().x()
            self.y_value = self.pos().y()
            self.save_settings()
            self.drag_pos = None
            self.initial_pos = None

    def initInputField(self, value):
        input_field = QLineEdit()
        input_field.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        input_field.setFixedSize(40, 40)
        input_field.setText(str(int(value / 60)))
        input_field.setStyleSheet("""
                        QLineEdit{
                            border: none;
                            padding: 0px;
                            color: #E6E6E6;
                            font-size: 25px;
                             font-weight: bold;
                            font-family: 'PT Mono';
                            background-color: transparent;
                        }""")
        return input_field

    def init_slider(self, function):
        slider = QSlider(Qt.Horizontal)
        slider.setFixedSize(250, 20)
        slider.setStyleSheet(self.set_style_to_slider(self.first_gradient_color))

        slider.valueChanged.connect(function)
        return slider

    def set_style_to_slider(self, color):
        return f"""
        QSlider::groove:horizontal {{
            height: 6px;
            background-color: transparent;
            border-radius: 5px;
            border:2px solid {color};
        }}

        QSlider::handle:horizontal {{
            width: 10px;
            height: 40px;
            margin: -5px 0;
            background-color:#2E2E2E;
            border: 2px solid {color};
            border-radius: 5px;
        }}

        QSlider::sub-page:horizontal {{
            background-color: {color};
            border-radius: 5px;
            border:2px solid {color};
        }}
        """


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    check_settings()
    version = "2.0.0"
    window = ClockWindow(version)
    window.show()
    app.exec()
