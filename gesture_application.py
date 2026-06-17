from pathlib import Path
import random

import pyglet

pyglet.options["dpi_scaling"] = "stretch"

from pyglet import shapes

from recognizer import (
    GAME_GESTURES,
    build_recognizer_from_logs,
    display_label,
)

WIDTH = 920
HEIGHT = 660
PLAY_LEFT = 24
PLAY_RIGHT = WIDTH - 24
PLAY_BOTTOM = 72
PLAY_TOP = HEIGHT - 130
PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "datasets" / "unistroke_test"
TEMPLATES_PER_GESTURE = 10
SEQUENCE_LENGTH = 4
SEQUENCE_SLOT_SIZE = 42
SEQUENCE_SLOT_GAP = 18


class ShapeTrainer(pyglet.window.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "Assignment 6 Trainer", resizable=False)
        self.batch = pyglet.graphics.Batch()
        self.recognizer = build_recognizer_from_logs(
            LOG_DIR,
            GAME_GESTURES,
            templates_per_label=TEMPLATES_PER_GESTURE,
            include_reversed=True,
        )
        self.random = random.Random(6)
        self.sequence = self._make_sequence()
        self.sequence_index = 0
        self.stroke = []
        self.is_drawing = False
        self.score = 0
        self.streak = 0
        self.message = f"Draw 1/{len(self.sequence)}: {display_label(self.target)}."

        self.title_label = pyglet.text.Label(
            "Trainer",
            x=24,
            y=HEIGHT - 38,
            font_size=24,
            color=(25, 31, 39, 255),
            batch=self.batch,
        )
        self.target_label = pyglet.text.Label(
            "",
            x=24,
            y=HEIGHT - 82,
            font_size=16,
            color=(25, 31, 39, 255),
            batch=self.batch,
        )
        self.sequence_label = pyglet.text.Label(
            "Code",
            x=WIDTH // 2,
            y=HEIGHT - 76,
            anchor_x="center",
            font_size=12,
            color=(76, 86, 99, 255),
            batch=self.batch,
        )
        self.score_label = pyglet.text.Label(
            "",
            x=WIDTH - 24,
            y=HEIGHT - 38,
            anchor_x="right",
            font_size=16,
            color=(25, 31, 39, 255),
            batch=self.batch,
        )
        self.message_label = pyglet.text.Label(
            self.message,
            x=24,
            y=30,
            font_size=13,
            color=(76, 86, 99, 255),
            batch=self.batch,
        )

    def on_draw(self):
        self.clear()
        self._draw_background()
        self._draw_sequence_hint()
        self.target_label.text = (
            f"{self.sequence_index + 1}/{len(self.sequence)}: "
            f"{display_label(self.target)}"
        )
        self.score_label.text = f"Score {self.score}  Streak {self.streak}"
        self.message_label.text = self.message
        self.batch.draw()
        self._draw_stroke()

    def on_mouse_press(self, x, y, button, modifiers):
        if button != pyglet.window.mouse.LEFT or not self._inside_play_area(x, y):
            return
        self.stroke = []
        self.is_drawing = True
        self._add_stroke_point(x, y)
        self.message = "Drawing"

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not buttons & pyglet.window.mouse.LEFT:
            return
        if not self.is_drawing and self._inside_play_area(x, y):
            self.stroke = []
            self.is_drawing = True
            self.message = "Drawing"
        if self.is_drawing:
            self._add_stroke_point(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button != pyglet.window.mouse.LEFT or not self.is_drawing:
            return
        self.is_drawing = False
        self._add_stroke_point(x, y)
        self._score_current_stroke()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.SPACE:
            self._new_sequence()
            self.message = f"New: draw 1/{len(self.sequence)}: {display_label(self.target)}."
        elif symbol == pyglet.window.key.C:
            self.is_drawing = False
            self.stroke.clear()
            self.message = "Cleared."

    def _score_current_stroke(self):
        if len(self.stroke) < 3:
            self.message = "Longer stroke."
            return

        try:
            guessed, score = self.recognizer.recognize(self.stroke)
        except ValueError as exc:
            self.message = str(exc)
            return

        expected = self.target
        if guessed == expected:
            self.score += 100 + self.sequence_index * 25
            if self.sequence_index == len(self.sequence) - 1:
                self.streak += 1
                self.score += 150 + self.streak * 25
                self._new_sequence()
                self.message = (
                    f"Done: {display_label(guessed)} ({score:.2f}). "
                    f"Next: {display_label(self.target)}."
                )
            else:
                self.sequence_index += 1
                self.stroke.clear()
                self.message = (
                    f"Correct: {display_label(guessed)} ({score:.2f}). "
                    f"Next {self.sequence_index + 1}/{len(self.sequence)}: "
                    f"{display_label(self.target)}."
                )
        else:
            self.streak = 0
            self.sequence_index = 0
            self.stroke.clear()
            self.message = (
                f"Got {display_label(guessed)} ({score:.2f}). "
                f"Reset: {display_label(self.target)}."
            )

    @property
    def target(self):
        return self.sequence[self.sequence_index]

    def _make_sequence(self):
        sequence = []
        previous = None
        for _ in range(SEQUENCE_LENGTH):
            choices = [gesture for gesture in GAME_GESTURES if gesture != previous]
            selected = self.random.choice(choices)
            sequence.append(selected)
            previous = selected
        return sequence

    def _new_sequence(self):
        self.sequence = self._make_sequence()
        self.sequence_index = 0
        self.stroke.clear()

    def _inside_play_area(self, x, y):
        return PLAY_LEFT <= x <= PLAY_RIGHT and PLAY_BOTTOM <= y <= PLAY_TOP

    def _add_stroke_point(self, x, y):
        point = (float(x), float(y))
        if not self.stroke or self.stroke[-1] != point:
            self.stroke.append(point)

    def _draw_background(self):
        shapes.Rectangle(0, 0, WIDTH, HEIGHT, color=(242, 246, 248)).draw()
        shapes.Rectangle(
            PLAY_LEFT,
            PLAY_BOTTOM,
            PLAY_RIGHT - PLAY_LEFT,
            PLAY_TOP - PLAY_BOTTOM,
            color=(255, 255, 255),
        ).draw()
        shapes.Line(
            PLAY_LEFT,
            PLAY_BOTTOM,
            PLAY_RIGHT,
            PLAY_BOTTOM,
            thickness=2,
            color=(207, 216, 220),
        ).draw()
        shapes.Line(
            PLAY_LEFT,
            PLAY_TOP,
            PLAY_RIGHT,
            PLAY_TOP,
            thickness=2,
            color=(207, 216, 220),
        ).draw()

    def _draw_sequence_hint(self):
        total_width = (
            len(self.sequence) * SEQUENCE_SLOT_SIZE
            + (len(self.sequence) - 1) * SEQUENCE_SLOT_GAP
        )
        start_x = (WIDTH - total_width) / 2
        y = HEIGHT - 124

        for index, gesture in enumerate(self.sequence):
            x = start_x + index * (SEQUENCE_SLOT_SIZE + SEQUENCE_SLOT_GAP)
            center_x = x + SEQUENCE_SLOT_SIZE / 2
            center_y = y + SEQUENCE_SLOT_SIZE / 2

            if index < self.sequence_index:
                fill = (218, 241, 225)
                border = (67, 160, 71)
                icon = (46, 125, 50)
            elif index == self.sequence_index:
                fill = (222, 238, 252)
                border = (30, 136, 229)
                icon = (25, 118, 210)
            else:
                fill = (255, 255, 255)
                border = (189, 199, 208)
                icon = (96, 111, 125)

            shapes.Rectangle(x, y, SEQUENCE_SLOT_SIZE, SEQUENCE_SLOT_SIZE, color=fill).draw()
            self._draw_box_border(x, y, SEQUENCE_SLOT_SIZE, SEQUENCE_SLOT_SIZE, border)
            self._draw_gesture_icon(gesture, center_x, center_y, icon)

            if index < len(self.sequence) - 1:
                line_y = y + SEQUENCE_SLOT_SIZE / 2
                shapes.Line(
                    x + SEQUENCE_SLOT_SIZE + 4,
                    line_y,
                    x + SEQUENCE_SLOT_SIZE + SEQUENCE_SLOT_GAP - 4,
                    line_y,
                    thickness=2,
                    color=(174, 184, 194),
                ).draw()

    def _draw_box_border(self, x, y, width, height, color):
        shapes.Line(x, y, x + width, y, thickness=2, color=color).draw()
        shapes.Line(x, y + height, x + width, y + height, thickness=2, color=color).draw()
        shapes.Line(x, y, x, y + height, thickness=2, color=color).draw()
        shapes.Line(x + width, y, x + width, y + height, thickness=2, color=color).draw()

    def _draw_gesture_icon(self, gesture, center_x, center_y, color):
        if gesture == "rectangle":
            self._draw_box_border(center_x - 13, center_y - 9, 26, 18, color)
        elif gesture == "circle":
            shapes.Circle(center_x, center_y, 13, color=color).draw()
            shapes.Circle(center_x, center_y, 9, color=(255, 255, 255)).draw()
        elif gesture == "check":
            shapes.Line(
                center_x - 14,
                center_y,
                center_x - 4,
                center_y - 10,
                thickness=4,
                color=color,
            ).draw()
            shapes.Line(
                center_x - 4,
                center_y - 10,
                center_x + 15,
                center_y + 13,
                thickness=4,
                color=color,
            ).draw()

    def _draw_stroke(self):
        if len(self.stroke) < 2:
            return
        for start, end in zip(self.stroke, self.stroke[1:]):
            shapes.Line(
                start[0],
                start[1],
                end[0],
                end[1],
                thickness=4,
                color=(0, 121, 107),
            ).draw()


def main():
    ShapeTrainer()
    pyglet.app.run()


if __name__ == "__main__":
    main()
