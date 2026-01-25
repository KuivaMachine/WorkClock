import math

from PyQt5.QtCore import QEasingCurve, QPoint, QTimer, QRect, QRectF, QPointF
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QLinearGradient
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
from PyQt5.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from pkg_resources import safe_extra

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


def checkIsMouseInButton(event):
    button_area_x = 20
    button_area_y = 95
    return button_area_x < event.x() < button_area_y and button_area_x < event.y() < button_area_y


class PlayButton(QPushButton):
    next = pyqtSignal()
    back = pyqtSignal()
    left_clicked = pyqtSignal()
    delete_track = pyqtSignal()
    volume_change = pyqtSignal(int)

    def __init__(self, volume, time, delete_label):
        super().__init__()
        self.settings = load_settings()
        self.first_gradient_color = self.settings['first_gradient_color']
        self.second_gradient_color = self.settings['second_gradient_color']
        self.setFixedSize(120, 120)

        self.next_track = False  # Флаг, указывающий где находится курсор при нажатии правой кнопкой мыши относительно центра
        self.time = time  # Текст времени для анимации его сдвига при удалении
        self.delete_label = delete_label  # Текст "Удалить"
        self.is_playing = False  # Флаг играет/не играет для установки картинки на кнопку
        self.press = False  # Флаг нажатия на кнопку
        self.hover = False  # Флаг наведения мыши на кнопку
        self.is_right_click = False  # Флаг правого клика
        self.drag_pos = None  # Позиция курсора при нажатии
        self.is_deleting = False  # Флаг, указывающий происходит ли процесс удаления
        self.delete = False  # Флаг, указывающий достиг ли курсор позиции удаления трека
        self.time_pos = None  # Позиция текста времени

        # Тень для кнопки
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

        # ПАРАМЕТРЫ СЛАЙДЕРА ГРОМКОСТИ
        self.min_value = 0
        self.max_value = 100
        self.current_volume = volume
        self.track_width = 6
        self.handle_radius = 6
        self.setMouseTracking(True)
        self.is_volume_changing = False

    def getVolume(self):
        return self.current_volume

    def mousePressEvent(self, event):
        if checkIsMouseInButton(event):
            self.press = True
            if event.button() == Qt.RightButton:
                self.is_right_click = True
                self.next_track = event.pos().x() > 45

            elif event.button() == Qt.LeftButton:
                self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                self.time_pos = self.time.pos()
            self.update()
        else:
            self.is_volume_changing = True
            self.update_volume_value(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if checkIsMouseInButton(event):
            self.hover = True
        else:
            self.hover = False

        if event.buttons() & Qt.MouseButton.LeftButton:
            self.update_volume_value(event.pos())
            if self.drag_pos is not None:
                new_position = event.globalPos() - self.drag_pos
                x = max(0, min(new_position.x(), 175))
                self.move(x, self.y())
                self.time.move(self.time_pos.x(), max(0, min(new_position.x(), 150)))
                self.return_animation.setStartValue(QPoint(x, self.pos().y()))
                self.return_time_animation.setStartValue(QPoint(self.time_pos.x(), new_position.x()))
                if x > 2:
                    self.is_volume_changing = False
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
                if x > 145:
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
            self.next_track = event.pos().x() > 45

        super().mouseMoveEvent(event)

    def set_first_gradient_color(self, color):
        self.first_gradient_color = color

    def set_second_gradient_color(self, color):
        self.second_gradient_color = color

    def mouseReleaseEvent(self, event):
        self.is_volume_changing = False
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

    def setVolume(self, value):
        """Установить громкость"""
        if value < self.min_value:
            value = self.min_value
        elif value > self.max_value:
            value = self.max_value
        self.current_volume = value
        self.update()

    def wheelEvent(self, event):
        """Обработка колеса мыши - изменение громкости"""
        delta = event.angleDelta().y()
        self.current_volume += 2 if delta > 0 else -2
        self.current_volume = max(self.min_value, min(self.max_value, self.current_volume))
        self.volume_change.emit(self.current_volume)

    def update_volume_value(self, mouse_pos):
        """Обновляет значение слайдера на основе позиции мыши"""
        if self.is_volume_changing:
            width = self.width()
            height = self.height()

            center_x = width // 2
            center_y = height // 2

            # Вычисляем вектор от центра к курсору
            dx = center_x - mouse_pos.x()
            dy = mouse_pos.y() - center_y

            # Вычисляем угол в радианах
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)

            # Нормализуем угол от 0 до 360
            if angle_deg < 0:
                angle_deg += 360

            # Преобразуем угол в значение слайдера
            start_angle = 90
            end_angle = 270

            # Ограничиваем угол пределами слайдера
            if angle_deg < start_angle:
                angle_deg = start_angle
            elif angle_deg > end_angle:
                angle_deg = end_angle

            # Преобразуем угол в значение
            angle_range = end_angle - start_angle
            normalized_angle = (angle_deg - start_angle) / angle_range

            # Обновляем значение
            new_value = self.min_value + normalized_angle * (self.max_value - self.min_value)
            self.current_volume = int(new_value)
            self.volume_change.emit(self.current_volume)

    def paintEvent(self, event):
        painter = QPainter(self)

        # # 1. Рисуем фон
        # painter.setBrush(QColor(0, 0, 0))
        # painter.setPen(Qt.NoPen)
        # painter.drawRect(self.rect())

        button_size = 92

        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, button_size, button_size)
        painter.setPen(Qt.PenStyle.NoPen)

        if not self.is_deleting:
            # Размеры для отрисовки
            width = self.width()
            height = self.height()

            # Центр и радиус дуги
            center_x = width // 2
            center_y = height // 2
            radius = min(center_x, center_y) - 8

            # Углы: от 12 часов (90°) до 6 часов (270°)
            start_angle = 270
            end_angle = 90

            # Вычисляем текущий угол в зависимости от значения
            angle_range = end_angle - start_angle
            current_angle = start_angle + (self.current_volume / (self.max_value - self.min_value)) * angle_range

            # 2. Рисуем пустой трек (дуга)
            pen = QPen(QColor("#29" + self.first_gradient_color[1:]), self.track_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            # Координаты для дуги
            arc_rect = QRectF(
                center_x - radius,
                center_y - radius,
                radius * 2,
                radius * 2
            )

            # Рисуем полную дугу трека
            painter.drawArc(arc_rect, start_angle * 16, -angle_range * 16)

            # 3. Рисуем заполненную часть дуги
            slider_gradient = QLinearGradient(60, 0, 120, 120)
            slider_gradient.setColorAt(0, QColor(self.first_gradient_color))
            slider_gradient.setColorAt(1, QColor(self.second_gradient_color))
            pen = QPen(slider_gradient, self.track_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)

            # Вычисляем угол для заполненной части
            filled_angle = current_angle - start_angle

            # Рисуем заполненную дугу
            painter.drawArc(arc_rect, start_angle * 16, int(-filled_angle * 16))

            # 4. Вычисляем позицию ползунка
            handle_angle_rad = math.radians(180 - current_angle)
            handle_x = center_x + radius * math.cos(handle_angle_rad)
            handle_y = center_y - radius * math.sin(handle_angle_rad)

            # 5. Рисуем ползунок
            # Внутренняя часть ползунка
            painter.setBrush(QColor(255, 255, 255))
            painter.setPen(QPen(QColor("#1E1F22"), 0))
            painter.drawEllipse(
                QPointF(handle_x, handle_y),
                self.handle_radius,
                self.handle_radius
            )

        if self.hover and not self.press:
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            gradient.setColorAt(0, QColor(self.first_gradient_color))
            gradient.setColorAt(1, QColor(self.second_gradient_color))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(16, 16, button_size - 5, button_size - 5)
        elif self.delete:
            painter.setPen(Qt.PenStyle.NoPen)
            gradient.setColorAt(0, QColor("#FF0080"))
            gradient.setColorAt(1, QColor("#4D000E"))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(15, 15, button_size, button_size)
        elif self.press:
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            gradient.setColorAt(0, QColor("#99" + self.first_gradient_color[1:]))
            gradient.setColorAt(1, QColor("#99" + self.second_gradient_color[1:]))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(16, 16, button_size - 5, button_size - 5)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            gradient.setColorAt(0, QColor(self.first_gradient_color))
            gradient.setColorAt(1, QColor(self.second_gradient_color))
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(16, 16, button_size - 5, button_size - 5)

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
                    QPoint(center_x + arrow_width + spacing - 5, center_y - arrow_height // 2),  # правая верхняя
                    QPoint(center_x + spacing - 5, center_y),  # левая (острие)
                    QPoint(center_x + arrow_width + spacing - 5, center_y + arrow_height // 2)  # правая нижняя
                ]
                # Вторая стрелка (правая)
                points2 = [
                    QPoint(center_x - spacing - 5, center_y - arrow_height // 2),  # левая верхняя
                    QPoint(center_x - arrow_width - spacing - 5, center_y),  # правая (острие)
                    QPoint(center_x - spacing - 5, center_y + arrow_height // 2)  # левая нижняя
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
