from ecomscrape.cleaner import (
    _clean_price,
    _clean_rating,
    _standardise_availability,
    clean_products,
)
from ecomscrape.config import CleaningConfig


def test_clean_price_and_rating_and_availability():
    # Spot-check helpers for price, rating, and availability normalisation.
    rating_map = {"three": 3, "five": 5}
    availability_map = {"in stock": "in_stock"}

    assert _clean_price("Â£1,234.50") == 1234.5
    assert _clean_rating(["star-rating", "Three"], rating_map) == 3
    assert _standardise_availability("In stock ", availability_map) == "in_stock"
    assert _standardise_availability("in_stock", availability_map) == "in_stock"


def test_clean_products_creates_products_and_dataframe():
    # Ensure clean_products returns both Product objects and a populated DataFrame.
    records = [
        {"name": "Book 1", "price_current": "Â£10.00", "rating": "Five", "availability": "In stock"},
        {"name": "Book 2", "price_current": "Â£5.50", "rating": "Three", "availability": "Out of stock"},
    ]
    cleaning = CleaningConfig(
        rating_words={"five": 5, "three": 3},
        availability_map={"out of stock": "out_of_stock", "in stock": "in_stock"},
    )

    products, df = clean_products(records, currency="GBP", cleaning=cleaning)

    assert len(products) == 2
    assert len(df) == 2
    assert df.loc[0, "price_current"] == 10.0
    assert df.loc[1, "availability"] == "out_of_stock"


def test_clean_products_repairs_mojibake_and_preserves_existing_ids():
    records = [
        {
            "id": "book-1",
            "name": "FranÃ§ais Title",
            "price_current": "Â£10.00",
            "availability": "in_stock",
            "description": "Camilleâ€™s story",
            "scraped_at": "2025-11-30T20:04:56+00:00",
        }
    ]

    products, df = clean_products(records, currency="GBP", cleaning=CleaningConfig())

    assert len(products) == 1
    assert df.loc[0, "id"] == "book-1"
    assert df.loc[0, "title"] == "Français Title"
    assert df.loc[0, "description"] == "Camille’s story"
    assert df.loc[0, "availability"] == "in_stock"
    assert df.loc[0, "scraped_at"] == "2025-11-30T20:04:56+00:00"


def test_clean_products_repairs_mixed_punctuation_sequences():
    em_dash = bytes([0xE2, 0x80, 0x94]).decode("cp1252")
    ellipsis = bytes([0xE2, 0x80, 0xA6]).decode("cp1252")
    records = [
        {
            "name": "Book 1",
            "availability": "In stock",
            "description": f"Line one {em_dash} line two{ellipsis}",
        }
    ]

    _, df = clean_products(records, currency="GBP", cleaning=CleaningConfig())

    assert df.loc[0, "description"] == "Line one — line two…"


def test_clean_products_repairs_partially_collapsed_em_dash_sequences():
    broken_em_dash = '\u00e2\u20ac"'
    records = [
        {
            "name": "Book 1",
            "availability": "In stock",
            "description": f'Blurb {broken_em_dash} quoted text',
        }
    ]

    _, df = clean_products(records, currency="GBP", cleaning=CleaningConfig())

    assert df.loc[0, "description"] == "Blurb — quoted text"
