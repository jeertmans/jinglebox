import argparse
import logging
import sys
from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import List

import rtoml
from pydantic import BaseModel, FilePath, field_serializer
from PySide6.QtCore import QDateTime, Qt, QTime, QTimer, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QApplication,
    QDateTimeEdit,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QStyle,
    QTimeEdit,
    QWidget,
)

from .utils import set_application_volume


class Anchor(str, Enum):
    start = "start"
    half = "half"
    end = "end"


class Jingle(BaseModel):
    file: FilePath
    name: str = "Unnamed"
    offset: timedelta = timedelta(seconds=0.0)
    anchor: Anchor = Anchor.start

    @field_serializer("file")
    def serialize_file(self, file: FilePath, _info):
        return file.as_posix()

    @field_serializer("offset")
    def serialize_offset(self, offset: timedelta, _info):
        return offset.total_seconds()


class Jingles(BaseModel):
    jingles: List[Jingle] = []

    def __iter__(self):
        return iter(self.jingles)

    @classmethod
    def from_file(cls, path):
        return cls.model_validate(rtoml.load(path))

    def to_file(self, path) -> None:
        """Dumps the configuration to a file."""
        rtoml.dump(self.model_dump(), path, pretty=True)


def slider_value_as_percentage(slider: QSlider) -> float:
    return slider.value() / (slider.maximum() - slider.minimum())


