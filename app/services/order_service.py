from decimal import Decimal, ROUND_HALF_UP

from app.models.order import OrderStatus

# Food delivery: base fee covers the first km, then a rate per extra km
FOOD_BASE_FEE = Decimal("20")
FOOD_FREE_KM = Decimal("2")
FOOD_PER_KM = Decimal("7")

# Parcel delivery
PARCEL_BASE_FEE = Decimal("30")
PARCEL_FREE_KM = Decimal("2")
PARCEL_PER_KM = Decimal("9")
PARCEL_PER_KG = Decimal("5")


def _extra_km(distance_km, free_km: Decimal) -> Decimal:
    return max(Decimal("0"), Decimal(str(distance_km)) - free_km)


def _rupees(value: Decimal) -> Decimal:
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def food_delivery_fee(distance_km) -> Decimal:
    """Rs 20 for the first 2 km, then Rs 7 per extra km."""
    return _rupees(FOOD_BASE_FEE + _extra_km(distance_km, FOOD_FREE_KM) * FOOD_PER_KM)


def calculate_charge(weight_kg, distance_km) -> Decimal:
    """Parcel: Rs 30 for the first 2 km, Rs 9 per extra km, Rs 5 per kg."""
    charge = (
        PARCEL_BASE_FEE
        + _extra_km(distance_km, PARCEL_FREE_KM) * PARCEL_PER_KM
        + Decimal(str(weight_kg)) * PARCEL_PER_KG
    )
    return _rupees(charge)


ALLOWED_TRANSITIONS = {
    OrderStatus.pending: {OrderStatus.assigned, OrderStatus.cancelled},
    OrderStatus.assigned: {OrderStatus.picked_up, OrderStatus.cancelled},
    OrderStatus.picked_up: {OrderStatus.in_transit},
    OrderStatus.in_transit: {OrderStatus.delivered},
    OrderStatus.delivered: set(),
    OrderStatus.cancelled: set(),
}