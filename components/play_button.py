from PyQt5.QtCore import QEasingCurve, QPoint
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QLinearGradient
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtWidgets import QPushButton, QGraphicsDropShadowEffect

from components.utils import load_settings


def calculate_alpha(x):
    """Вычисляет значение прозрачности от 00 до FF в зависимости от позиции x"""
    # Диапазон x: от 15 до 191 (176 единиц)
    min_x = 15
    max_x = 191
    range_x = max_x - min_x
    clamped_x = max(min_x, min(x, max_x))
    progress = (clamped_x - min_x) / range_x
    alpha_hex = format(int(progress * 255), '02X')
    return alpha_hex


class PlayButton(QPushButton):
    next = pyqtSignal()
    back = pyqtSignal()
    left_clicked = pyqtSignal()
    delete_track = pyqtSignal()

    def __init__(self, time, delete_label):
        super().__init__()
        self.settings = load_settings()
        self.first_gradient_color = self.settings['first_gradient_color']
        self.second_gradient_color = self.settings['second_gradient_color']

        self.setFixedSize(90, 90)
        self.setGeometry(11, 11, 90, 90)

        self.next_track = False             # Флаг, указывающий где находится курсор при нажатии правой кнопкой мыши относительно центра
        self.time = time                    # Текст времени для анимации его сдвига при удалении
        self.delete_label = delete_label    # Текст "Удалить"
        self.is_playing = False             # Флаг играет/не играет для установки картинки на кнопку
        self.press = False                  # Флаг нажатия на кнопку
        self.hover = False                  # Флаг наведения мыши на кнопку
        self.is_right_click = False         # Флаг правого клика
        self.drag_pos = None                # Позиция курсора при нажатии
        self.is_deleting = False            # Флаг, указывающий происходит ли процесс удаления
        self.delete = False                 # Флаг, указывающий достиг ли курсор позиции удаления трека
        self.time_pos = None                # Позиция текста времени

        # Тень для контейнера
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.shadow.setOffset(0, 8)
        self.setGraphicsEffect(self.shadow)

        # АНИМАЦИЯ ВОЗВРАЩЕНИЯ
        self.return_animation = QPropertyAnimation(self, b"pos")
        self.return_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.return_animation.setEndValue(self.pos())
        self.return_animation.setDuration(500)

        # АНИМАЦИЯ ВОЗВРАЩЕНИЯ
        self.return_time_animation = QPropertyAnimation(self.time, b"pos")
        self.return_time_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.return_time_animation.setDuration(500)

    def enterEvent(self, a0):
        self.hover = True

    def leaveEvent(self, a0):
        self.hover = False

    def mousePressEvent(self, event):
        self.press = True
        if event.button() == Qt.RightButton:
            self.is_right_click = True
            self.next_track = event.pos().x()>45


        elif event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self.time_pos = self.time.pos()
        self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.drag_pos is not None:
                new_position = event.globalPos() - self.drag_pos
                x = max(11, min(new_position.x(), 191))
                self.move(x, self.y())
                self.time.move(self.time_pos.x(), max(11, min(new_position.x(), 150)))
                self.return_animation.setStartValue(QPoint(x, 11))
                self.return_time_animation.setStartValue(QPoint(self.time_pos.x(), new_position.x()))
                if x > 15:
                    self.is_deleting = True
                    self.delete_label.setGeometry(15, 11, x, 90)
                    self.delete_label.setStyleSheet(f"""QLabel {{
                                                       padding: 0px;
                                                       font-size: 40px;
                                                       font-weight: bold;
                                                       font-family: 'PT Mono';
                                                       color: #{calculate_alpha(x)}FFFFFF;
                                                       background-color: transparent;
                                                   }}
                                                   """)
                if x > 189:
                    self.delete = True
                    self.delete_label.setStyleSheet("""QLabel {padding: 0px;
                                                                           font-size: 40px;
                                                                           font-weight: bold;
                                                                           font-family: 'PT Mono';
                                                                           color: #FFFFFF;
                                                                           background-color: transparent;
                                                                       }
                                                                       """)
                else:
                    self.delete = False

        elif event.buttons() & Qt.MouseButton.RightButton:
            self.next_track = event.pos().x()>45
        super().mouseMoveEvent(event)

    def set_first_gradient_color(self, color):
        self.first_gradient_color = color

    def set_second_gradient_color(self, color):
        self.second_gradient_color = color

    def mouseReleaseEvent(self, event):
        if self.press:
            self.press = False
            self.drag_pos = None

            if self.is_deleting:
                self.return_animation.start()
                self.return_time_animation.setEndValue(self.time_pos)
                self.return_time_animation.start()
                self.is_deleting = False
                self.delete_label.setStyleSheet("""QLabel {
                padding: 0px;
                font-size: 40px;
                font-weight: bold;
                font-family: 'PT Mono';
                color: #00FFFFFF;
                background-color: transparent;
                }
                """)
                if self.delete:
                    self.delete_track.emit()
                    self.delete = False

            elif event.button() == Qt.LeftButton:
                self.left_clicked.emit()
                self.is_playing = not self.is_playing

            elif event.button() == Qt.RightButton:
                if self.next_track:
                    self.next.emit()
                else:
                    self.back.emit()
                self.is_right_click = False

            self.update()
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        painter.setPen(Qt.PenStyle.NoPen)

        if self.hover and not self.press:
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            gradient.setColorAt(0, QColor(self.first_gradient_color))
            gradient.setColorAt(1, QColor(self.second_gradient_color))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(2, 2, self.width() - 5, self.height() - 5)
        elif self.delete:
            gradient.setColorAt(0, QColor("#FF0080"))
            gradient.setColorAt(1, QColor("#4D000E"))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(0, 0, self.width(), self.height())
        elif self.press:
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            gradient.setColorAt(0, QColor("#99"+self.first_gradient_color[1:]))
            gradient.setColorAt(1, QColor("#99"+self.second_gradient_color[1:]))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(2, 2, self.width() - 5, self.height() - 5)
        else:
            gradient.setColorAt(0, QColor(self.first_gradient_color))
            gradient.setColorAt(1, QColor(self.second_gradient_color))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(2, 2, self.width() - 5, self.height() - 5)

        # Иконка
        painter.setPen(QPen(Qt.white, 2))
        painter.setBrush(QBrush(Qt.white))

        center_x = self.width() // 2
        center_y = self.height() // 2

        if self.is_right_click:
            if self.next_track:
                # Иконка "дальше" - двойная стрелка вправо
                arrow_width = 20
                arrow_height = 35
                spacing = 2
                # Первая стрелка
                points1 = [
                    QPoint(center_x - arrow_width - spacing, center_y - arrow_height // 2),
                    QPoint(center_x - spacing, center_y),
                    QPoint(center_x - arrow_width - spacing, center_y + arrow_height // 2)
                ]
                # Вторая стрелка
                points2 = [
                    QPoint(center_x + spacing, center_y - arrow_height // 2),
                    QPoint(center_x + arrow_width + spacing, center_y),
                    QPoint(center_x + spacing, center_y + arrow_height // 2)
                ]
            else:
                # Иконка "назад" - двойная стрелка влево
                arrow_width = 20
                arrow_height = 35
                spacing = 2
                # Первая стрелка
                points1 = [
                    QPoint(center_x + arrow_width + spacing-5, center_y - arrow_height // 2),  # правая верхняя
                    QPoint(center_x + spacing-5, center_y),  # левая (острие)
                    QPoint(center_x + arrow_width + spacing-5, center_y + arrow_height // 2)  # правая нижняя
                ]
                # Вторая стрелка (правая)
                points2 = [
                    QPoint(center_x - spacing-5, center_y - arrow_height // 2),  # левая верхняя
                    QPoint(center_x - arrow_width - spacing-5, center_y),  # правая (острие)
                    QPoint(center_x - spacing-5, center_y + arrow_height // 2)  # левая нижняя
                ]
            painter.drawPolygon(points1)
            painter.drawPolygon(points2)

        elif self.delete:
            # Иконка корзины
            bin_width = 60
            bin_height = 20
            bin_top_width = 28
            bin_bottom_width = 20

            # Корпус корзины (трапеция)
            bin_points = [
                QPoint(center_x - bin_top_width // 2, center_y - bin_height // 2),  # Верхний левый
                QPoint(center_x + bin_top_width // 2, center_y - bin_height // 2),  # Верхний правый
                QPoint(center_x + bin_bottom_width // 2, center_y + bin_height),  # Нижний правый
                QPoint(center_x - bin_bottom_width // 2, center_y + bin_height)  # Нижний левый
            ]

            # Крышка корзины
            cap_y = center_y - bin_height // 2 - 5
            cap_points = [
                QPoint(center_x - 18, cap_y),  # Левая точка ручки
                QPoint(center_x - 18, cap_y - 3),  # Левая верхняя
                QPoint(center_x + 18, cap_y - 3),  # Правая верхняя
                QPoint(center_x + 18, cap_y)  # Правая точка ручки
            ]

            # Ручка корзины
            handle_y = center_y - bin_height // 2 - 9
            handle_points = [
                QPoint(center_x - 5, handle_y),  # Левая точка ручки
                QPoint(center_x - 5, handle_y - 2),  # Левая верхняя
                QPoint(center_x + 5, handle_y - 2),  # Правая верхняя
                QPoint(center_x + 5, handle_y)  # Правая точка ручки
            ]

            # Рисуем корзину
            painter.drawPolygon(bin_points)

            # Рисуем ручку
            painter.drawPolygon(handle_points)

            # Рисуем крышку
            painter.drawPolygon(cap_points)


        elif self.is_playing:
            # Иконка паузы - два прямоугольника
            rect_width = 8
            rect_height = 35
            spacing = 5

            # Левый прямоугольник
            painter.drawRect(center_x - spacing - rect_width, center_y - rect_height // 2,
                             rect_width, rect_height)
            # Правый прямоугольник
            painter.drawRect(center_x + spacing, center_y - rect_height // 2,
                             rect_width, rect_height)
        else:
            # Иконка play - треугольник
            triangle_size = 40
            points = [
                QPoint(center_x - triangle_size // 3, center_y - triangle_size // 2),
                QPoint(center_x - triangle_size // 3, center_y + triangle_size // 2),
                QPoint(center_x + triangle_size // 2, center_y)
            ]
            painter.drawPolygon(points)