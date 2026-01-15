from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    # Dataclass used across cleaning, exports, and API responses to keep schema explicit.
    id: Optional[str] = None
    title: Optional[str] = None
    name: Optional[str] = None  # keep compatibility with configs using "name"
    price_current: Optional[float] = None
    price_original: Optional[float] = None
    rating: Optional[float] = None
    availability: Optional[str] = None
    image_url: Optional[str] = None
    url: Optional[str] = None
    product_url: Optional[str] = None
    source_url: Optional[str] = None
    category: Optional[str] = None
    currency: Optional[str] = None
    review_count: Optional[int] = None
    scraped_at: Optional[str] = None
    description: Optional[str] = None
