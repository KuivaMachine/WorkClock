from pathlib import Path

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QWidget, QLineEdit, QHBoxLayout

from components.hint_window import HintWidget


class IntervalInputWidget(QWidget):
    textChanged = pyqtSignal(str)
    def __init__(self,root_window, init_value,  hint_text, icon):
        super().__init__()
        self.hint_text = hint_text
        self.root_window = root_window
        self.setAttribute(Qt.WA_StyledBackground, True)
        app_directory = Path(__file__).parent.parent  # Ищет родительский каталог проекта
        resource_path = app_directory / 'resources'
        self.setFixedSize(120, 70)
        self.setStyleSheet("""
                                               QWidget{
                                              background-color: transparent;
                                              border: 1px solid #808080;
                                                border-radius: 20px;
                                                 padding: 0px 20px;
                                              }
                                               QWidget::hover{
                                       background-color: rgba(20, 20, 20, 0.1);
                                      border: 2px solid #808080;
                                      border-radius: 20px;
                                       }
                                              """)
        work_interval_icon = QSvgWidget(str(resource_path / icon))
        work_interval_icon.setStyleSheet("""
                background-color: transparent;
                border: none;
                """)
        work_interval_icon.setFixedSize(50, 50)



        self.interval_field = QLineEdit()
        self.interval_field.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.interval_field.setFixedSize(40, 40)
        self.interval_field.setText(str(int(init_value / 60)))
        self.interval_field.setStyleSheet("""
                                QLineEdit{
                                    border: none;
                                    padding: 0px;
                                    color: #E6E6E6;
                                    font-size: 25px;
                                     font-weight: bold;
                                    font-family: 'PT Mono';
                                    background-color: transparent;
                                }""")

        self.interval_field.textChanged.connect(self.textChanged.emit)

        interval_hbox = QHBoxLayout(self)
        interval_hbox.setSpacing(0)
        interval_hbox.addWidget(self.interval_field)
        interval_hbox.addWidget(work_interval_icon)

    def setStyle(self, style):
        self.interval_field.setStyleSheet(style)

    def setText(self, text):
        self.interval_field.setText(text)

    def text(self):
        return self.interval_field.text()

    def enterEvent(self, e):
        self.hint = HintWidget(self.root_window, self.hint_text)
        self.hint.show()

    def leaveEvent(self, e):
        self.hint.close()


