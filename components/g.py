from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt
import math


class SimpleGraph(QWidget):
    def __init__(self, y_values, width=400, height=300, parent=None):
        super().__init__(parent)
        self.y_values = y_values
        self.x_values = list(range(1, len(y_values) + 1))
        self.setFixedSize(width, height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Настройки отступов
        margin = 40
        graph_width = self.width() - 2 * margin
        graph_height = self.height() - 2 * margin

        # Рисуем фон
        self.draw_background(painter, margin, graph_width, graph_height)

        # Рисуем оси
        self.draw_axes(painter, margin, graph_width, graph_height)

        # Рисуем график
        self.draw_graph(painter, margin, graph_width, graph_height)

        # Рисуем заголовок и подписи
        self.draw_labels(painter, margin, graph_width, graph_height)

    def draw_background(self, painter, margin, graph_width, graph_height):
        # Фон графика
        painter.fillRect(margin, margin, graph_width, graph_height, QColor(250, 250, 250))

        # Сетка
        painter.setPen(QPen(QColor(220, 220, 220), 1))

        # Вертикальные линии сетки
        for i in range(0, 11):
            x = margin + (i * graph_width) // 10
            painter.drawLine(x, margin, x, margin + graph_height)

        # Горизонтальные линии сетки
        for i in range(0, 11):
            y = margin + (i * graph_height) // 10
            painter.drawLine(margin, y, margin + graph_width, y)

    def draw_axes(self, painter, margin, graph_width, graph_height):
        # Оси
        painter.setPen(QPen(QColor(0, 0, 0), 2))

        # Ось X
        painter.drawLine(margin, margin + graph_height, margin + graph_width, margin + graph_height)

        # Ось Y
        painter.drawLine(margin, margin, margin, margin + graph_height)

    def draw_graph(self, painter, margin, graph_width, graph_height):
        if not self.y_values:
            return

        # Находим min и max значения Y для масштабирования
        y_min = min(self.y_values)
        y_max = max(self.y_values)
        y_range = y_max - y_min if y_max != y_min else 1

        # Настройки линии графика
        painter.setPen(QPen(QColor(65, 105, 225), 3))  # Royal Blue

        # Рисуем линии графика
        points = []
        for i, y in enumerate(self.y_values):
            # Масштабируем координаты
            x_coord = margin + (i * graph_width) / (len(self.y_values) - 1)
            y_coord = margin + graph_height - ((y - y_min) * graph_height) / y_range
            points.append((x_coord, y_coord))

        # Рисуем соединительные линии
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

        # Рисуем точки
        painter.setPen(QPen(QColor(30, 144, 255), 6))  # Dodger Blue
        for x, y in points:
            painter.drawPoint(int(x), int(y))

    def draw_labels(self, painter, margin, graph_width, graph_height):
        painter.setPen(QColor(0, 0, 0))
        painter.setFont(QFont("Arial", 9))

        # Подписи оси X
        x_step = max(1, len(self.x_values) // 10)
        for i in range(0, len(self.x_values), x_step):
            x_coord = margin + (i * graph_width) / (len(self.x_values) - 1)
            painter.drawText(int(x_coord - 10), margin + graph_height + 15,
                             str(self.x_values[i]))

        # Подписи оси Y
        y_min = min(self.y_values)
        y_max = max(self.y_values)
        y_range = y_max - y_min if y_max != y_min else 1

        for i in range(0, 11):
            value = y_min + (i * y_range) / 10
            y_coord = margin + graph_height - (i * graph_height) / 10
            painter.drawText(5, int(y_coord + 4), f"{value:.1f}")

        # Заголовок
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        painter.drawText(0, 20, self.width(), 20, Qt.AlignCenter, "График функции")