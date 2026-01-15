from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .config import CleaningConfig
from .models import Product

LOGGER = logging.getLogger(__name__)

DEFAULT_AVAILABILITY_MAP = {
    "in stock": "in_stock",
    "available": "in_stock",
    "out of stock": "out_of_stock",
    "out-of-stock": "out_of_stock",
    "pre-order": "preorder",
    "preorder": "preorder",
}

DEFAULT_RATING_WORD_MAP = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


def _normalise_text(value: Any) -> str:
    # Replace non-breaking spaces and compress whitespace for consistent parsing.
    text = str(value).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _clean_price(value: Any) -> Optional[float]:
    # Extract numeric price from mixed strings while tolerating commas and symbols.
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = _normalise_text(value)
    match = re.search(r"([-+]?\d[\d,]*(?:\.\d+)?)", text)
    if not match:
        return None
    numeric = match.group(1).replace(",", "")
    try:
        return float(numeric)
    except ValueError:
        return None


def _clean_review_count(value: Any) -> Optional[int]:
    # Pull the first integer-like sequence from the value.
    if value is None:
        return None
    match = re.search(r"(\d+)", _normalise_text(value).replace(",", ""))
    return int(match.group(1)) if match else None


def _clean_rating(value: Any, rating_map: Dict[str, float]) -> Optional[float]:
    # Accept either numeric text or mapped rating words/classes.
    if value is None:
        return None
    if isinstance(value, list):
        for entry in value:
            if entry is None:
                continue
            if entry.lower() in rating_map:
                return float(rating_map[entry.lower()])
    text = _normalise_text(value)
    number_match = re.search(r"(\d+(?:\.\d+)?)", text)
    if number_match:
        return float(number_match.group(1))
    for word, number in rating_map.items():
        if word in text.lower():
            return float(number)
    return None


def _standardise_availability(value: Any, availability_map: Dict[str, str]) -> Optional[str]:
    # Map site-specific availability phrases into normalised labels.
    if value is None:
        return None
    lower = _normalise_text(value).lower()
    for key, canonical in availability_map.items():
        if key in lower:
            return canonical
    if lower:
        return "unknown"
    return None


def _stable_product_id(title: Optional[str], category: Optional[str], product_url: Optional[str], source_url: Optional[str]) -> str:
    # Create a deterministic identifier for stable product URLs.
    parts = [product_url, source_url, title, category]
    base = "|".join(p.strip().lower() for p in parts if p)
    if not base:
        base = "unknown"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]


def clean_products(
    records: List[Dict[str, Any]],
    currency: Optional[str] = None,
    cleaning: Optional[CleaningConfig] = None,
) -> Tuple[List[Product], pd.DataFrame]:
    """
    Convert raw scraped product dicts into a list of Product instances and a normalised DataFrame.
    """
    if not records:
        empty_df = pd.DataFrame()
        return [], empty_df

    rating_map = {**DEFAULT_RATING_WORD_MAP, **((cleaning.rating_words) if cleaning else {})}
    availability_map = {**DEFAULT_AVAILABILITY_MAP, **((cleaning.availability_map) if cleaning else {})}

    products: List[Product] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for record in records:
        title = record.get("title") or record.get("name")
        category_val = record.get("category") or record.get("genre") or record.get("type") or record.get("category_name")
        product_url = record.get("product_url") or record.get("url")
        prod = Product(
            id=_stable_product_id(title, category_val, product_url, record.get("source_url")),
            title=title,
            name=record.get("name") or title,
            url=record.get("url"),
            product_url=product_url,
            price_current=_clean_price(record.get("price_current")),
            price_original=_clean_price(record.get("price_original")),
            rating=_clean_rating(record.get("rating"), rating_map),
            availability=_standardise_availability(record.get("availability"), availability_map),
            image_url=record.get("image_url"),
            source_url=record.get("source_url"),
            category=category_val or "unknown",
            currency=record.get("currency") or currency,
            review_count=_clean_review_count(record.get("review_count")),
            scraped_at=now_iso,
            description=record.get("description"),
        )
        products.append(prod)

    df = pd.DataFrame([asdict(p) for p in products])
    LOGGER.debug("Cleaned %s products into DataFrame with %s columns", len(products), len(df.columns))
    return products, df
