import math
import sys
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QTransform
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSlider,
                             QApplication, QMainWindow)

from python.clock.components.g import SimpleGraph


class FlipCard(QWidget):
    def __init__(self, front_items, back_items, label, parent=None):
        super().__init__(parent)
        self.start_angle = None
        self.press = False
        self.drag_pos = None
        self.label = label
        self.is_flipped = False

        self.card_width = 300
        self.card_height = 450


        self.front_items = front_items
        self.back_items = back_items
        self.rotation_angle = 0

        self.setFixedSize(self.card_width, self.card_height+80)
        self.setup_ui()

        self.bounce_timer = QTimer()
        self.bounce_timer.timeout.connect(self.update_rotation_angle)
        self.bounce_values = []
        self.bounce_pointer=0

    def mousePressEvent(self, event):
        self.press = True
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.pos()
            self.start_angle = self.rotation_angle  # Сохраняем начальный угол
        self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.drag_pos is not None:
                delta_x = event.pos().x() - self.drag_pos.x()
                # Вычисляем новый угол относительно начального
                self.rotation_angle = self.start_angle - delta_x
                self.update()

    def mouseReleaseEvent(self, event):
        if self.press:
            self.press = False
            self.drag_pos = None

            if event.button() == Qt.LeftButton:
                normalized_angle = self.rotation_angle % 360
                if 0 <= normalized_angle <= 90 or normalized_angle >= 270:
                    self.rotation_angle = round(self.rotation_angle / 360) * 360
                elif 90 < normalized_angle < 270:
                    self.rotation_angle = round(self.rotation_angle / 360) * 360 + 180
                self.bounce_values = self.get_bounce_values()
                self.draw_graph(list(range(1, len(self.bounce_values)+1)), self.bounce_values)

                self.bounce_timer.start(5)
            self.update()
            super().mouseReleaseEvent(event)

    def draw_graph(self, x, y):
        self.graph = QMainWindow()
        self.graph.setGeometry(2500, 400, 600, 400)
        # Создаем виджет для построения графика
        self.plot_graph = pg.PlotWidget()
        # Устанавливаем белый фон
        self.plot_graph.setBackground("w")
        x_axis = self.plot_graph.getAxis('bottom')
        y_axis = self.plot_graph.getAxis('left')

        # Устанавливаем черный цвет для линий сетки
        x_axis.setGrid(255)  # 255 соответствует черному цвету в HEX #000000
        y_axis.setGrid(255)
        # Создаем красную линию толщиной 2 пикселя
        pen = pg.mkPen(color=(255, 0, 0), width=2)
        # Рисуем график
        self.plot_graph.plot(x, y, pen=pen)
        self.graph.setCentralWidget(self.plot_graph)
        self.graph.show()

    def get_bounce_values(self, steps=30):
        """
        Плавный bounce-эффект с 5 скачками с убывающей амплитудой
        но одинаковыми пиками внутри каждого скачка
        """
        values = []

        # Амплитуды для каждого из 5 скачков
        amplitudes = [10, 8, 6, 4, 2]

        for i in range(steps):
            t = i / steps
            value = 0

            # Создаем 5 отдельных скачков
            for j, amp in enumerate(amplitudes):
                # Сдвигаем каждый следующий скачок по времени
                phase_shift = j * 0.15  # сдвиг фазы для разделения скачков
                freq_factor = 8 + j * 2  # увеличиваем частоту для более резких скачков

                # Затухающая огибающая для плавности
                envelope = math.exp(-3 * (t - phase_shift)) if t >= phase_shift else 0

                # Синусоида для скачка
                bounce = amp * math.sin(freq_factor * math.pi * (t - phase_shift)) * envelope
                value += bounce

            values.append(round(value, 3))

        return values

    def setup_ui(self):
        # Основной layout для карточки
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)

        # Контейнер для контента (будет вращаться)
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
                            background-color: #333333;
                       """)
        self.content_widget.setFixedSize(self.card_width, 600)

        # Front side (лицевая сторона)
        self.front_widget = self.create_side_widget(self.front_items, "Лицевая сторона", "#E3F2FD")
        self.front_widget.setParent(self.content_widget)

        # Back side (обратная сторона)
        self.back_widget = self.create_side_widget(self.back_items, "Обратная сторона", "#FFF3E0")
        self.back_widget.setParent(self.content_widget)

    def update_rotation_angle(self):

        if self.bounce_pointer>=len(self.bounce_values):
            self.bounce_timer.stop()
            self.bounce_pointer = 0

        else:
            self.rotation_angle = self.rotation_angle + self.bounce_values[self.bounce_pointer]
            self.bounce_pointer+=1

        self.update()


    def create_side_widget(self, items, title, color):
        widget = QWidget()
        widget.setGeometry(0, 40, self.card_width, 450)
        widget.setStyleSheet(f"""
            background-color: {color}; 
            border-radius: 15px; 
            border: 2px solid #000000;
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок стороны
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #2E2E2E; margin-bottom: 20px;")
        layout.addWidget(title_label)

        # Список пунктов
        for i, item in enumerate(items, 1):
            item_label = QLabel(f"{i}. {item}")
            item_label.setFont(QFont("Arial", 12))
            item_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(255,255,255,0.7);
                    border: 1px solid #DDD;
                    border-radius: 8px;
                    padding: 10px;
                    margin: 4px;
                }
            """)
            item_label.setMinimumHeight(35)
            item_label.setWordWrap(True)
            layout.addWidget(item_label)

        layout.addStretch()
        return widget

    def set_rotation(self, angle):
        """Устанавливает угол вращения (0-360 градусов)"""
        self.rotation_angle = angle
        self.update()  # Перерисовываем

    def paintEvent(self, event):
        painter = QPainter(self)

        # Нормализуем угол в диапазон 0-360 градусов
        self.normalized_angle = self.rotation_angle % 360

        # Применяем трансформацию вращения вокруг оси Y
        transform = QTransform()
        transform.translate(self.width() / 2, self.height() / 2)
        transform.rotate(self.normalized_angle, Qt.YAxis)

        # Определяем, какая сторона видна (используем self.normalized_angle)
        # Если угол между 90° и 270° - показываем обратную сторону
        if 90 < self.normalized_angle < 270:
            transform.scale(-1, 1)  # Отражение по вертикали
            self.front_widget.hide()
            self.back_widget.show()
        else:
            self.front_widget.show()
            self.back_widget.hide()

        transform.translate(-self.width() / 2, -self.height() / 2)
        painter.setTransform(transform)

        # Отрисовываем контент
        self.content_widget.render(painter, self.content_widget.pos())
        self.label.setText(f"Угол вращения: {int(self.rotation_angle)}° (норм: {int(self.normalized_angle)}°)")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.X11BypassWindowManagerHint)
        self.setGeometry(1900, 400, 400, 780)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)

        # Данные для сторон
        front_items = [
            "История воспроизведения треков",
            "Текущий плейлист",
            "Настройки звука",
            "Статистика прослушивания",
            "Избранные композиции"
        ]

        back_items = [
            "Громкость: 75%",
            "Повтор: Вкл",
            "Случайный порядок: Выкл",
            "Эквалайзер: Поп",
            "Автопауза: 30 мин",
            "Качество: Высокое"
        ]

        # Слайдер для управления вращением
        slider_layout = QVBoxLayout()

        slider_label = QLabel("Угол вращения: 0°")
        slider_label.setAlignment(Qt.AlignCenter)
        slider_label.setFont(QFont("Arial", 12, QFont.Bold))
        slider_layout.addWidget(slider_label)

        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(0)
        self.rotation_slider.setTickPosition(QSlider.TicksBelow)
        self.rotation_slider.setTickInterval(45)
        self.rotation_slider.valueChanged.connect(lambda value: (
            self.flip_card.set_rotation(value),
            slider_label.setText(f"Угол вращения: {value}°")
        ))
        slider_layout.addWidget(self.rotation_slider)

        # Создаем карточку
        self.flip_card = FlipCard(front_items, back_items, slider_label)
        layout.addWidget(self.flip_card)

        layout.addLayout(slider_layout)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
