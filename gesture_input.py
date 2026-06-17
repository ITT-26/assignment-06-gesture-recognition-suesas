from pathlib import Path

import pyglet

pyglet.options["dpi_scaling"] = "stretch"

from pyglet import shapes

from recognizer import (
    REQUIRED_GESTURES,
    build_recognizer_from_logs,
    display_label,
)

WIDTH = 900
HEIGHT = 620
CANVAS_TOP = HEIGHT - 90
CANVAS_BOTTOM = 45
PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "datasets" / "unistroke_test"
TEMPLATES_PER_GESTURE = 10


class GestureInputWindow(pyglet.window.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, "Assignment 6 Gestures", resizable=False)
        self.batch = pyglet.graphics.Batch()
        self.stroke = []
        self.is_drawing = False
        self.status = "Draw, then release."
        self.result = "Ready"
        self.recognizer = build_recognizer_from_logs(
            LOG_DIR,
            REQUIRED_GESTURES,
            templates_per_label=TEMPLATES_PER_GESTURE,
            include_reversed=True,
        )

        self.title_label = pyglet.text.Label(
            "Gestures",
            x=24,
            y=HEIGHT - 34,
            font_size=22,
            color=(25, 31, 39, 255),
            batch=self.batch,
        )
        gestures = ", ".join(display_label(name) for name in REQUIRED_GESTURES)
        self.hint_label = pyglet.text.Label(
            f"Try: {gestures}. C clears.",
            x=24,
            y=HEIGHT - 64,
            font_size=12,
            color=(76, 86, 99, 255),
            batch=self.batch,
        )
        self.status_label = pyglet.text.Label(
            self.status,
            x=24,
            y=18,
            font_size=12,
            color=(76, 86, 99, 255),
            batch=self.batch,
        )
        self.result_label = pyglet.text.Label(
            self.result,
            x=WIDTH - 24,
            y=HEIGHT - 46,
            anchor_x="right",
            font_size=18,
            color=(25, 31, 39, 255),
            batch=self.batch,
        )

    def on_draw(self):
        self.clear()
        self._draw_background()
        self.status_label.text = self.status
        self.result_label.text = self.result
        self.batch.draw()
        self._draw_stroke()

    def on_mouse_press(self, x, y, button, modifiers):
        if button != pyglet.window.mouse.LEFT or not self._inside_canvas(y):
            return
        self.stroke = []
        self.is_drawing = True
        self._add_stroke_point(x, y)
        self.status = "Drawing"

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not buttons & pyglet.window.mouse.LEFT:
            return
        if not self.is_drawing and self._inside_canvas(y):
            self.stroke = []
            self.is_drawing = True
            self.status = "Drawing"
        if self.is_drawing:
            self._add_stroke_point(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        if button != pyglet.window.mouse.LEFT or not self.is_drawing:
            return
        self.is_drawing = False
        self._add_stroke_point(x, y)
        self._recognize_current_stroke()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.C:
            self.is_drawing = False
            self.stroke.clear()
            self.result = "Ready"
            self.status = "Cleared."

    def _inside_canvas(self, y):
        return CANVAS_BOTTOM <= y <= CANVAS_TOP

    def _add_stroke_point(self, x, y):
        point = (float(x), float(y))
        if not self.stroke or self.stroke[-1] != point:
            self.stroke.append(point)

    def _recognize_current_stroke(self):
        if len(self.stroke) < 3:
            self.result = "Too short"
            self.status = "Longer gesture."
            return

        try:
            name, score = self.recognizer.recognize(self.stroke)
        except ValueError as exc:
            self.result = "No match"
            self.status = str(exc)
        else:
            self.result = f"{display_label(name)} ({score:.2f})"
            self.status = "Draw again. C clears."

    def _draw_background(self):
        shapes.Rectangle(0, 0, WIDTH, HEIGHT, color=(244, 247, 250)).draw()
        shapes.Rectangle(
            18,
            CANVAS_BOTTOM,
            WIDTH - 36,
            CANVAS_TOP - CANVAS_BOTTOM,
            color=(255, 255, 255),
        ).draw()
        shapes.Line(
            18,
            CANVAS_BOTTOM,
            WIDTH - 18,
            CANVAS_BOTTOM,
            thickness=2,
            color=(210, 216, 224),
        ).draw()
        shapes.Line(
            18,
            CANVAS_TOP,
            WIDTH - 18,
            CANVAS_TOP,
            thickness=2,
            color=(210, 216, 224),
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
                color=(25, 118, 210),
            ).draw()


def main():
    GestureInputWindow()
    pyglet.app.run()


if __name__ == "__main__":
    main()
