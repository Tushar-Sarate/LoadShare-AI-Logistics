"""Train the delivery-time (ETA) model.

IMPORTANT: the training data is SYNTHETIC. It is generated from realistic rules
(preparation time, rush-hour speed, noise). A real system would train on
historical delivery logs. Say this openly in an interview.
"""
import joblib
import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split


def make_data(n=6000, seed=42):
    rng = np.random.default_rng(seed)

    distance = rng.gamma(2.0, 3.0, n).clip(0.3, 25)       # km
    hour = rng.integers(8, 24, n)                          # 8 to 23
    dow = rng.integers(0, 7, n)                            # 0 = Monday
    items = np.where(rng.random(n) < 0.25, 0, rng.integers(1, 11, n))  # 0 = parcel

    rush = ((hour >= 12) & (hour <= 14)) | ((hour >= 18) & (hour <= 21))
    speed = np.where(rush, 17.0, 27.0)                     # km/h
    speed = np.where(dow >= 5, speed * 0.93, speed)        # slower on weekends

    prep = np.where(items == 0, 5.0, 8.0 + 1.8 * items)    # kitchen time
    prep = prep + np.where(rush & (items > 0), 5.0, 0.0)   # busy kitchens
    pickup_wait = rng.uniform(2, 8, n)

    eta = prep + pickup_wait + distance / speed * 60 + rng.normal(0, 3, n)

    X = np.column_stack([distance, hour, dow, items])
    y = np.maximum(eta, 8)
    return X, y


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
    print(f"{'Model':<20} {'MAE (min)':>10} {'RMSE (min)':>11}")
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, pred)
        rmse = mean_squared_error(y_test, pred) ** 0.5
        results[name] = (mae, model)
        print(f"{name:<20} {mae:>10.2f} {rmse:>11.2f}")

    candidates = {k: v for k, v in results.items() if not k.startswith("Baseline")}
    best_name = min(candidates, key=lambda k: candidates[k][0])
    best = candidates[best_name][1]

    joblib.dump(best, "ml/eta_model.joblib")
    print(f"\nSaved best model: {best_name} -> ml/eta_model.joblib")

    if hasattr(best, "feature_importances_"):
        names = ["distance_km", "hour", "day_of_week", "items"]
        print("\nFeature importance:")
        for n, imp in sorted(zip(names, best.feature_importances_), key=lambda t: -t[1]):
            print(f"  {n:<12} {imp:.2f}")


if __name__ == "__main__":
    main()