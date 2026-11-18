def test_tracking_history(client, make_customer, make_partner, admin_headers, order_payload):
    pincode = "600" + "001"
    customer = make_customer(pincode)
    make_partner(pincode)

    order = client.post("/orders/", headers=customer, json=order_payload(pincode)).json()
    client.post(f"/orders/{order['id']}/assign", headers=admin_headers)

    r = client.get(f"/tracking/{order['id']}", headers=customer)
    assert r.status_code == 200

    statuses = [item["status"] for item in r.json()]
    assert statuses == ["Pending", "Assigned"]


def test_other_customer_cannot_view_tracking(client, make_customer, order_payload):
    owner = make_customer()
    other = make_customer()

    order = client.post("/orders/", headers=owner, json=order_payload("411001")).json()

    r = client.get(f"/tracking/{order['id']}", headers=other)
    assert r.status_code == 403