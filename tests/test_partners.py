def test_partner_profile(client, make_partner):
    headers = make_partner()

    r = client.get("/partners/profile", headers=headers)
    assert r.status_code == 200
    assert r.json()["is_available"] is True


def test_customer_cannot_create_partner_profile(client, make_customer):
    headers = make_customer()

    r = client.post("/partners/profile", headers=headers, json={
        "phone": "9876543210",
        "vehicle_type": "Bike",
        "vehicle_number": "MH12AB1234",
        "city": "Pune",
        "pincode": "411001",
    })
    assert r.status_code == 403