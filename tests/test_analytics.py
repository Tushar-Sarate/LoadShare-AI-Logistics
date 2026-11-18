from app.services.demand_service import base_pattern, forecast_next_hours


def test_dinner_is_busier_than_night():
    assert base_pattern(20, 2) > base_pattern(4, 2)


def test_forecast_has_24_hours():
    rows = forecast_next_hours(24)
    assert len(rows) == 24
    assert all(0 <= r["index"] <= 100 for r in rows)


def test_analytics_is_admin_only(client, make_customer, admin_headers):
    assert client.get("/analytics/summary", headers=make_customer()).status_code == 403

    r = client.get("/analytics/summary", headers=admin_headers)
    assert r.status_code == 200
    assert "totals" in r.json()

    r = client.get("/analytics/demand", headers=admin_headers)
    assert r.status_code == 200
    assert len(r.json()["forecast"]) == 24