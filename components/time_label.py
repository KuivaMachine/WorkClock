from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel
import itertools

class TimeLabel(QLabel):
    fontChanged = pyqtSignal()
    def __init__(self, time_font):
        super().__init__()
        self.setFixedSize(150,50)
        self.time_font = time_font
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
                        QLabel {
                            padding: 0px;
                            color: #FFFFFF;
                            background-color: transparent;
                        }
                        """)
        font = QFont(time_font, 25)
        font.setBold(True)
        self.setFont(font)
        self.font_list=[
            "PT Mono",
            "HYWenHei",
            "Stengazeta",
            "Ringus-Regular"
        ]
        self.font_cycle = itertools.cycle(self.font_list)
        current_font = next(self.font_cycle)
        while current_font != time_font:
            current_font = next(self.font_cycle)

    def get_time_font(self):
        return self.time_font

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            next_font = next(self.font_cycle)
            font = QFont(next_font, 25)
            font.setBold(True)
            self.setFont(font)
            self.time_font = next_font
            self.fontChanged.emit()
        super().mousePressEvent(event)