from datetime import datetime
from pathlib import Path

import joblib

MODEL_PATH = Path("ml/eta_model.joblib")
_model = None
_loaded = False


def _load():
    global _model, _loaded
    if not _loaded:
        _loaded = True
        if MODEL_PATH.exists():
            _model = joblib.load(MODEL_PATH)
    return _model


def predict_eta(distance_km: float, items_count: int = 0, when: datetime = None) -> int:
    """Estimated delivery time in minutes."""
    when = when or datetime.now()
    model = _load()

    if model is not None:
        features = [[float(distance_km), when.hour, when.weekday(), int(items_count)]]
        minutes = float(model.predict(features)[0])
    else:
        # Fallback formula if the model file is missing
        prep = 5 if items_count == 0 else 8 + 1.8 * items_count
        minutes = prep + 5 + float(distance_km) / 25 * 60

    return max(10, round(minutes))