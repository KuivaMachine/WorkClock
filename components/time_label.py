from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel
import itertools

class TimeLabel(QLabel):
    fontChanged = pyqtSignal()
    def __init__(self, time_font):
        super().__init__()
        self.setFixedSize(170,70)
        self.time_font = time_font
        self.setAlignment(Qt.AlignCenter)
        self.set_background_transparency(0.5)


        # Словарь с оптимальными размерами шрифтов для разного количества символов
        self.font_sizes = {
            "PT Mono": {5: 25, 6: 21},
            "HYWenHei": {5: 22, 6: 20},
            "Stengazeta": {5: 28, 6: 28},
            "Ringus-Regular": {5: 24, 6: 22}
        }

        self.font_list = list(self.font_sizes.keys())
        self.font_cycle = itertools.cycle(self.font_list)

        # Синхронизируем цикл с текущим шрифтом
        current_font = next(self.font_cycle)
        while current_font != time_font:
            current_font = next(self.font_cycle)

    def setText(self, text):
        super().setText(text)
        # Устанавливаем шрифт
        font = QFont(self.time_font, self.font_sizes[self.time_font][len(text)])
        font.setBold(True)
        self.setFont(font)

    def set_background_transparency(self, value):
        """Значение должно быть от 0.0 до 1.0"""
        self.setStyleSheet(f"""
                                QLabel {{
                                    padding: 10px 20px;
                                    color: #FFFFFF;
                                    border-radius: 35px;
                                    background-color: rgba(0, 0, 0, {value});
                                }}
                                """)

    def get_time_font(self):
        return self.time_font

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            next_font = next(self.font_cycle)
            self.time_font = next_font
            font = QFont(self.time_font, self.font_sizes[self.time_font][len(self.text())])
            font.setBold(True)
            self.setFont(font)
            self.fontChanged.emit()
        super().mousePressEvent(event)