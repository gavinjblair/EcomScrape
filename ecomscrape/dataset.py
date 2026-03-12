from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple


def utc_now_iso() -> str:
    # Keep dataset timestamps in a single ISO format across exporters and API responses.
    return datetime.now(timezone.utc).isoformat()


def build_products_dataset(
    products: Iterable[Dict[str, Any]],
    *,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    product_list = list(products)
    return {
        "products": product_list,
        "generated_at": generated_at or utc_now_iso(),
    }


def parse_products_dataset(raw: Any) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    # Accept both legacy arrays and the canonical object payload for compatibility.
    if isinstance(raw, list):
        return _validate_products(raw), None

    if isinstance(raw, dict):
        products = raw.get("products") or []
        if not isinstance(products, list):
            raise ValueError("Dataset field 'products' must be a list.")
        generated_at = raw.get("generated_at") or raw.get("generatedAt")
        if generated_at is not None:
            generated_at = str(generated_at)
        return _validate_products(products), generated_at

    raise ValueError("Dataset JSON must be a product array or an object with a 'products' array.")


def _validate_products(products: List[Any]) -> List[Dict[str, Any]]:
    validated: List[Dict[str, Any]] = []
    for index, product in enumerate(products):
        if not isinstance(product, dict):
            raise ValueError(f"Product at index {index} must be an object.")
        validated.append(product)
    return validated
