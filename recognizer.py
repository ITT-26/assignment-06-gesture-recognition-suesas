import math
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

NUM_POINTS = 64
SQUARE_SIZE = 250.0
HALF_DIAGONAL = 0.5 * math.sqrt(SQUARE_SIZE * SQUARE_SIZE * 2.0)
ANGLE_RANGE = math.radians(45.0)
ANGLE_PRECISION = math.radians(2.0)
PHI = 0.5 * (-1.0 + math.sqrt(5.0))

REQUIRED_GESTURES = (
    "rectangle",
    "circle",
    "check",
    "delete_mark",
    "pigtail",
)

GAME_GESTURES = ("rectangle", "circle", "check")

ALL_GESTURES = (
    "arrow",
    "caret",
    "check",
    "circle",
    "delete_mark",
    "left_curly_brace",
    "left_sq_bracket",
    "pigtail",
    "question_mark",
    "rectangle",
    "right_curly_brace",
    "right_sq_bracket",
    "star",
    "triangle",
    "v",
    "x",
)


def display_label(name):
    if name == "delete_mark":
        return "delete"
    return name.replace("_", " ")


def normalize_label(name):
    cleaned = name.strip().lower().replace("-", "_").replace(" ", "_")
    cleaned = re.sub(r"\d+$", "", cleaned)
    aliases = {"delete": "delete_mark", "delete_mark": "delete_mark"}
    if cleaned in aliases:
        return aliases[cleaned]
    if cleaned in ALL_GESTURES:
        return cleaned
    for gesture in sorted(ALL_GESTURES, key=len, reverse=True):
        if cleaned.endswith(f"_{gesture}"):
            return gesture
    return cleaned


def label_from_path(path):
    source = Path(path)
    stem_label = normalize_label(source.stem)
    if stem_label in ALL_GESTURES:
        return stem_label

    parent_label = normalize_label(source.parent.name)
    if parent_label in ALL_GESTURES:
        return parent_label

    return stem_label


def read_xml_points(path):
    root = ET.parse(path).getroot()
    points = []
    for element in root.findall("Point"):
        x = element.get("X")
        y = element.get("Y")
        if x is None or y is None:
            continue
        points.append((float(x), float(y)))
    return points


def iter_gesture_files(log_dir="xml_logs", labels=None):
    root = Path(log_dir)
    wanted = {normalize_label(label) for label in labels} if labels else None
    files = sorted(root.rglob("*.xml"))
    if wanted is None:
        return files
    return [path for path in files if label_from_path(path) in wanted]


def group_gesture_files(log_dir="xml_logs", labels=None):
    grouped = {}
    for path in iter_gesture_files(log_dir, labels):
        grouped.setdefault(label_from_path(path), []).append(path)
    return {label: sorted(paths) for label, paths in sorted(grouped.items())}


def create_test_dataset(
    log_dir="xml_logs",
    output_dir="datasets/unistroke_test",
    samples_per_class=10,
    labels=ALL_GESTURES,
    clean=True,
):
    grouped = group_gesture_files(log_dir, labels)
    output_root = Path(output_dir)
    selected = {}

    output_root.mkdir(parents=True, exist_ok=True)
    if clean:
        log_root = Path(log_dir).resolve()
        output_root_resolved = output_root.resolve()
        if log_root == output_root_resolved or log_root.is_relative_to(output_root_resolved):
            raise ValueError("output_dir must not be the log_dir or contain it when clean=True.")

        for stale_file in output_root.rglob("*.xml"):
            stale_file.unlink()
        for stale_dir in sorted(
            (path for path in output_root.rglob("*") if path.is_dir()),
            reverse=True,
        ):
            if not any(stale_dir.iterdir()):
                stale_dir.rmdir()

    for label in labels:
        files = grouped.get(label, [])
        if len(files) < samples_per_class:
            raise ValueError(
                f"Need {samples_per_class} samples for {label}, found {len(files)}."
            )

        label_dir = output_root / label
        label_dir.mkdir(parents=True, exist_ok=True)
        selected[label] = []

        for source in files[:samples_per_class]:
            subject, speed = source.parts[-3], source.parts[-2]
            destination = label_dir / f"{subject}_{speed}_{source.name}"
            shutil.copy2(source, destination)
            selected[label].append(destination)

    return selected


def path_length(points):
    return sum(distance(start, end) for start, end in zip(points, points[1:]))


def distance(first, second):
    return math.hypot(second[0] - first[0], second[1] - first[1])


def centroid(points):
    return (
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )


