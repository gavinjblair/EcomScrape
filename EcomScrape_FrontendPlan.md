# EcomScrape – Frontend UI + Charts Dashboard Implementation Plan (For Codex)

This document describes all required steps for Codex to implement:

1. A simple HTML/JS UI for browsing scraped products.
2. A second HTML/JS page with charts and category-level analytics.
3. FastAPI routes to serve both pages.

Codex should follow these instructions exactly.  
No scraper logic, API schema, tests, or CLI behaviour should be changed.

---

# 1. Create `frontend/` Directory

Add a new folder in the project root:

```
frontend/
```

This folder will contain:
- `index.html` – main product table UI  
- `charts.html` – charts/dashboard UI  

---

# 2. Implement `frontend/index.html`

Codex should create a standalone HTML file that:

## UI Content
- Shows:
  - Min price (number input)
  - Max price (number input)
  - Category dropdown (populated dynamically)
  - “Load products” button
  - “Reset filters” button
- Displays a table containing:
  - Title
  - Category
  - Price (use `price_current` if available)
  - Rating
  - Availability
- Shows a summary:
  - “X product(s) displayed.”
- Shows:
  - “Data generated at: <timestamp>” from `/products`

## Behaviour
- On page load:
  - Auto-fetch `/products`
  - Populate category dropdown
- Apply filters using query params:
  - `min_price`
  - `max_price`
  - `category`
- Use `fetch()` to call `/products` and update the table.

## Error handling
- If `/products` returns empty data:
  Display a message:
  ```
  No product data available. Run the scraper, e.g.:
  ecomscrape -c configs/books_toscrape.yaml -f json
  ```

---

# 3. Implement `frontend/charts.html`

A second HTML/JS page showing a **visual dashboard**.

## Data source
Fetch data from:
```
/products
```
(no filters required)

## Required charts
Codex may use Chart.js via CDN.

1. **Category counts**  
   - Bar chart  
   - X-axis: category  
   - Y-axis: number of products  

2. **Average price per category**  
   - Bar chart  
   - Use `price_current` else `price_original`  

3. **Price distribution**  
   - Histogram-style chart  
   - Use same price logic as above  

## Required page content
- Header:
  - “EcomScrape – Category Dashboard”
- Status panel:
  - Total number of products
  - Data generated timestamp
- Chart containers for the three charts
- Link back to `index.html`

## Optional
- Tooltip support (default in Chart.js)
- Simple CSS similar to `index.html`

---

# 4. Update `ecomscrape/api.py` to Serve Frontend

Codex should modify `api.py`:

## 4.1 Add file paths
Define paths pointing to:
```
frontend/index.html
frontend/charts.html
```

## 4.2 Add new FastAPI routes

### Route 1: `/`
Serve `index.html`

### Route 2: `/charts`
Serve `charts.html`

### Requirements
- Return files with `HTMLResponse`
- If missing, return 500 error with message:
  - “Frontend file not found.”

## 4.3 Do NOT modify existing `/products` endpoint.

---

# 5. Behaviour Validation (Codex self-check)

Codex should verify that after implementing:

## Backend
Running:
```
uvicorn ecomscrape.api:app --reload
```
provides:

- Main UI at:  
  ```
  http://127.0.0.1:8000/
  ```
- Charts UI at:
  ```
  http://127.0.0.1:8000/charts
  ```

## Frontend functionality
- `index.html` loads data, filters work, table updates.
- `charts.html` renders:
  - category counts,
  - average prices,
  - price distribution.

## API functionality
Existing `/products` behaviour unchanged:
- Supports `min_price`
- `max_price`
- `category`
- Returns `products`, `count`, `generated_at`.

## Tests
All previous tests must still pass:
```
python -m pytest
```

---

# 6. Constraints — Codex MUST NOT:

- Change scraper logic
- Change data model
- Change CLI behaviour
- Modify tests unless strictly required
- Remove existing routes
- Add Node.js or bundlers
- Introduce new APIs

---

# 7. Optional Enhancements (If Simple)

- Add navigation links between pages.
- Add light CSS styling for readability.
- Add explanations under each chart.

---

# 8. Input Files for Codex

The project ZIP is available at:

```
/mnt/data/EcomScrape.zip
```

Implement all steps within that project.

---

This specification is complete.  
Codex should now implement both frontend pages and the required FastAPI routes.
