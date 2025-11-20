from PyQt5.QtWidgets import QCheckBox


class Checkbox(QCheckBox):
    def __init__(self):
        super().__init__()
        self.setFixedSize(28, 28)
        self.setStyleSheet("""
                    QCheckBox {
                        background-color: transparent;
                        border: 2px solid #808080;
                        border-radius: 14px;
                        padding-left: 6px; 
                    }
                    QCheckBox::hover {
                        cursor: pointer;
                    }

                    QCheckBox::indicator {
                        background-color:  transparent;
                        
                    }
                    QCheckBox::indicator:checked {
                        background-color:  #808080;
                        border-radius: 6px;
                        width: 12px;
                        height: 12px;
                    }
                """)