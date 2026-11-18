import pytest

from app.database import SessionLocal
from app.models.order import Order, OrderStatus


def _set_order(order_id, **fields):
    """Change an order directly in the database (used to set up test cases)."""
    db = SessionLocal()
    try:
        order = db.get(Order, order_id)
        for key, value in fields.items():
            setattr(order, key, value)
        db.commit()
    finally:
        db.close()


def _assigned_order(client, customer, partner, pincode, order_payload):
    partner_id = client.get("/partners/profile", headers=partner).json()["id"]
    order = client.post("/orders/", headers=customer, json=order_payload(pincode)).json()
    _set_order(order["id"], delivery_partner_id=partner_id, order_status=OrderStatus.assigned)
    return order


def test_partner_location_reaches_customer(client, make_customer, make_partner, order_payload):
    customer = make_customer("411045")
    partner = make_partner("411045")
    order = _assigned_order(client, customer, partner, "411045", order_payload)

    r = client.post("/live/location", headers=partner, json={"lat": 18.52, "lng": 73.86})
    assert r.status_code == 200
    assert r.json()["orders"] >= 1

    r = client.get(f"/live/order/{order['id']}", headers=customer)
    assert r.status_code == 200
    assert r.json()["location"]["lat"] == 18.52


def test_location_hidden_from_other_customer(client, make_customer, make_partner, order_payload):
    owner = make_customer("411046")
    other = make_customer("411046")
    partner = make_partner("411046")
    order = _assigned_order(client, owner, partner, "411046", order_payload)

    assert client.get(f"/live/order/{order['id']}", headers=other).status_code == 403


def test_bad_coordinates_rejected(client, make_partner):
    r = client.post("/live/location", headers=make_partner(), json={"lat": 200, "lng": 10})
    assert r.status_code == 422


def test_customer_cannot_send_location(client, make_customer):
    r = client.post("/live/location", headers=make_customer(), json={"lat": 18.5, "lng": 73.8})
    assert r.status_code == 403


def test_review_flow(client, make_customer):
    headers = make_customer()

    restaurants = client.get("/restaurants/", headers=headers).json()
    if not restaurants:
        pytest.skip("Run seed_food.py first")

    restaurant = restaurants[0]
    menu = client.get(f"/restaurants/{restaurant['id']}/menu", headers=headers).json()

    placed = client.post("/food-orders/", headers=headers, json={
        "restaurant_id": restaurant["id"],
        "items": [{"menu_item_id": menu[0]["id"], "quantity": 1}],
        "delivery_address": "Test address, Pune",
        "delivery_pincode": restaurant["pincode"],
    })
    assert placed.status_code == 201
    order_id = placed.json()["id"]

    # cannot rate before the order is delivered
    r = client.post("/reviews/", headers=headers, json={"order_id": order_id, "rating": 5})
    assert r.status_code == 400

    _set_order(order_id, order_status=OrderStatus.delivered)

    r = client.post("/reviews/", headers=headers,
                    json={"order_id": order_id, "rating": 4, "comment": "Tasty"})
    assert r.status_code == 201

    # only one review per order
    r = client.post("/reviews/", headers=headers, json={"order_id": order_id, "rating": 5})
    assert r.status_code == 400

    assert {"order_id": order_id, "rating": 4} in client.get("/reviews/mine", headers=headers).json()

    listed = client.get("/restaurants/", headers=headers).json()
    updated = next(x for x in listed if x["id"] == restaurant["id"])
    assert updated["rating_count"] >= 1


def test_insights_admin_only(client, make_customer, admin_headers):
    assert client.get("/analytics/insights", headers=make_customer()).status_code == 403

    r = client.get("/analytics/insights", headers=admin_headers)
    assert r.status_code == 200

    data = r.json()
    for key in ["revenue", "retention", "restaurants", "peak_hours",
                "partners", "cancellation", "demand_compare"]:
        assert key in data

    assert len(data["revenue"]["daily"]) == 30
    assert len(data["revenue"]["weekly"]) == 12
    assert len(data["revenue"]["monthly"]) == 12
    assert len(data["demand_compare"]["actual_share"]) == 24


def test_public_home_data(client):
    assert client.get("/public/restaurants").status_code == 200
    assert "restaurants" in client.get("/public/stats").json()