class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class JingleBox(QMainWindow):
    def __init__(self, jingles_path: Path):
        super().__init__()

        # Fix ToolTip with dark theme issue

        self.setStyleSheet(
            """
            QToolTip {
                background-color: #ea5626;
            }"""
        )

        # Central widget

        central_widget = QWidget()
        layout = QGridLayout(central_widget)

        # Game settings

        self.datetime_format = "yyyy/MM/dd HH:mm:ss"
        self.time_format = "HH:mm:ss"
        start = QDateTime.fromString("2023/08/13 09:00:00", self.datetime_format)
        end = QDateTime.fromString("2023/08/13 13:00:00", self.datetime_format)
        game_duration = QTime.fromString("00:30:00", self.time_format)
        break_duration = QTime.fromString("00:05:00", self.time_format)

        game_settings = QGroupBox("Game settings")
        game_settings.setCheckable(True)
        grid = QGridLayout()

        grid.addWidget(QLabel("First game at:"), 1, 1)
        self.start_datetime = QDateTimeEdit(start)
        self.start_datetime.dateTimeChanged.connect(
            lambda _: self.update_game_settings()
        )
        self.start_datetime.setDisplayFormat(self.datetime_format)
        grid.addWidget(self.start_datetime, 1, 2)

        grid.addWidget(QLabel("Last game at:"), 2, 1)
        self.end_datetime = QDateTimeEdit(end)
        self.end_datetime.dateTimeChanged.connect(lambda _: self.update_game_settings())
        self.end_datetime.setDisplayFormat(self.datetime_format)
        grid.addWidget(self.end_datetime, 2, 2)

        grid.addWidget(QLabel("Game duration:"), 3, 1)
        self.game_duration = QTimeEdit(game_duration)
        self.game_duration.timeChanged.connect(lambda _: self.update_game_settings())
        self.game_duration.setDisplayFormat(self.time_format)
        grid.addWidget(self.game_duration, 3, 2)

        grid.addWidget(QLabel("Break duration:"), 4, 1)
        self.break_duration = QTimeEdit(break_duration)
        self.break_duration.timeChanged.connect(lambda _: self.update_game_settings())
        self.break_duration.setDisplayFormat(self.time_format)
        grid.addWidget(self.break_duration, 4, 2)

        game_settings.setLayout(grid)
        layout.addWidget(game_settings, 1, 1)

        # Jingles settings

        jingles_settings = QGroupBox(f"Jingles (from: {jingles_path})")
        self.jingles = Jingles.from_file(jingles_path)

        grid = QGridLayout()

        grid.addWidget(QLabel("Name"), 1, 1)
        offset_label = QLabel("Offset")
        offset_label.setToolTip("Time offset w/ respect of the start of a game.")
        grid.addWidget(offset_label, 1, 2)

        for i, jingle in enumerate(self.jingles, start=2):
            jingle_label = QLabel(jingle.name)
            jingle_label.setToolTip(f"Source: {jingle.file.as_posix()}")
            grid.addWidget(jingle_label, i, 1)

            total_seconds = jingle.offset.total_seconds()

            if total_seconds < 0:
                total_seconds = -total_seconds
                sign = "-"
            else:
                sign = "+"
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int((total_seconds % 3600) % 60)
            grid.addWidget(
                QLabel(sign + f"{hours:02d}h:{minutes:02d}m:{seconds:02d}s"), i, 2
            )

            icon = QIcon.fromTheme(
                "media-playback-start.png",
                self.style().standardIcon(QStyle.SP_MediaPlay),
            )

            def make_callback(self, file):
                def callback():
                    return self.play_jingle(file)

                return callback

            button = QPushButton("")
            button.setIcon(icon)

            button.clicked.connect(make_callback(self, jingle.file))
            grid.addWidget(button, i, 3)

        jingles_settings.setLayout(grid)
        layout.addWidget(jingles_settings, 2, 1)

        # Sound setting

        self.muted = False

        sound_info = QGroupBox("Sound settings")
        sound_info.setCheckable(True)
        grid = QGridLayout()

        grid.addWidget(QLabel("Music application:"), 1, 1)
        self.application_name = QLineEdit()
        self.application_name.setToolTip(
            "The name of the application that plays music.\n"
            "The name is found using `pactl list sink-inputs`.\n"
            "If no name is provided, or the name is wrong, "
            "an error message will be printed in the console"
        )
        grid.addWidget(self.application_name, 1, 2)

        application_volume_label = QLabel()
        application_volume_muted_label = QLabel()
        self.application_name.textChanged.connect(
            lambda text: application_volume_label.setText(f"{text}'s volume:")
        )
        self.application_name.textChanged.connect(
            lambda text: application_volume_muted_label.setText(
                f"{text}'s volume (muted):"
            )
        )
        self.application_name.setText("Spotify")

        self.application_volume_slider = QSlider(Qt.Horizontal)
        self.application_volume_muted_slider = QSlider(Qt.Horizontal)
        self.jingles_volume_slider = QSlider(Qt.Horizontal)

        self.application_volume_slider.valueChanged.connect(
            lambda _: self.set_application_volume()
        )
        self.application_volume_muted_slider.valueChanged.connect(
            lambda _: self.set_application_volume()
        )
        self.jingles_volume_slider.valueChanged.connect(
            lambda _: self.set_jingles_volume()
        )

        grid.addWidget(application_volume_label, 2, 1)
        grid.addWidget(application_volume_muted_label, 3, 1)
        grid.addWidget(QLabel("Jingles' volume:"), 4, 1)

        grid.addWidget(self.application_volume_slider, 2, 2)
        grid.addWidget(self.application_volume_muted_slider, 3, 2)
        grid.addWidget(self.jingles_volume_slider, 4, 2)

        sound_info.setLayout(grid)
        layout.addWidget(sound_info, 1, 2)

        # Game info

        game_info = QGroupBox("Game info")
        grid = QGridLayout()

        grid.addWidget(QLabel("Next game at:"), 1, 1)
        self.next_game_label = QLabel("")
        grid.addWidget(self.next_game_label, 1, 2)

        grid.addWidget(QLabel("Next jingle at:"), 2, 1)
        self.next_jingle_label = QLabel("")
        grid.addWidget(self.next_jingle_label, 2, 2)

        log_text_box = QTextEditLogger(self)
        # You can format what is printed to text box
        log_text_box.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(log_text_box)
        # You can control the logging level
        logging.getLogger().setLevel(logging.DEBUG)
        grid.addWidget(log_text_box.widget, 3, 1, 1, 2)

        game_info.setLayout(grid)
        layout.addWidget(game_info, 2, 2)

        # Audio output for jingles

        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self.update_application_volume)

        # Set audio levels

        self.application_volume_slider.setValue(66)
        self.application_volume_muted_slider.setValue(33)
        self.jingles_volume_slider.setValue(99)

        # Finish up
        self.update_game_settings()
        self.setCentralWidget(central_widget)

        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.check_for_jingle_and_game)
        self.timer.start()

    def update_game_settings(self):
        logging.debug("Game settings have changed, updating...")
        now = QDateTime.currentDateTime()
        end = self.end_datetime.dateTime()

        if now >= end:
            self.next_game_label.setText("no more games are planned")
            return

        self.games = []

        start = self.start_datetime.dateTime()
        game_duration_msecs = self.game_duration.time().msecsSinceStartOfDay()
        break_duration_msecs = self.break_duration.time().msecsSinceStartOfDay()
        time_between_games_msecs = game_duration_msecs + break_duration_msecs

        while start < now:
            # self.games.append(start)  # We don't add past games :-)
            start = start.addMSecs(time_between_games_msecs)

        # TODO: also update after each game ends
        self.next_game_label.setText(start.toString(self.datetime_format))

        while start < end:
            self.games.append(start)
            start = start.addMSecs(time_between_games_msecs)

        self.games = self.games[::-1]  # Latest if first

        self.update_jingles()

    def update_jingles(self):
        self.planned_jingles = []
        now = QDateTime.currentDateTime()

        for game in self.games:
            start = game
            game_duration_msecs = self.game_duration.time().msecsSinceStartOfDay()
            half = start.addMSecs(game_duration_msecs // 2)
            end = start.addMSecs(game_duration_msecs)

            anchor_map = {
                Anchor.start: start,
                Anchor.half: half,
                Anchor.end: end,
            }

            for jingle in self.jingles:
                anchor = anchor_map[jingle.anchor]
                anchor = anchor.addMSecs(int(jingle.offset.total_seconds() * 1000))

                if now > anchor:
                    continue

                planned_jingle = (
                    jingle.file,
                    jingle.name,
                    anchor,
                )
                self.planned_jingles.append(planned_jingle)

        self.planned_jingles.sort(key=lambda p: p[2], reverse=True)

        # TODO: only update in one method
        if len(self.planned_jingles) > 0:
            _, name, datetime = self.planned_jingles[-1]
            self.next_jingle_label.setText(
                datetime.toString(self.datetime_format) + f" ({name})"
            )
        else:
            self.next_jingle_label.setText("no more jingles are planned")

    def check_for_jingle_and_game(self):
        now = QDateTime.currentDateTime()

        if len(self.games) > 0 and now > self.games[-1]:
            logging.debug("We entered a new game, updating next game info.")
            self.games.pop()

            if len(self.games) > 0:
                self.next_game_label.setText(
                    self.games[-1].toString(self.datetime_format)
                )
            else:
                self.next_game_label.setText("no more games are planned")

        if len(self.planned_jingles) > 0 and now > self.planned_jingles[-1][2]:
            logging.debug("We play a new jingle and update next jingle info.")
            file, _, _ = self.planned_jingles.pop()
            self.play_jingle(file)

            if len(self.planned_jingles) > 0:
                _, name, datetime = self.planned_jingles[-1]
                self.next_jingle_label.setText(
                    datetime.toString(self.datetime_format) + f" ({name})"
                )
            else:
                self.next_jingle_label.setText("no more jingles are planned")

    def play_jingle(self, file: Path):
        logging.debug(f"Playing jingle from file: {file.as_posix()}")
        self.player.setSource(QUrl.fromLocalFile(file.as_posix()))
        self.player.setPosition(0)
        self.muted = True
        self.player.play()

    def update_application_volume(self, state):
        if state == QMediaPlayer.MediaStatus.EndOfMedia:
            self.muted = False

        self.set_application_volume()

    def set_application_volume(self):
        application = self.application_name.text()

        if self.muted:
            volume = slider_value_as_percentage(self.application_volume_muted_slider)
        else:
            volume = slider_value_as_percentage(self.application_volume_slider)

        set_application_volume(application, volume)

    def set_jingles_volume(self):
        volume = slider_value_as_percentage(self.jingles_volume_slider)
        self.audio_output.setVolume(volume)


def main():

    parser = argparse.ArgumentParser(description="Launches the JingleBox!")
    parser.add_argument(
        "jingles_path",
        nargs="?",
        metavar="FILE",
        type=Path,
        default=Path("jingles.example.toml"),
        help="Path to jingles' configuration. Defaults to jingles.example.toml",
    )
    args = parser.parse_args()

    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    app.setApplicationName("JingleBox")

    jingle_box = JingleBox(jingles_path=args.jingles_path)
    jingle_box.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
