import math

# City centres (latitude, longitude)
CITY_CENTERS = {
    "pune": (18.5204, 73.8567),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
    "bangalore": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873),
    "lucknow": (26.8467, 80.9462),
    "chandigarh": (30.7333, 76.7794),
    "kochi": (9.9312, 76.2673),
    "goa": (15.4909, 73.8278),
    "indore": (22.7196, 75.8577),
}

ALIASES = {
    "bengaluru": "bangalore",
    "panaji": "goa",
    "new delhi": "delhi",
    "bombay": "mumbai",
    "calcutta": "kolkata",
    "madras": "chennai",
    "cochin": "kochi",
    "poona": "pune",
}

# First 3 digits of an Indian pincode -> city
PINCODE_PREFIX = {
    "411": "pune", "400": "mumbai", "110": "delhi", "560": "bangalore",
    "500": "hyderabad", "600": "chennai", "700": "kolkata", "380": "ahmedabad",
    "302": "jaipur", "226": "lucknow", "160": "chandigarh", "682": "kochi",
    "403": "goa", "452": "indore",
}

INDIA_CENTER = (20.5937, 78.9629)

# Limits (km)
MAX_ASSIGN_KM = 20.0
MAX_DELIVERY_KM = 25.0

# Spread of pincodes around a city centre, in degrees
SPREAD = 0.2


def coords_for(city, pincode):
    """Approximate coordinates from city and pincode.

    This is NOT real geocoding. It places a pincode at a stable point near its
    city centre, so distances are consistent. A real system would call a
    geocoding API (Google Maps, Mapbox, OpenStreetMap Nominatim).
    """
    pin = str(pincode or "").strip()

    key = PINCODE_PREFIX.get(pin[:3])
    if key is None:
        key = (city or "").strip().lower()
    key = ALIASES.get(key, key)

    lat, lng = CITY_CENTERS.get(key, INDIA_CENTER)

    if pin.isdigit() and len(pin) == 6:
        p = int(pin)
        lat += ((p % 1000) / 999 - 0.5) * SPREAD
        lng += (((p // 1000) % 1000) / 999 - 0.5) * SPREAD

    return round(lat, 6), round(lng, 6)


def haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def register_geo(model):
    """Fill latitude and longitude automatically whenever a row is saved."""
    from sqlalchemy import event

    def fill(mapper, connection, target):
        target.latitude, target.longitude = coords_for(
            getattr(target, "city", None), getattr(target, "pincode", None)
        )

    event.listen(model, "before_insert", fill)
    event.listen(model, "before_update", fill)