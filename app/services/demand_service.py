import math
from datetime import datetime, timedelta
from pathlib import Path

import joblib

MODEL_PATH = Path("ml/demand_model.joblib")
_model = None
_loaded = False


def base_pattern(hour: int, dow: int) -> float:
    """Typical orders per hour for a mid-size city (synthetic rules).

    Breakfast bump around 9, lunch around 13, a bigger dinner peak around 20,
    quiet nights, busier weekends and Friday evenings.
    """

    def bump(h, centre, width, height):
        return height * math.exp(-((h - centre) ** 2) / (2 * width ** 2))

    value = 3 + bump(hour, 9, 1.2, 6) + bump(hour, 13, 1.4, 22) + bump(hour, 20, 1.8, 34)

    if hour < 7:
        value *= 0.2
    if dow >= 5:
        value *= 1.25 if hour >= 18 else 1.15
    if dow == 4 and hour >= 19:
        value *= 1.15

    return value


def _load():
    global _model, _loaded
    if not _loaded:
        _loaded = True
        if MODEL_PATH.exists():
            _model = joblib.load(MODEL_PATH)
    return _model


def _predict_many(pairs):
    """pairs: list of (hour, day_of_week)."""
    model = _load()

    if model is not None:
        values = model.predict([[h, d] for h, d in pairs])
        return [max(0.0, float(v)) for v in values]

    return [base_pattern(h, d) for h, d in pairs]


def _label(t: datetime) -> str:
    hour12 = t.hour % 12 or 12
    suffix = "AM" if t.hour < 12 else "PM"
    return f"{t:%a} {hour12}{suffix}"


def forecast_next_hours(hours: int = 24):
    """Expected demand for the next N hours, plus an index from 0 to 100
    relative to the busiest hour of the whole week."""

    now = datetime.now()

    weekly = _predict_many([(h, d) for d in range(7) for h in range(24)])
    weekly_max = max(weekly) or 1.0

    times = [now + timedelta(hours=i) for i in range(hours)]
    expected = _predict_many([(t.hour, t.weekday()) for t in times])

    return [
        {
            "label": _label(t),
            "hour": t.hour,
            "expected": round(e, 1),
            "index": round(e / weekly_max * 100),
        }
        for t, e in zip(times, expected)
    ]