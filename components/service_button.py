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
            background-color: transparent;
            border: 1px solid #808080;
            border-radius: 15px;
            padding: 3px;
        }
        QPushButton:hover{
            background-color: rgba(20, 20, 20, 0.1);
            border: 2px solid #808080;
        }
        QPushButton:pressed{
            background-color: rgba(20, 20, 20, 0.4);
            border:2px solid #808080;
        }
        """)
