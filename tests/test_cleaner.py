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

    assert _clean_price("£1,234.50") == 1234.5
    assert _clean_rating(["star-rating", "Three"], rating_map) == 3
    assert _standardise_availability("In stock ", availability_map) == "in_stock"


def test_clean_products_creates_products_and_dataframe():
    # Ensure clean_products returns both Product objects and a populated DataFrame.
    records = [
        {"name": "Book 1", "price_current": "£10.00", "rating": "Five", "availability": "In stock"},
        {"name": "Book 2", "price_current": "£5.50", "rating": "Three", "availability": "Out of stock"},
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
