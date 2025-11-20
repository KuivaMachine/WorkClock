from PyQt5.QtWidgets import QPushButton


class ServiceButton(QPushButton):
    def __init__(self, text, width):
        super().__init__()
        self.setFixedSize(width, 30)
        self.setText(text)
        self.setStyleSheet("""
        QPushButton {
            font-size: 18px;
            font-weight: light;
            font-family: 'PT Mono';
            color: #CCCCCC;
            background-color: #4D4D4D;
            border-radius: 15px;
            padding: 3px;
        }
        QPushButton:hover{
            border:1px solid #808080;
        }
        QPushButton:pressed{
            color: #CCCCCC;
            background-color: #333333;
            border:1px solid #808080;
        }
        """)