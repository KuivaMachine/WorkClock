import os
import random
import pygame.mixer
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaContent
from PyQt5.QtMultimedia import QMediaPlayer
from components.utils import get_resource_path, check_exists, log_error


class AudioPlayerThread(QThread):
    def __init__(self):
        super().__init__()
        self.pointer_of_song_in_history = -1
        self.is_first_play = True  # Флаг первого воспроизведения
        self.random = True  # Флаг случайного воспроизведения
        self.path_to_music = None  # Путь к дериктории с музыкой
        self.is_playing = False  # Флаг воспроизведения главной в данный момент
        self.is_background_playing = False  # Флаг воспроизведения фоновой музыки в данный момент
        self.MAX_VOL = 0.2  # Максимальная громкость
        self.off = False  # Флаг тишины основной музыки
        self.current_song = None  # Индекс текущего трека
        self.playlist = []  # Список файлов для воспроизведения
        self.history = []  # Список файлов, которые были проиграны

        self.fade_timer = QTimer()  # Таймер плавного изменения громкости
        self.fade_timer.timeout.connect(self._update_fade)

        self.check_timer = QTimer()  # Таймер отслеживания конца трека
        self.check_timer.timeout.connect(self.check_music_end)
        self.check_timer.start(500)  # Проверка каждые 500 мс

        self.background_sound_player = QMediaPlayer()  # Плеер фоновой музыки
        self.background_sound_player.stateChanged.connect(self.on_background_music_end)
        self.alarm_sound_player = QMediaPlayer()  # Плеер основной музыки

    def switch_random(self, state):
        self.random = True if state else False

    def on_background_music_end(self, state):
        # Если состояние "Остановлено", перезапускаем
        if state == QMediaPlayer.StoppedState:
            self.background_sound_player.play()

    def check_music_end(self):
        # Проверяем, закончилось ли воспроизведение
        if self.is_playing and not pygame.mixer.music.get_busy():
            self.play_next_track()

    def run(self):
        pygame.mixer.init()
        self.alarm_sound_player.setMedia(QMediaContent(QUrl.fromLocalFile(get_resource_path("music/alarm.wav"))))
        self.alarm_sound_player.setVolume(11)
        self.background_sound_player.setMedia(QMediaContent(QUrl.fromLocalFile(get_resource_path("music/water.wav"))))
        self.background_sound_player.setVolume(1)

    def play_alarm(self):
        self.alarm_sound_player.play()

    def pause_alarm(self):
        if self.is_playing:
            self.alarm_sound_player.pause()
        else:
            self.alarm_sound_player.play()

    def set_music_folder(self, track_path):
        self.path_to_music = track_path
        if self.is_playing:
            self.stop_music()
            self.play_music()
        else:
            self.is_first_play = True

    def stop_music(self, fade_duration=3000):
        self.is_playing = False
        self._fade_volume(self.MAX_VOL, 0.0, pygame.mixer.stop, fade_duration)
        self.off = True

    def set_background_volume(self, volume):
        self.background_sound_player.setVolume(volume)

    def play_music(self):
        audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac'}
        self.is_playing = True
        self.off = False
        if not self.playlist and self.path_to_music:
            self.playlist = [
                os.path.join(self.path_to_music, f)
                for f in os.listdir(self.path_to_music)
                if os.path.splitext(f)[1].lower() in audio_extensions
            ]
        if self.playlist:
            self.play_next_track()
        self.background_sound_player.play()
        self.is_background_playing = True

    def get_next_track(self):
        if self.playlist:
            if self.random:
                next_song_index = random.randint(0, len(self.playlist) - 1)
                while len(self.playlist) > 1 and self.playlist[next_song_index] == self.current_song:
                    next_song_index = random.randint(0, len(self.playlist) - 1)
                return self.playlist[next_song_index]
            else:
                return self.playlist[
                    (self.playlist.index(self.current_song) + 1) % len(self.playlist) if not self.is_first_play else 0]

    def play_previous_track(self):
        if self.is_playing and self.history:
            try:
                if self.pointer_of_song_in_history > 0:
                    self.current_song = self.history[self.pointer_of_song_in_history - 1]
                    while not check_exists(self.current_song):
                        self.pointer_of_song_in_history -= 1
                        self.current_song = self.history[self.pointer_of_song_in_history]
                    self.pointer_of_song_in_history -= 1
                else:
                    self.current_song = self.history[0]
                self.play_track(self.current_song)
                self.print_history()

            except Exception as e:
                log_error(self.path_to_music, e, "play_previous_track", self.current_song)
                print("ОШИБКА В play_previous_track, ПЕСНЯ: ", self.current_song, e)

    def delete_current_track(self):
        if self.playlist:
            if self.is_playing:
                try:
                    deleting_song = self.current_song
                    if len(self.playlist) > 1:
                        self.play_next_track()
                        self.pointer_of_song_in_history -= 1
                        self.history.pop(self.pointer_of_song_in_history)
                        os.remove(deleting_song)
                    else:
                        self.stop_music()
                        pygame.mixer.music.unload()
                        os.remove(deleting_song)

                except Exception as e:
                    log_error(self.path_to_music, e, "delete_current_track", self.current_song)
                    print("ОШИБКА В delete_current_track, ПЕСНЯ: ", self.current_song, e)

    def play_next_track(self):
        if self.playlist and self.is_playing:
            try:
                # Если я не в конце истории - беру следующий в истории трек
                if self.pointer_of_song_in_history != -1 and len(self.history) - 1 > self.pointer_of_song_in_history:
                    self.current_song = self.history[self.pointer_of_song_in_history + 1]
                    while not check_exists(self.current_song):
                        self.pointer_of_song_in_history += 1
                        self.current_song = self.history[self.pointer_of_song_in_history]
                # Если я в конце истории - просто беру следующий в плейлисте
                else:
                    self.current_song = self.get_next_track()
                    while not check_exists(self.current_song):
                        self.current_song = self.get_next_track()
                    self.history.append(self.current_song)

                self.play_track(self.current_song)
                self.pointer_of_song_in_history += 1
                self.print_history()

            except Exception as e:
                log_error(self.path_to_music, e, "play_next_track", self.current_song)
                print("ОШИБКА В play_next_track, ПЕСНЯ: ", self.current_song, e)

    def play_track(self, song):
        pygame.mixer.music.load(song)
        pygame.mixer.music.play()
        pygame.mixer.music.set_volume(0.0)
        self._fade_volume(0.0, self.MAX_VOL)

    def print_history(self):
        """Цветной вывод истории"""
        if not self.history:
            print("\033[90mИстория пуста\033[0m")
            return

        print("\033[1;36m" + "─" * 50 + "\033[0m")
        print("\033[1;36m🎵 ИСТОРИЯ ВОСПРОИЗВЕДЕНИЯ\033[0m")
        print("\033[1;36m" + "─" * 50 + "\033[0m")

        for i, song in enumerate(self.history):
            song_name = os.path.basename(song)

            if i == self.pointer_of_song_in_history:
                print(f"\033[1;32m▶ [{i:2d}] {song_name}\033[0m")
            else:
                print(f"\033[90m  [{i:2d}] {song_name}\033[0m")

        print("\033[1;36m" + "─" * 50 + "\033[0m")

    # ГЛАВНЫЙ МЕТОД PAUSE/PLAY
    def switch_play_pause(self):
        if not self.off:
            if self.is_first_play:
                self.play_music()
                self.is_first_play = False
                return
            else:
                if self.is_playing:
                    self.is_playing = False
                    self._fade_volume(self.MAX_VOL, 0.0, pygame.mixer.music.pause)
                else:
                    self.is_playing = True
                    pygame.mixer.music.unpause()
                    self._fade_volume(0.0, self.MAX_VOL)

        if self.is_background_playing:
            self.background_sound_player.pause()
            self.is_background_playing = False
        else:
            self.background_sound_player.play()
            self.is_background_playing = True

    def _fade_volume(self, start_volume, end_volume, custom_callback=None, fade_duration=2500):
        self.fade_timer.stop()
        self.current_volume = start_volume
        self.target_volume = end_volume
        self.custom_callback = custom_callback
        self.fade_duration = fade_duration
        self.fade_timer.start(50)

    def _update_fade(self):
        """Обновление громкости на каждом шаге фейда"""
        # Рассчитываем шаг изменения громкости для 15 секунд
        total_steps = self.fade_duration / 100  # 15000ms / 100ms = 150 шагов
        step = 1.0 / total_steps  # Шаг изменения громкости

        if self.current_volume < self.target_volume:
            self.current_volume = min(self.current_volume + step, self.target_volume)
        else:
            self.current_volume = max(self.current_volume - step, self.target_volume)

        # Устанавливаем громкость
        pygame.mixer.music.set_volume(self.current_volume)

        # Проверяем достижение целевой громкости
        if abs(self.current_volume - self.target_volume) < 0.01:
            self.fade_timer.stop()
            self.current_volume = self.target_volume

            if self.custom_callback:
                self.custom_callback()

    def quit(self):
        """Корректное завершение"""
        self.fade_timer.stop()

        pygame.mixer.music.stop()
        pygame.mixer.quit()

        super().quit()
