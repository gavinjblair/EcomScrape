from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class DetailFields:
    category: Optional[str] = None
    description: Optional[str] = None


class SiteAdapter:
    name = "generic"

    def matches(self, site_name: str, base_url: Optional[str]) -> bool:
        return False

    def prepare_product_url(self, url: str) -> str:
        return url

    def extract_detail_fields(self, html: str) -> DetailFields:
        return DetailFields()


class BooksToScrapeAdapter(SiteAdapter):
    name = "books.toscrape.com"

    def matches(self, site_name: str, base_url: Optional[str]) -> bool:
        site_key = site_name.strip().lower().replace(" ", "_")
        host = urlparse(base_url or "").netloc.lower()
        return "books.toscrape.com" in host or site_key in {"books_toscrape", "bookstoscrape"}

    def prepare_product_url(self, url: str) -> str:
        if "/catalogue/" not in url:
            return url.replace("https://books.toscrape.com/", "https://books.toscrape.com/catalogue/", 1)
        return url

    def extract_detail_fields(self, html: str) -> DetailFields:
        soup = BeautifulSoup(html, "lxml")
        category_node = soup.select_one("ul.breadcrumb li:nth-last-child(2) a")
        description_node = soup.select_one("#product_description + p")
        return DetailFields(
            category=category_node.get_text(strip=True) if category_node else None,
            description=description_node.get_text(strip=True) if description_node else None,
        )


_REGISTERED_ADAPTERS = (BooksToScrapeAdapter(),)


def get_site_adapter(site_name: str, base_url: Optional[str]) -> Optional[SiteAdapter]:
    for adapter in _REGISTERED_ADAPTERS:
        if adapter.matches(site_name, base_url):
            return adapter
    return None
