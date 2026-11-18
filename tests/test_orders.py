from app.services.order_service import calculate_charge
from tests.conftest import random_pincode


def test_create_order_and_charge(client, make_customer, order_payload):
    headers = make_customer()

    r = client.post("/orders/", headers=headers, json=order_payload("411001"))
    assert r.status_code == 201

    data = r.json()
    assert data["order_status"] == "Pending"
    # same pincode = 0 km: Rs 30 base + 2 kg x Rs 5
    assert float(data["delivery_charge"]) == 40.0


def test_longer_trip_costs_more(client, make_customer, order_payload):
    headers = make_customer()
    payload = order_payload("411001")
    payload["delivery_pincode"] = "411999"   # about 13 km away in Pune

    r = client.post("/orders/", headers=headers, json=payload)
    assert r.status_code == 201

    data = r.json()
    km = float(data["distance_km"])

    assert km > 10
    assert float(data["delivery_charge"]) == float(calculate_charge(2, km))
    assert float(data["delivery_charge"]) > 100


def test_full_delivery_flow(client, make_customer, make_partner, admin_headers, order_payload):
    pincode = random_pincode()
    customer = make_customer(pincode)
    partner = make_partner(pincode)

    order = client.post("/orders/", headers=customer, json=order_payload(pincode)).json()
    order_id = order["id"]

    r = client.post(f"/orders/{order_id}/assign", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["order_status"] == "Assigned"

    for new_status in ["Picked Up", "In Transit", "Delivered"]:
        r = client.patch(
            f"/orders/{order_id}/status",
            headers=partner,
            json={"order_status": new_status},
        )
        assert r.status_code == 200
        assert r.json()["order_status"] == new_status


def test_cannot_skip_status(client, make_customer, make_partner, admin_headers, order_payload):
    pincode = random_pincode()
    customer = make_customer(pincode)
    partner = make_partner(pincode)

    order = client.post("/orders/", headers=customer, json=order_payload(pincode)).json()
    client.post(f"/orders/{order['id']}/assign", headers=admin_headers)

    r = client.patch(
        f"/orders/{order['id']}/status",
        headers=partner,
        json={"order_status": "Delivered"},
    )
    assert r.status_code == 400


def test_customer_cannot_assign(client, make_customer, order_payload):
    headers = make_customer()
    order = client.post("/orders/", headers=headers, json=order_payload("411001")).json()

    r = client.post(f"/orders/{order['id']}/assign", headers=headers)
    assert r.status_code == 403