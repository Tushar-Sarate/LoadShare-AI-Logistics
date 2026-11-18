import random

from app.services.eta_service import predict_eta
from app.services.geo_service import coords_for, haversine_km


def test_haversine_known_distance():
    # Pune to Mumbai is roughly 120 km in a straight line
    km = haversine_km(18.5204, 73.8567, 19.0760, 72.8777)
    assert 110 < km < 130


def test_same_pincode_same_coordinates():
    assert coords_for("Pune", "411040") == coords_for("pune", "411040")
    assert coords_for("Pune", "411040") != coords_for("Pune", "411041")


def test_eta_grows_with_distance():
    assert predict_eta(20, 3) > predict_eta(1, 3)


def test_nearest_partner_is_assigned(
    client, make_customer, make_partner, admin_headers, order_payload
):
    near_pin = "411" + str(random.randint(100, 999))
    far_pin = "411" + str(random.randint(100, 999))
    while far_pin == near_pin:
        far_pin = "411" + str(random.randint(100, 999))

    customer = make_customer(near_pin)
    far_partner = make_partner(far_pin)
    near_partner = make_partner(near_pin)

    near_id = client.get("/partners/profile", headers=near_partner).json()["id"]

    order = client.post(
        "/orders/", headers=customer, json=order_payload(near_pin)
    ).json()

    r = client.post(f"/orders/{order['id']}/assign", headers=admin_headers)

    assert r.status_code == 200
    assert r.json()["delivery_partner_id"] == near_id