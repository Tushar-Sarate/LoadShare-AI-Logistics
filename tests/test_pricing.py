import pytest

from app.services.order_service import calculate_charge, food_delivery_fee


def test_food_fee_first_two_km_is_flat():
    assert food_delivery_fee(0) == 20
    assert food_delivery_fee(1) == 20
    assert food_delivery_fee(2) == 20


def test_food_fee_per_extra_km():
    assert food_delivery_fee(5) == 41     # 20 + 3 x 7
    assert food_delivery_fee(10) == 76    # 20 + 8 x 7


def test_parcel_charge_uses_distance_and_weight():
    assert calculate_charge(2, 0) == 40      # 30 + 2 x 5
    assert calculate_charge(2, 12) == 130    # 30 + 10 x 9 + 2 x 5


def test_cart_quote_matches_distance(client, make_customer):
    headers = make_customer()

    restaurants = client.get("/restaurants/", headers=headers).json()
    if not restaurants:
        pytest.skip("Run seed_food.py first")

    r = restaurants[0]

    # delivering to the restaurant's own pincode is 0 km
    q = client.get(
        "/food-orders/quote",
        headers=headers,
        params={"restaurant_id": r["id"], "delivery_pincode": r["pincode"]},
    ).json()

    assert q["distance_km"] == 0
    assert q["delivery_fee"] == 20
    assert q["deliverable"] is True