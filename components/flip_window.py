import os

from PyQt5.QtCore import Qt, QEasingCurve, QRect
from PyQt5.QtGui import QPainter, QTransform, QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class SlideHintArea(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(0, 0, 300, 40)
        self.label = QLabel(self)
        self.hover = False
        self.timer = QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update_label)
        self.counter = 1

        self.label.setGeometry(120, 0, 60, 40)
        font = QFont("HYWenHei", 18)
        font.setBold(False)
        self.label.setFont(font)
        self.label.setStyleSheet("""
                        QLabel {
                    padding: 0px;
                    color: #808080;
                    background-color: transparent;
                }
                        """)

    def stop_flash(self):
        self.hover = False
        self.timer.stop()
        self.label.setText("")
        self.counter = 1

    def update_label(self):
        if self.counter <= 3:
            self.label.setText(self.counter * ">")
            self.counter += 1
        else:
            self.label.setText("")
            self.counter = 1
        self.update()
        self.timer.start()

    def enterEvent(self, event):
        if not self.hover:
            self.hover = True
            self.update_label()

    def leaveEvent(self, event):
        self.hover = False
        self.timer.stop()
        self.label.setText("")
        self.counter = 1

from PyQt5.QtCore import QTimer, QPropertyAnimation, pyqtProperty

class MarqueeLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.original_text = text
        self.current_position = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.animation_speed = 300  # ms
        self.is_marquee_active = False
        self.setText(text)

    def setText(self, text):
        super().setText(text)
        self.original_text = text
        self.check_marquee_needed()

    def check_marquee_needed(self):
        """Проверяет, нужен ли эффект бегущей строки"""
        if len(self.original_text) > 26:
            if not self.is_marquee_active:
               self.start_marquee()
        else:
            self.stop_marquee()

    def start_marquee(self):
        """Запускает эффект бегущей строки"""
        self.is_marquee_active = True
        self.current_position = 0
        self.timer.start(self.animation_speed)

    def stop_marquee(self):
        """Останавливает эффект бегущей строки"""
        self.is_marquee_active = False
        self.timer.stop()
        self.current_position = 0

    def update_text(self):
        """Обновляет текст для эффекта бегущей строки"""
        if len(self.original_text) <= 26:
            self.stop_marquee()
            return

        # Двигаем позицию
        self.current_position += 1

        # Если осталось 17 символов, начинаем сначала
        if self.current_position > len(self.original_text) - 17:
            self.current_position = 0

        # Обрезаем текст
        display_text = self.original_text[self.current_position:]

        # Обрезаем до максимальной длины
        display_text = display_text[:26]
        super().setText(display_text)



