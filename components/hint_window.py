from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel


class HintWidget(QLabel):
    def __init__(self, parent, text):
        super().__init__(parent)

        self.setGeometry(15, 570, 300, 95)
        self.setAlignment(Qt.AlignCenter)
        self.setText( text)
        self.setStyleSheet("""
                                QLabel{
                                text-align:center;
                                background-color: transparent;
                                font-size:22px;
                                font-family: 'Stengazeta';
                                color: #E6E6E6;
                                }""")







