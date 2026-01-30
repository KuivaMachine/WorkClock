from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt5.QtWidgets import QWidget

from components.flip_window import MarqueeLabel
from components.hint_window import HintWidget


class PickMusicFolderButton(QWidget):
    clicked = pyqtSignal()
    delete_clicked = pyqtSignal()

    def __init__(self, root_window, text):
        super().__init__()
        self.close_btn_hover = False
        self.hover = False
        self.root_window = root_window
        self.setFixedSize(250, 40)
        self.setMouseTracking(True)

        self.text = MarqueeLabel(text)
        self.text.setMouseTracking(True)
        self.text.setGeometry(15,0,200,40)
        self.text.setParent(self)
        self.text.setStyleSheet("""
                                 QLabel{
                                    color: #ffffff;
                                    font-weight: 400;
                                    font-size: 16px;
                                    border: none;
                                    background-color: transparent;
                                }
                        """)

    def setText(self, text):
        self.text.setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if 210 < event.pos().x() < 240 and 1 < event.pos().y() < 39:
                self.text.setText("")
                self.delete_clicked.emit()
            else:
                self.clicked.emit()

    def mouseMoveEvent(self, event):
        if 210 < event.pos().x() < 240 and 1 < event.pos().y() < 39:
            self.close_btn_hover = True
            self.hover = False
        else:
            self.hover = True
            self.close_btn_hover = False


    def enterEvent(self, e):
        self.hint = HintWidget(self.root_window, "Папка с музыкой")
        self.hint.show()

    def leaveEvent(self, e):
        self.hint.close()
        self.hover = False
        self.close_btn_hover = False

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 120 if self.hover else 90)))
        painter.drawRoundedRect(1, 1, 248, 38, 20, 20)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 250 if self.close_btn_hover else 60)))
        painter.drawEllipse(210, 2, 36, 36)

        font = QFont("Comic Sans", 12)
        painter.setFont(font)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawText(QRect(210, 0, 36, 36) ,Qt.AlignCenter, 'x')