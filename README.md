# EcomScrape

Config-driven e-commerce scraper with CSV/Excel/JSON export, FastAPI JSON endpoint, and a GitHub Pages static demo for portfolio use (MSc/PhD-friendly).

## Features
- YAML/JSON configs for selectors, pagination (link/format), retries, rotating headers, concurrency.
- Cleaning pipeline to normalise prices, ratings, availability, categories, images; outputs a `Product` dataclass and pandas DataFrame.
- Exports CSV/Excel/JSON plus `latest_products.json` for the API/UI and static demo.
- FastAPI endpoint `GET /products` with filters; serves a lightweight frontend.
- Static GitHub Pages-ready UI in `docs/`: Home, Products Explorer, Analytics Dashboard, Product Details with dark mode and shared filters.

## Running the scraper (CLI)
```bash
cd EcomScrape
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Scrape and export JSON/CSV/Excel
python -m ecomscrape.cli -c configs/books_toscrape.yaml -f json csv excel
```
Outputs land in `outputs/processed/` with `latest_products.json` for the API/UI.

## Running the API + frontend
```bash
uvicorn ecomscrape.api:app --reload
# Browse: http://127.0.0.1:8000/ (products) and /charts (charts)
```
Environment override for data: `ECOMSCRAPE_DATA_PATH=/path/to/latest_products.json`.

## GitHub Pages static demo
- Static pages live in `docs/` and read `docs/datasets/latest_products.json` (no backend).
- Pages:
  - `docs/index.html` - landing page and dataset overview
  - `docs/products.html` - products explorer
  - `docs/analytics.html` - analytics dashboard
  - `docs/product_details.html` - per-product view via `?id=...`
- Publish by pushing `docs/` to the default branch and enabling GitHub Pages (root = `/docs`).

## Dataset structure
`latest_products.json` (array or object with `products`):
```json
{
  "products": [
    {
      "id": "123",
      "title": "Example",
      "price_current": 19.99,
      "price_original": 24.99,
      "rating": 4.5,
      "availability": "in_stock",
      "category": "Books",
      "image_url": "https://...",
      "source_url": "https://...",
      "scraped_at": "2025-11-24T18:00:00Z"
    }
  ],
  "generated_at": "2025-11-24T18:00:00Z"
}
```

## Publishing a dataset to GitHub Pages
1. Run the scraper with `-f json` to produce `outputs/processed/latest_products.json`.
2. Copy that file to `docs/datasets/latest_products.json` (create the folder if missing).
3. Commit and push. GitHub Pages will serve the updated data without backend changes.

## Screenshot placeholders
- Add captures for:
  - Products page (with filters applied).
  - Charts dashboard.
  - Product details page.
Place images in `docs/assets/` and reference them here once captured.

## Future work
- Add pagination crawling for more demo sites.
- Extend cleaning rules per-site with richer mapping.
- Add automated visual tests for the static pages.
- Optional auth/rate limiting for the API.

## Licence
MIT Licence. Use freely for learning, research, and portfolio demonstrations.
