# Assignment 6

Gesture recognition with the `$1` recognizer and small LSTM models.

## Files

- `recognizer.py`: `$1` recognizer and XML helpers.
- `gesture_input.py`: draw one gesture and see the result.
- `gesture_application.py`: a small gesture sequence game.
- `unistroke_gestures.ipynb`: LSTM comparison and `$1` baseline.
- `datasets/unistroke_test/`: copied test XML files for the notebook and demos.

## Setup

Python 3.11 is recommended because the notebook uses TensorFlow.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Basic recognizer:

```bash
python gesture_input.py
```

Gesture game:

```bash
python gesture_application.py
```

Notebook:

```bash
jupyter notebook unistroke_gestures.ipynb
```

To recreate the train/test split, keep the full XML logs in `xml_logs/`.