def resample(points, num_points=NUM_POINTS):
    if len(points) < 2:
        raise ValueError("Need at least two points to resample a gesture.")

    original = [tuple(point) for point in points]
    total_length = path_length(original)
    if total_length == 0:
        return [original[0]] * num_points

    interval = total_length / (num_points - 1)
    accumulated = 0.0
    next_target = interval
    new_points = [original[0]]
    previous = original[0]

    for current in original[1:]:
        segment_length = distance(previous, current)

        if segment_length == 0:
            previous = current
            continue

        while accumulated + segment_length >= next_target and len(new_points) < num_points:
            ratio = (next_target - accumulated) / segment_length
            next_point = (
                previous[0] + ratio * (current[0] - previous[0]),
                previous[1] + ratio * (current[1] - previous[1]),
            )
            new_points.append(next_point)
            next_target += interval

        accumulated += segment_length
        previous = current

    while len(new_points) < num_points:
        new_points.append(original[-1])

    return new_points[:num_points]


def indicative_angle(points):
    center = centroid(points)
    return math.atan2(center[1] - points[0][1], center[0] - points[0][0])


def rotate_by(points, radians):
    center = centroid(points)
    cos_value = math.cos(radians)
    sin_value = math.sin(radians)
    rotated = []

    for x, y in points:
        dx = x - center[0]
        dy = y - center[1]
        rotated.append(
            (
                dx * cos_value - dy * sin_value + center[0],
                dx * sin_value + dy * cos_value + center[1],
            )
        )

    return rotated


def bounding_box(points):
    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    min_y = min(point[1] for point in points)
    max_y = max(point[1] for point in points)
    return min_x, min_y, max_x - min_x, max_y - min_y


def scale_to_square(points, size=SQUARE_SIZE):
    min_x, min_y, width, height = bounding_box(points)
    scaled = []

    for x, y in points:
        scaled_x = (x - min_x) * (size / width) if width else 0.0
        scaled_y = (y - min_y) * (size / height) if height else 0.0
        scaled.append((scaled_x, scaled_y))

    return scaled


def translate_to_origin(points):
    center = centroid(points)
    return [(x - center[0], y - center[1]) for x, y in points]


def normalize_points(points):
    prepared = resample(points, NUM_POINTS)
    prepared = rotate_by(prepared, -indicative_angle(prepared))
    prepared = scale_to_square(prepared, SQUARE_SIZE)
    prepared = translate_to_origin(prepared)
    return tuple(prepared)


def path_distance(candidate, template):
    return sum(distance(first, second) for first, second in zip(candidate, template)) / len(candidate)


def distance_at_angle(points, template, radians):
    rotated = rotate_by(points, radians)
    return path_distance(rotated, template)


def distance_at_best_angle(
    points,
    template,
    angle_range=ANGLE_RANGE,
    angle_precision=ANGLE_PRECISION,
):
    lower_bound = -angle_range
    upper_bound = angle_range
    x1 = PHI * lower_bound + (1.0 - PHI) * upper_bound
    f1 = distance_at_angle(points, template, x1)
    x2 = (1.0 - PHI) * lower_bound + PHI * upper_bound
    f2 = distance_at_angle(points, template, x2)

    while abs(upper_bound - lower_bound) > angle_precision:
        if f1 < f2:
            upper_bound = x2
            x2 = x1
            f2 = f1
            x1 = PHI * lower_bound + (1.0 - PHI) * upper_bound
            f1 = distance_at_angle(points, template, x1)
        else:
            lower_bound = x1
            x1 = x2
            f1 = f2
            x2 = (1.0 - PHI) * lower_bound + PHI * upper_bound
            f2 = distance_at_angle(points, template, x2)

    return min(f1, f2)


class DollarRecognizer:
    def __init__(self):
        self.templates = []

    def add_template(self, name, points):
        if len(points) < 2:
            return
        self.templates.append((normalize_label(name), normalize_points(points)))

    def recognize(self, points):
        if len(points) < 2:
            raise ValueError("Longer stroke.")
        if not self.templates:
            raise ValueError("No templates loaded.")

        candidate = normalize_points(points)
        best_template = self.templates[0]
        best_distance = distance_at_best_angle(candidate, best_template[1])

        for template in self.templates[1:]:
            template_distance = distance_at_best_angle(candidate, template[1])
            if template_distance < best_distance:
                best_distance = template_distance
                best_template = template

        score = max(0.0, 1.0 - best_distance / HALF_DIAGONAL)
        return best_template[0], score


def build_recognizer_from_logs(
    log_dir="xml_logs",
    labels=REQUIRED_GESTURES,
    templates_per_label=3,
    include_reversed=False,
):
    recognizer = DollarRecognizer()
    grouped = group_gesture_files(log_dir, labels)
    for label in labels:
        files = grouped.get(label, [])
        if len(files) < templates_per_label:
            raise ValueError(
                f"Need {templates_per_label} templates for {label}, found {len(files)} "
                f"in {Path(log_dir)}."
            )
        for path in files[:templates_per_label]:
            points = read_xml_points(path)
            recognizer.add_template(label, points)
            if include_reversed:
                recognizer.add_template(label, list(reversed(points)))
    return recognizer


if __name__ == "__main__":
    grouped_files = group_gesture_files("xml_logs", REQUIRED_GESTURES)
    for gesture_name, paths in grouped_files.items():
        print(f"{display_label(gesture_name):12s} {len(paths):3d} examples")
