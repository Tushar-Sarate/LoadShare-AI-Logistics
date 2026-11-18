from tests.conftest import random_pincode


def test_partner_sees_and_accepts_nearby_order(
    client, make_customer, make_partner, order_payload
):
    pin = random_pincode()
    customer = make_customer(pin)
    partner = make_partner(pin)
    order = client.post("/orders/", headers=customer, json=order_payload(pin)).json()

    listed = client.get("/orders/available", headers=partner)
    assert listed.status_code == 200
    assert order["id"] in [o["id"] for o in listed.json()]

    r = client.post(f"/orders/{order['id']}/accept", headers=partner)
    assert r.status_code == 200
    assert r.json()["order_status"] == "Assigned"


def test_second_partner_cannot_take_same_order(
    client, make_customer, make_partner, order_payload
):
    pin = random_pincode()
    customer = make_customer(pin)
    first = make_partner(pin)
    second = make_partner(pin)
    order = client.post("/orders/", headers=customer, json=order_payload(pin)).json()

    assert client.post(f"/orders/{order['id']}/accept", headers=first).status_code == 200
    assert client.post(f"/orders/{order['id']}/accept", headers=second).status_code == 400


def test_far_partner_cannot_accept(client, make_customer, make_partner, order_payload):
    customer = make_customer("411047")          # Pune
    far_partner = make_partner("500001")        # Hyderabad
    order = client.post("/orders/", headers=customer, json=order_payload("411047")).json()

    listed = client.get("/orders/available", headers=far_partner).json()
    assert order["id"] not in [o["id"] for o in listed]

    assert client.post(f"/orders/{order['id']}/accept", headers=far_partner).status_code == 400


def test_customer_cannot_use_partner_routes(client, make_customer):
    headers = make_customer()
    assert client.get("/orders/available", headers=headers).status_code == 403