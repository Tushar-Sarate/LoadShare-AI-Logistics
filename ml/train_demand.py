"""Train the hourly demand model.

IMPORTANT: the training data is SYNTHETIC. It comes from the pattern rules in
app/services/demand_service.py plus Poisson noise and day-to-day variation.
A real system would train on historical order logs. Say this openly.
"""
import joblib
import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from app.services.demand_service import base_pattern


def make_data(weeks=60, seed=7):
    rng = np.random.default_rng(seed)
    X, y = [], []

    for _ in range(weeks):
        for dow in range(7):
            day_factor = rng.normal(1.0, 0.12)   # weather, events, etc.
            for hour in range(24):
                lam = max(base_pattern(hour, dow) * day_factor, 0.1)
                X.append([hour, dow])
                y.append(rng.poisson(lam))

    return np.array(X), np.array(y, dtype=float)


def main():
    X, y = make_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    models = {
        "Baseline (mean)": DummyRegressor(strategy="mean"),
        "Linear regression": LinearRegression(),
        "Gradient boosting": GradientBoostingRegressor(random_state=42),
    }

    results = {}
    print(f"{'Model':<20} {'MAE (orders/h)':>15} {'RMSE':>8}")
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, pred)
        rmse = mean_squared_error(y_test, pred) ** 0.5
        results[name] = (mae, model)
        print(f"{name:<20} {mae:>15.2f} {rmse:>8.2f}")

    candidates = {k: v for k, v in results.items() if not k.startswith("Baseline")}
    best_name = min(candidates, key=lambda k: candidates[k][0])

    joblib.dump(candidates[best_name][1], "ml/demand_model.joblib")
    print(f"\nSaved best model: {best_name} -> ml/demand_model.joblib")


if __name__ == "__main__":
    main()