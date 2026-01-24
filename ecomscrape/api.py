from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[1] / "outputs" / "processed" / "latest_products.json"
UI_DIR = Path(__file__).resolve().parents[1] / "docs"
INDEX_FILE = UI_DIR / "index.html"
PRODUCTS_FILE = UI_DIR / "products.html"
ANALYTICS_FILE = UI_DIR / "analytics.html"
DETAILS_FILE = UI_DIR / "product_details.html"
ASSETS_DIR = UI_DIR / "assets"
DATASETS_DIR = UI_DIR / "datasets"


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
    if not UI_DIR.exists():
        raise RuntimeError(f"UI directory not found: {UI_DIR}")
    app = FastAPI(title="EcomScrape API", version="0.1.0")

    ui_dataset_path = DATASETS_DIR / "latest_products.json"

    def _resolve_active_data_path() -> Optional[Path]:
        if path.exists():
            return path
        if ui_dataset_path.exists():
            return ui_dataset_path
        return None

    def _load_products() -> List[Dict[str, Any]]:
        # Read the latest JSON snapshot; empty list if missing to avoid crashes.
        active_path = _resolve_active_data_path()
        if not active_path:
            return []
        try:
            return json.loads(active_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to read data: {exc}") from exc

    def _generated_at_iso() -> Optional[str]:
        # Provide ISO timestamp for display and caching hints.
        active_path = _resolve_active_data_path()
        if not active_path:
            return None
        return datetime.fromtimestamp(active_path.stat().st_mtime, tz=timezone.utc).isoformat()

    def _serve_html(file_path: Path) -> HTMLResponse:
        # Serve static frontend pages with a friendly error if missing.
        if not file_path.exists():
            raise HTTPException(status_code=500, detail="Frontend file not found.")
        return HTMLResponse(content=file_path.read_text(encoding="utf-8"))

    @app.get("/", response_class=HTMLResponse)
    def serve_index() -> HTMLResponse:
        return _serve_html(INDEX_FILE)

    @app.get("/analytics", response_class=HTMLResponse)
    def serve_analytics() -> HTMLResponse:
        return _serve_html(ANALYTICS_FILE)

    @app.get("/charts", response_class=HTMLResponse)
    def serve_charts() -> HTMLResponse:
        # Backwards-compatible route for older links.
        return _serve_html(ANALYTICS_FILE)

    @app.get("/product-details", response_class=HTMLResponse)
    def serve_product_details() -> HTMLResponse:
        return _serve_html(DETAILS_FILE)

    @app.get("/products-page", response_class=HTMLResponse)
    def serve_products_page() -> HTMLResponse:
        return _serve_html(PRODUCTS_FILE)

    def _products_payload(
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
            "data_path": str(_resolve_active_data_path() or path),
        }

    @app.get("/products")
    def get_products(
        min_price: Optional[float] = Query(default=None, description="Minimum current price"),
        max_price: Optional[float] = Query(default=None, description="Maximum current price"),
        category: Optional[str] = Query(default=None, description="Exact category match"),
    ) -> Dict[str, Any]:
        return _products_payload(min_price=min_price, max_price=max_price, category=category)

    @app.get("/api/products")
    def get_products_api(
        min_price: Optional[float] = Query(default=None, description="Minimum current price"),
        max_price: Optional[float] = Query(default=None, description="Maximum current price"),
        category: Optional[str] = Query(default=None, description="Exact category match"),
    ) -> Dict[str, Any]:
        return _products_payload(min_price=min_price, max_price=max_price, category=category)

    @app.get("/api/health")
    def health() -> Dict[str, Any]:
        ui_updated_at = None
        if INDEX_FILE.exists():
            ui_updated_at = datetime.fromtimestamp(INDEX_FILE.stat().st_mtime, tz=timezone.utc).isoformat()
        return {
            "status": "ok",
            "version": app.version,
            "ui_updated_at": ui_updated_at,
            "data_updated_at": _generated_at_iso(),
            "data_path": str(_resolve_active_data_path() or path),
        }

    # Serve static UI assets and dataset.
    if ASSETS_DIR.exists():
        app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
    if DATASETS_DIR.exists():
        app.mount("/datasets", StaticFiles(directory=DATASETS_DIR), name="datasets")
    app.mount("/", StaticFiles(directory=UI_DIR, html=True), name="ui")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("ecomscrape.api:app", host="0.0.0.0", port=port)
