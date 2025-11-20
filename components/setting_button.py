from PyQt5.QtWidgets import QPushButton


class SettingsButton(QPushButton):
    def __init__(self, text, width):
        super().__init__()
        self.setFixedSize(width, 40)
        self.setText(text)
        self.setStyleSheet("""
        QPushButton {
         border: 2px dashed #808080;
         text-align: left;
         border-radius: 20px;
         padding: 0px 20px;
         color: #E6E6E6;
         font-size: 20px;
         background-color: transparent;
        }
        """)