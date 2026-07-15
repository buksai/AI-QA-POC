"""Automated regression tests for the shop API."""
from shop_api import app


def test_create_order_returns_201_with_total():
    client = app.test_client()
    resp = client.post("/api/orders", json={"userId": 1, "items": [{"sku": "A100", "qty": 2}]})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["total"] == 39.98
    assert body["status"] == "created"
    assert body["itemCount"] == 2


def test_get_order_roundtrip():
    client = app.test_client()
    created = client.post("/api/orders", json={"userId": 2, "items": [{"sku": "B200", "qty": 1}]}).get_json()
    resp = client.get("/api/orders/" + created["orderId"])
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 19.99
    assert body["status"] == "created"
