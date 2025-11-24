"""
EcomScrape package entry.

Provides scraping, cleaning, and exporting utilities for e-commerce pages.
"""

__all__ = [
    "config",
    "fetch",
    "parser",
    "cleaner",
    "exporter",
    "models",
    "Product",
]

__version__ = "0.1.0"

from .models import Product  # noqa: E402  (re-export for convenience)
