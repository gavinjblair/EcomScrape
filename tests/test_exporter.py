import json
from dataclasses import asdict
from datetime import datetime

import pandas as pd

from ecomscrape.exporter import export_dataframe, write_latest_json
from ecomscrape.models import Product


def test_export_creates_files(tmp_path):
    # Verify export writes chosen formats and files are present.
    products = [
        Product(name="Book 1", price_current=10.0, availability="in_stock"),
        Product(name="Book 2", price_current=5.5, availability="out_of_stock"),
    ]
    df = pd.DataFrame([asdict(p) for p in products])

    paths = export_dataframe(df, formats=["csv", "json"], output_dir=tmp_path)

    assert "csv" in paths and paths["csv"].exists()
    assert "json" in paths and paths["json"].exists()


def test_write_latest_json_uses_object_contract(tmp_path):
    products = [
        Product(name="Book 1", price_current=10.0, availability="in_stock"),
        Product(name="Book 2", price_current=5.5, availability="out_of_stock"),
    ]
    df = pd.DataFrame([asdict(p) for p in products])

    latest_path = write_latest_json(df, output_dir=tmp_path)

    assert latest_path is not None and latest_path.exists()
    payload = json.loads(latest_path.read_text(encoding="utf-8"))
    assert list(payload.keys()) == ["products", "generated_at"]
    assert len(payload["products"]) == 2
    assert payload["products"][0]["name"] == "Book 1"
    assert datetime.fromisoformat(payload["generated_at"])
