from pathlib import Path

from PyQt5.QtCore import pyqtSignal, Qt

from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import QCheckBox, QWidget, QHBoxLayout


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

class CheckboxWidget(QWidget):
    stateChanged = pyqtSignal(bool)
    def __init__(self, icon, checked):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        app_directory = Path(__file__).parent.parent  # Ищет родительский каталог проекта
        resource_path = app_directory / 'resources'
        self.setFixedSize(120, 70)
        self.setStyleSheet("""
                                  QWidget{
                                       background-color: transparent;
                                      border: 1px solid #808080;
                                      border-radius: 20px;
                                       }
                                        QWidget::hover{
                                       background-color: rgba(20, 20, 20, 0.1);
                                      border: 2px solid #808080;
                                      border-radius: 20px;
                                       }
                                """)

        lock_window_hbox = QHBoxLayout(self)
        self.lock_window_checkbox = Checkbox()
        self.lock_window_checkbox.setChecked(checked)
        self.lock_window_checkbox.stateChanged.connect(self.stateChanged.emit)
        lock_window_icon = QSvgWidget(str(resource_path / icon))
        lock_window_icon.setStyleSheet("""
                background-color: transparent;
                border:none;
                """)
        lock_window_icon.setFixedSize(50, 50)
        lock_window_hbox.addWidget(self.lock_window_checkbox)
        lock_window_hbox.addWidget(lock_window_icon)
        lock_window_hbox.setSpacing(5)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.lock_window_checkbox.setChecked(not self.lock_window_checkbox.isChecked())
        super().mousePressEvent(event)
