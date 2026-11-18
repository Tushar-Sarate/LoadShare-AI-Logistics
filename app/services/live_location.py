import time

# partner_id -> last known position (kept in memory, one server only)
_locations = {}


def set_location(partner_id, lat, lng, accuracy=None, simulated=False):
    _locations[partner_id] = {
        "lat": lat,
        "lng": lng,
        "accuracy": accuracy,
        "simulated": simulated,
        "ts": time.time(),
    }


def get_location(partner_id, max_age=None):
    loc = _locations.get(partner_id)

    if not loc:
        return None

    age = time.time() - loc["ts"]

    if max_age is not None and age > max_age:
        return None

    return {**loc, "age_seconds": round(age)}