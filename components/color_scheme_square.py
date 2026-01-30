from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QPen
from PyQt5.QtWidgets import QWidget
from vcolorpicker import ColorPicker

from components.utils import hex_to_rgb, rgb_to_hex


class ColorSchemeSquare(QWidget):
    clicked = pyqtSignal(int, str, str)

    def __init__(self, root_container, number, first_color, second_color):
        super().__init__()
        self.my_number = number
        self.root_window=root_container
        self.hover = False
        self.is_current = False
        self.setStyleSheet("""
                                QWidget{
                               background-color: #FFFFFF;
                               border: none;
                                padding: 0px;
                               }
                               """)

        self.setFixedSize(46, 46)
        self.first_color = first_color
        self.second_color = second_color


    def get_is_current(self):
        return self.is_current

    def set_is_current(self, is_current):
        self.is_current = is_current

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.my_number, self.first_color, self.second_color)
            self.is_current = True
        elif event.button() == Qt.RightButton:
            x =event.x()
            y= event.y()
            size = self.width()
            if 0 <= x < size and 0 <= y < size:
                if x + y < size:
                    # верхний треугольник
                    self.change_gradient_color(True)
                else:
                    # нижний треугольник
                    self.change_gradient_color(False)
        super().mouseReleaseEvent(event)


    def change_gradient_color(self, is_first=True):
        color = ColorPicker()
        color.setFixedSize(420, 330)
        color.move(self.root_window.x() - color.width(), self.root_window.y() + color.width() // 2)
        current_color = self.first_color if is_first else self.second_color
        if hsv_color := color.getColor(hex_to_rgb(current_color)):
            new_color = rgb_to_hex(hsv_color)
            if is_first:
                self.first_color = new_color
            else:
                self.second_color = new_color
            self.clicked.emit(self.my_number, self.first_color, self.second_color)
            self.update()


    def enterEvent(self, e):
        if not self.hover:
            self.hover = True
            self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        if self.hover:
            self.hover = False
            self.update()
        super().leaveEvent(e)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Параметры квадрата
        square_size = 40
        corner_radius = 10
        x = (self.width() - square_size) // 2
        y = (self.height() - square_size) // 2
        border_width = 4 if self.hover else 3
        # Создаем скругленный квадрат
        square_path = QPainterPath()
        square_path.addRoundedRect(x, y, square_size, square_size, corner_radius, corner_radius)
        # Угловые точки
        top_left = (x, y)
        top_right = (x + square_size, y)
        bottom_left = (x, y + square_size)
        bottom_right = (x + square_size, y + square_size)

        # Левый нижний треугольник (зеленый)
        triangle1_path = QPainterPath()
        triangle1_path.moveTo(*top_right)
        triangle1_path.lineTo(*top_left)
        triangle1_path.lineTo(*bottom_left)
        triangle1_path.closeSubpath()

        # Правый верхний треугольник (оранжевый)
        triangle2_path = QPainterPath()
        triangle2_path.moveTo(*bottom_right)
        triangle2_path.lineTo(*bottom_left)
        triangle2_path.lineTo(*top_right)
        triangle2_path.closeSubpath()

        # Обрезаем по форме квадрата и заливаем треугольники
        painter.setClipPath(square_path)
        painter.fillPath(triangle1_path, QColor(self.first_color))  # Зеленый
        painter.fillPath(triangle2_path, QColor(self.second_color))  # Оранжевый
        painter.setClipping(False)

        # Черная обводка
        pen = QPen(QColor("#000000" if not self.is_current else "#FFFFFF"))
        pen.setWidth(border_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(x, y, square_size, square_size, corner_radius, corner_radius)

        # Диагональная линия
        painter.drawLine(x + 3, y + square_size - 3, x + square_size - 4, y + 5)
