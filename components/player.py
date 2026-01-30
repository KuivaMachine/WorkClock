import os
import random
from pathlib import Path

import pygame.mixer
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaContent
from PyQt5.QtMultimedia import QMediaPlayer

from components.utils import get_resource_path, check_exists, log_error


class AudioPlayerThread(QThread):
    update_song_history = pyqtSignal(str, list)

    def __init__(self, volume):
        super().__init__()
        self.pointer_of_song_in_history = -1  # Указатель индекса текущего трека в истории
        self.is_first_play = True  # Флаг первого воспроизведения
        self.random = True  # Флаг случайного воспроизведения
        self.path_to_music = ""  # Путь к дериктории с музыкой
        self.play_button_on = False  # Флаг воспроизведения главной в данный момент

        self.CURRENT_VOLUME = volume  # Громкость
        self.off = False  # Флаг тишины основной музыки
        self.current_song = None  # Индекс текущего трека
        self.playlist = []  # Список файлов для воспроизведения
        self.history = []  # Список файлов, которые были проиграны

        self.fade_timer = QTimer()  # Таймер плавного изменения громкости
        self.fade_timer.timeout.connect(self._update_fade)

        self.check_timer = QTimer()  # Таймер отслеживания конца трека
        self.check_timer.timeout.connect(self.check_music_end)
        self.check_timer.start(500)  # Проверка каждые 500 мс

        self.alarm_sound_player = QMediaPlayer()  # Плеер основной музыки

    # ГЛАВНЫЙ МЕТОД PAUSE/PLAY
    def switch_play_pause(self,is_playing):
        self.play_button_on = is_playing
        if not self.off:
            if self.is_first_play:
                self.play_music()
                self.is_first_play = False
                return
            else:
                if self.play_button_on:
                    self.play_button_on = False
                    self._fade_volume(self.CURRENT_VOLUME, 0.0, pygame.mixer.music.pause)
                else:
                    self.play_button_on = True
                    pygame.mixer.music.unpause()
                    self._fade_volume(0.0, self.CURRENT_VOLUME)
        else:
            self.play_button_on = not is_playing


    def set_volume(self, value):
        if 0.0 <= value <= 1.0:
            self.CURRENT_VOLUME = value
            if not self.off:
                pygame.mixer.music.set_volume(value)

    def switch_random(self, state):
        self.random = True if state else False


    def check_music_end(self):
        # Проверяем, закончилось ли воспроизведение
        if self.play_button_on and not pygame.mixer.music.get_busy():
            self.play_next_track()

    def run(self):
        pygame.mixer.init()
        pygame.mixer.music.set_volume(self.CURRENT_VOLUME)
        self.alarm_sound_player.setMedia(QMediaContent(QUrl.fromLocalFile(get_resource_path("music/alarm.wav"))))
        self.alarm_sound_player.setVolume(11)


    def play_alarm(self):
        self.alarm_sound_player.play()

    def pause_alarm(self):
        if self.play_button_on:
            self.alarm_sound_player.pause()
        else:
            self.alarm_sound_player.play()

    def set_music_folder(self, track_path):
        self.path_to_music = track_path
        if self.play_button_on:
            self.stop_music()
            pygame.mixer.music.unload()
            self.playlist = []
            self.history = []
            self.play_music()
        else:
            self.is_first_play = True
            self.off = False

    def set_music_off(self):
        self._fade_volume(self.CURRENT_VOLUME, 0.0, pygame.mixer.stop, 3000)
        self.off = True
        pygame.mixer.music.unload()
        self.playlist = []
        self.history = []


    def stop_music(self, fade_duration=3000):
        self.play_button_on = False
        self._fade_volume(self.CURRENT_VOLUME, 0.0, pygame.mixer.stop, fade_duration)
        self.off = True


    def play_music(self):
        self.play_button_on = True
        self.off = False
        if not self.playlist and self.path_to_music:
            self.playlist = self.find_audio_files_recursive(self.path_to_music)
        if self.playlist:
            self.play_next_track()


    def find_audio_files_recursive(self, directory):
        """Рекурсивный поиск аудиофайлов с использованием pathlib"""
        audio_files = []

        try:
            path = Path(directory)
            # Рекурсивный поиск всех файлов с нужными расширениями
            for ext in {'.mp3', '.wav'}:
                audio_files.extend([
                    str(file_path) for file_path in path.rglob(f"*{ext}")
                ])
        except Exception as e:
            print(f"Ошибка при сканировании директории {directory}: {e}")
        return audio_files

    def get_next_track(self):
        if self.playlist:
            if self.random:
                return self.get_random_song()
            else:
                return self.playlist[
                    (self.playlist.index(self.current_song) + 1) % len(self.playlist) if not self.is_first_play else 0]

    def get_random_song(self):
        if self.playlist:
            if len(self.playlist) <= 1:
                return self.playlist[0]
            # Ищем в плейлисте песню, которой еще не было
            available_songs = [song for song in self.playlist if song not in self.history]
            # Если все песни были в истории - берем любую
            if not available_songs:
                available_songs = self.playlist
            # Выбираем случайную из доступных
            return random.choice(available_songs)

    def play_previous_track(self):
        if self.play_button_on and self.history:
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
                self.update_song_history.emit(self.current_song,
                                              self.get_context_songs(self.playlist, self.current_song))
                # self.print_history()

            except Exception as e:
                log_error(self.path_to_music, e, "play_previous_track", self.current_song)
                print("ОШИБКА В play_previous_track, ПЕСНЯ: ", self.current_song, e)

    def delete_current_track(self):
        if self.playlist:
            if self.play_button_on:
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
        if self.playlist and self.play_button_on:
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
                self.update_song_history.emit(self.current_song,
                                              self.get_context_songs(self.playlist, self.current_song))

                # self.print_history()

            except Exception as e:
                log_error(self.path_to_music, e, "play_next_track", self.current_song)
                print("ОШИБКА В play_next_track, ПЕСНЯ: ", self.current_song, e)

    def play_track(self, song):
        pygame.mixer.music.load(song)
        pygame.mixer.music.play()
        pygame.mixer.music.set_volume(0.0)
        self._fade_volume(0.0, self.CURRENT_VOLUME)

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

    def get_context_songs(self, song_list, current_song):
        if not song_list:
            return []

        try:
            current_index = song_list.index(current_song)
        except ValueError:
            return song_list[:11]

        if len(song_list) <= 11:
            return song_list

        # Вычисляем стартовый индекс
        start_index = max(0, min(current_index - 5, len(song_list) - 11))
        return song_list[start_index:start_index + 11]

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
