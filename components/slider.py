from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSlider

from components.hint_window import HintWidget


class Slider(QSlider):
    def __init__(self, root_window, hint_text, color):
        super().__init__(Qt.Horizontal)
        self.hint_text = hint_text
        self.root_window = root_window
        self.setFixedSize(250, 20)
        self.set_color(color)

    def set_color(self, color):
        self.setStyleSheet(f"""
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
                """)


    def enterEvent(self, e):
        self.hint = HintWidget(self.root_window, self.hint_text)
        self.hint.show()

    def leaveEvent(self, e):
        self.hint.close()
