import json

from fastapi.testclient import TestClient

from ecomscrape.api import create_app


def test_products_api_accepts_object_dataset(tmp_path):
    data_path = tmp_path / "latest_products.json"
    data_path.write_text(
        json.dumps(
            {
                "products": [
                    {"title": "Book 1", "price_current": 10.0, "category": "Books"},
                    {"title": "Book 2", "price_current": 25.0, "category": "SciFi"},
                ],
                "generated_at": "2026-03-12T20:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    client = TestClient(create_app(data_path=data_path))
    response = client.get("/api/products", params={"max_price": 15, "category": "books"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["products"][0]["title"] == "Book 1"
    assert payload["generated_at"] == "2026-03-12T20:00:00+00:00"


def test_products_api_accepts_legacy_array_dataset(tmp_path):
    data_path = tmp_path / "latest_products.json"
    data_path.write_text(
        json.dumps(
            [
                {"title": "Book 1", "price_current": 10.0, "category": "Books"},
                {"title": "Book 2", "price_current": 25.0, "category": "SciFi"},
            ]
        ),
        encoding="utf-8",
    )

    client = TestClient(create_app(data_path=data_path))
    response = client.get("/api/products", params={"min_price": 20})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["products"][0]["title"] == "Book 2"
    assert payload["generated_at"] is not None
