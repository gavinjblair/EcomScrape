from __future__ import annotations

import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .config import FieldSelector, ParsingConfig


class Parser:
    def __init__(self, parsing: ParsingConfig, base_url: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.parsing = parsing
        self.base_url = base_url
        self.logger = logger or logging.getLogger(__name__)

    def _extract_value(self, node, field: FieldSelector) -> Optional[str]:
        # Safely pull either text content or a chosen attribute, joining relative links when needed.
        if node is None:
            return None
        if field.attribute and field.attribute != "text":
            value = node.get(field.attribute)
            if isinstance(value, list):
                value = " ".join(value)
        else:
            value = node.get_text(" ", strip=True)
        if value and field.join_base_url:
            value = urljoin(self.base_url or "", value)
        return value

    def parse(self, html: str, source_url: str) -> List[Dict[str, Optional[str]]]:
        soup = BeautifulSoup(html, "lxml")
        containers = soup.select(self.parsing.product_container)
        products: List[Dict[str, Optional[str]]] = []

        for container in containers:
            record: Dict[str, Optional[str]] = {"source_url": source_url}
            for field_name, field in self.parsing.fields.items():
                node = container.select_one(field.selector)
                record[field_name] = self._extract_value(node, field)
            products.append(record)

        self.logger.debug("Parsed %s products from %s", len(products), source_url)
        return products
