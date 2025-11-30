from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout
from vcolorpicker import ColorPicker

from components.utils import hex_to_rgb, rgb_to_hex, lighten_color_subtract


class ColorSettingsWidget(QWidget):
    on_color_change = pyqtSignal(str, str)

    def __init__(self, color_scheme_button, root_window, first_color, second_color):
        super().__init__(root_window)
        self.root_window = root_window
        self.setGeometry(
            (self.mapToGlobal(color_scheme_button.pos()) - root_window.frameGeometry().topLeft()).x()+50,
            color_scheme_button.pos().y() + 170,
            170,
            250)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
                                       QWidget{
                                      background-color: #4D4D4D;
                                       border: 2px solid #1A1A1A;
                                      border-radius: 20px;
                                      }
                                      """)
        third_settings_vbox = QVBoxLayout(self)
        third_settings_vbox.setAlignment(Qt.AlignCenter)
        third_settings_vbox.setSpacing(3)

        self.first_color = first_color
        self.second_color = second_color

        print()

        # КНОПКА НАСТРОЙКИ ПЕРВОГО ЦВЕТА
        self.first_gradient_color_pick_button = self.create_color_button("Первый цвет", self.first_color,
                                                                         self.change_first_gradient_color)
        third_settings_vbox.addWidget(self.first_gradient_color_pick_button)
        # КНОПКА НАСТРОЙКИ ВТОРОГО ЦВЕТА
        self.second_gradient_color_pick_button = self.create_color_button("Второй цвет", self.second_color,
                                                                          self.change_second_gradient_color)
        third_settings_vbox.addWidget(self.second_gradient_color_pick_button)

        submit_button = QPushButton("Установить")
        submit_button.setFixedSize(120, 30)
        submit_button.setStyleSheet("""
                       QPushButton{
                                font-weight: light;
                                font-size: 14px;
                                font-family: 'PT Mono';
                                color: white;
                                background-color: transparent;
                                border: 2px solid #1A1A1A;
                                border-radius: 15px;}
                       QPushButton::hover{ background-color: #90333333;
                                       border: 2px solid #1A1A1A;
                                      border-radius:15px;}
                   """)
        submit_button.clicked.connect(self.on_close_handler)
        third_settings_vbox.addWidget(submit_button)

    def on_close_handler(self):
        self.on_color_change.emit(self.first_color, self.second_color)
        self.close()

    def create_color_button(self, text, color, handler):
        button = QPushButton(text)
        button.setFixedSize(120, 70)
        button.setStyleSheet(self.create_stylesheet(color))
        button.clicked.connect(handler)
        return button

    def create_stylesheet(self, color):
        return f"""
               QPushButton{{background-color:{color};border:2px solid {lighten_color_subtract(color, 40)};border-radius:20px;}}
               QPushButton::hover{{border:3px solid {lighten_color_subtract(color, 40)};border-radius:20px;}}
           """

    def change_first_gradient_color(self):
        self.change_gradient_color(True)

    def change_second_gradient_color(self):
        self.change_gradient_color(False)

    def change_gradient_color(self, is_first=True):
        color = ColorPicker()
        color.setFixedSize(420, 330)
        color.move(self.root_window.x() - color.width(), self.root_window.y() + color.width() // 2)
        current_color = self.first_color if is_first else self.second_color
        if hsv_color := color.getColor(hex_to_rgb(current_color)):
            new_color = rgb_to_hex(hsv_color)
            if is_first:
                self.first_color = new_color
                self.first_gradient_color_pick_button.setStyleSheet(self.create_stylesheet(new_color))
            else:
                self.second_color = new_color
                self.second_gradient_color_pick_button.setStyleSheet(self.create_stylesheet(new_color))