class FlipCard(QWidget):
    def __init__(self,font_color):
        super().__init__()
        self.current_label = None
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.back_widget = None
        self.front_widget = None
        self.start_angle = None
        self.press = False
        self.font_color =font_color
        self.drag_pos = None
        self.card_width = 300
        self.card_height = 450
        self._rotation_angle = 0
        self.setFixedSize(self.card_width, self.card_height + 80)
        self.setStyleSheet("""
                                         QWidget{
                                        background-color: transparent;
                                        border: none;
                                        padding: 0px;
                                        }
                                        """)

        # Контейнер для контента (будет вращаться)
        self.content_widget = QWidget()
        self.content_widget.setAttribute(Qt.WA_StyledBackground, True)
        self.content_widget.setStyleSheet("""
                         QWidget{
                        background-color:transparent;
                        border: none;
                        }
                        """)

        self.trigger_widget = SlideHintArea()
        self.trigger_widget.setParent(self)

        self.animation = QPropertyAnimation(self, b"rotation_angle")
        self.animation.setDuration(700)
        self.animation.setEasingCurve(QEasingCurve.OutBounce)

        self.song_list = ["тут",
                          "будут",
                          "песенки",
                          ":)",
                        ]

        self.back_widget = QWidget()
        self.back_widget.setGeometry(2, 40, self.card_width-4, 450)
        self.back_widget.setStyleSheet("""
                 QWidget{
                    background-color: #transparent;
                    border-radius: 25px; 
                    border: 1px solid #808080;
                    }
                """)

        self.history_layout = QVBoxLayout(self.back_widget)
        self.history_layout.setAlignment(Qt.AlignTop)
        self.history_layout.setSpacing(10)
        self.history_layout.setContentsMargins(10, 40, 0, 20)
        self.update_song_history("тут", self.song_list)
        self.history_layout.addStretch()

    def update_song_history(self, current_song, song_list):
        while self.history_layout.count():
            child = self.history_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, song in enumerate(song_list):
            song_name = "  "+str(os.path.basename(song).replace(".mp3", "").replace(".wav", ""))

            song_text = QLabel(song_name)
            if song==current_song:
                song_text = MarqueeLabel(song_name)
                song_text.setStyleSheet(f"""
                         QLabel{{
                            color: {self.font_color};
                            font-weight: bold;
                            font-size: 20px;
                            font-family: 'Sans Serif';
                            border: none;
                            background-color: transparent;
                        }}
                """)
                self.current_label = song_text
            else:
                song_text.setStyleSheet("""
                                             QLabel{
                                                color: #999999;
                                                font-size: 20px;
                                                font-weight: light;
                                                font-family: 'Sans Serif'; 
                                                border: none;
                                                background-color: transparent;
                                            }
                                    """)
            self.history_layout.addWidget(song_text)

    def set_font_color(self, font_color):
        self.font_color=font_color
        self.current_label.setStyleSheet(f"""
                                 QLabel{{
                                    color:{font_color};
                                    font-weight: bold;
                                    font-size: 20px;
                                    font-family: 'Sans Serif'; 
                                    border: none;
                                    background-color: transparent;
                                }}
                        """)

    def set_front_widget(self, front_widget):
        self.front_widget = front_widget
        self.front_widget.setGeometry(0, 40, self.card_width, 450)
        self.front_widget.setParent(self)
        self.back_widget.setParent(self)

    def get_rotation_angle(self):
        return self._rotation_angle

    def set_rotation_angle(self, angle):
        self._rotation_angle = angle % 360
        self.update()  # Перерисовываем при изменении угла

    # Кастомное property для анимации
    rotation_angle = pyqtProperty(float, get_rotation_angle, set_rotation_angle)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.pos()
            track_area = QRect(0, 0, 300, 50)
            if self.drag_pos is not None and track_area.contains(self.drag_pos):
                self.trigger_widget.stop_flash()
                self.press = True
                self.start_angle = self._rotation_angle  # Сохраняем начальный угол
                self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            track_area = QRect(0, 0, 300, 50)
            if self.drag_pos is not None and track_area.contains(self.drag_pos):
                delta_x = event.pos().x() - self.drag_pos.x()
                # Вычисляем новый угол относительно начального
                self._rotation_angle = self.start_angle - delta_x
                self.update()
            else:
                super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.press:
            self.press = False
            self.drag_pos = None

            if event.button() == Qt.LeftButton:
                normalized_angle = self.rotation_angle % 360
                self.animation.setStartValue(normalized_angle)

                if 0 <= normalized_angle < 90:
                    self.animation.setEndValue(0)

                elif 90 <= normalized_angle < 180:
                    self.animation.setEndValue(180)

                elif 180 <= normalized_angle < 270:
                    self.animation.setEndValue(180)

                elif 270 <= normalized_angle < 360:
                    self.animation.setEndValue(360)

            self.animation.start()
            self.update()
        super().mouseMoveEvent(event)





    def paintEvent(self, event):
        painter = QPainter(self)
        # Нормализуем угол в диапазон 0-360 градусов
        normalized_angle = self.rotation_angle % 360

        # Если карточка не вращается (угол 0° или 180°) - показываем реальные виджеты
        if normalized_angle == 0:
            # Показываем реальные виджеты для интерактивности
            self.front_widget.setParent(self)
            self.front_widget.show()
            self.back_widget.hide()
        elif normalized_angle == 180:
            self.front_widget.hide()
            self.back_widget.setParent(self)
            self.back_widget.show()
        else:
            # Применяем трансформацию вращения вокруг оси Y
            transform = QTransform()
            transform.translate(self.width() / 2, self.height() / 2)
            transform.rotate(normalized_angle, Qt.YAxis)

            if 90 < normalized_angle < 270:
                transform.scale(-1, 1)
                self.back_widget.setParent(self.content_widget)
                self.back_widget.show()
                self.front_widget.hide()
            else:
                self.front_widget.setParent(self.content_widget)
                self.front_widget.show()
                self.back_widget.hide()

            transform.translate(-self.width() / 2, -self.height() / 2)
            painter.setTransform(transform)

            # Отрисовываем контент
            self.content_widget.render(painter, self.content_widget.pos())
