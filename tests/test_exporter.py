from dataclasses import asdict

import pandas as pd

from ecomscrape.exporter import export_dataframe
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
