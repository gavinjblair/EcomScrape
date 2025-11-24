from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[1] / "outputs" / "processed" / "latest_products.json"
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"
CHARTS_FILE = FRONTEND_DIR / "charts.html"


def _resolve_data_path() -> Path:
    # Allow deployments to override the data location via environment.
    env_path = os.getenv("ECOMSCRAPE_DATA_PATH")
    return Path(env_path) if env_path else DEFAULT_DATA_PATH


def _filter_products(
    products: List[Dict[str, Any]],
    min_price: Optional[float],
    max_price: Optional[float],
    category: Optional[str],
) -> List[Dict[str, Any]]:
    # Apply server-side filtering to keep the frontend simple.
    result = []
    for product in products:
        price = product.get("price_current")
        if price is None:
            price = product.get("price_original")
        if min_price is not None and (price is None or price < min_price):
            continue
        if max_price is not None and (price is None or price > max_price):
            continue
        if category and str(product.get("category", "")).lower() != category.lower():
            continue
        result.append(product)
    return result


def create_app(data_path: Optional[Path] = None) -> FastAPI:
    path = data_path or _resolve_data_path()
    app = FastAPI(title="EcomScrape API", version="0.1.0")

    def _load_products() -> List[Dict[str, Any]]:
        # Read the latest JSON snapshot; empty list if missing to avoid crashes.
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to read data: {exc}") from exc

    def _generated_at_iso() -> Optional[str]:
        # Provide ISO timestamp for display and caching hints.
        if not path.exists():
            return None
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()

    def _serve_html(file_path: Path) -> HTMLResponse:
        # Serve static frontend pages with a friendly error if missing.
        if not file_path.exists():
            raise HTTPException(status_code=500, detail="Frontend file not found.")
        return HTMLResponse(content=file_path.read_text(encoding="utf-8"))

    @app.get("/", response_class=HTMLResponse)
    def serve_index() -> HTMLResponse:
        return _serve_html(INDEX_FILE)

    @app.get("/charts", response_class=HTMLResponse)
    def serve_charts() -> HTMLResponse:
        return _serve_html(CHARTS_FILE)

    @app.get("/products")
    def get_products(
        min_price: Optional[float] = Query(default=None, description="Minimum current price"),
        max_price: Optional[float] = Query(default=None, description="Maximum current price"),
        category: Optional[str] = Query(default=None, description="Exact category match"),
    ) -> Dict[str, Any]:
        products = _load_products()
        filtered = _filter_products(products, min_price=min_price, max_price=max_price, category=category)
        return {
            "products": filtered,
            "count": len(filtered),
            "generated_at": _generated_at_iso(),
            "data_path": str(path),
        }

    return app


app = create_app()
