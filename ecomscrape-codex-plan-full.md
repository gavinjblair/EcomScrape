# EcomScrape – Codex Work Plan

This document defines four feature tasks to make EcomScrape feel like a real SaaS product:

1. Saved views on Products  
2. AI-powered insights engine (Analytics)  
3. Scrape Jobs page (fake but realistic)  
4. Empty / loading / error states  

Codex: please treat each section as a separate feature, but keep the overall design and architecture consistent.

---

## 1. Saved views on Products (filters → named presets)

**Goal**  
Add **Saved Views** to the Products Explorer so users can save the current filters (min price, max price, category, min rating, availability, sort) as named presets and quickly re-apply them.

**Scope**
- Only modify `docs/products.html` and the JS file controlling filters/table rendering.
- Do NOT change how products load or filter; just add a feature layer.
- Use `localStorage` to persist presets.

### Requirements

### 1. Saved Views UI bar
Add above the table or filters sidebar:

```html
<div id="savedViewsBar" class="flex flex-wrap items-center gap-2 mb-4">
  <span class="text-xs uppercase tracking-wide text-white/50">Saved views</span>
</div>
```

### 2. “Save current view” workflow
- Button opens a modal prompting for a name.
- Saves structure:

```json
{
  "name": "High rated cheap",
  "filters": {
    "minPrice": 0,
    "maxPrice": 30,
    "category": "Fiction",
    "minRating": 4,
    "availability": "in-stock",
    "sort": "price-asc"
  }
}
```

- Save array under `ecomscrape_saved_views`.

### 3. Load views from `localStorage`
Render pills for each saved view at load.

### 4. Apply saved view
- Update filter inputs.
- Trigger existing filter logic.

### 5. Delete saved view
- Small “×” icon on each pill deletes it.

### 6. Styling
Use Tailwind glassmorphic pill styles.

### 7. JS helper functions
- `loadSavedViews()`
- `renderSavedViews()`
- `saveCurrentView()`
- `applySavedView()`
- `deleteSavedView()`

---

## 2. AI-powered insights engine (Analytics)

**Goal**  
Add a dynamic **Insights** section based on analytics data.  
Uses heuristics, not real AI.

**Scope**  
Only change `analytics.html` + its JS.

### UI to add in analytics.html:

```html
<section class="mt-12">
  <h2 class="text-2xl font-semibold mb-2">AI-powered insights</h2>
  <p class="text-sm text-white/70 mb-5">
    Highlights derived from the current filtered dataset. These update whenever filters change.
  </p>
  <div id="insightsGrid" class="grid gap-4 md:grid-cols-2 xl:grid-cols-3"></div>
</section>
```

### Insight card design

```html
<div class="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 shadow-lg shadow-black/40 p-4 flex flex-col gap-1 glass-topline">
  <h3 class="text-sm font-semibold text-white">High-value category</h3>
  <p class="text-xs text-white/60">Food and Drink • Avg £35.21</p>
  <p class="text-xs text-white/70 leading-relaxed">
    Food and Drink titles are priced higher than other categories, suggesting a premium segment.
  </p>
</div>
```

### Required analyticsState
Expose:

- totalProducts  
- avgPrice  
- medianPrice  
- avgRating  
- numCategories  
- minPrice / maxPrice  
- categoryCounts  
- avgPricePerCategory  
- ratingDistribution  
- availabilityCounts  

### Insight heuristics
Generate 3–6 insights:

- High-value category  
- Value-friendly category  
- Rating skew  
- Availability comment  
- Price spread  

### Functions needed:
- `computeAnalyticsState(products)`
- `generateInsights(state)`
- `renderInsights(insights)`

### When filters change:
```js
const state = computeAnalyticsState(filteredProducts);
updateCharts(state);
renderInsights(generateInsights(state));
```

### Empty dataset:
Show a single “Not enough data” card.

---

## 3. Scrape Jobs page (fake jobs + modals)

**Goal**  
Add a realistic **Scrape Jobs** system with fake data, progress simulation, and a details panel.

**Scope**
- New file: `docs/jobs.html`
- New JS: `docs/assets/js/jobs.js`
- Add “Jobs” to sidebar.

### jobs.html layout

- Title: “Scrape Jobs”
- Subtitle: “Manage scraping runs and view history.”
- Button: “New job”
- Job table (glassmorphic)
- Job detail panel below

### Job table columns:
- Name  
- Target  
- Last run  
- Status  
- Records  
- Actions (Run now, Details)

### Fake data example:

```js
const jobs = [
  {
    id: "books_full",
    name: "Books – Full catalogue",
    target: "https://books.toscrape.com",
    description: "Scrapes all titles with price, rating, availability.",
    selectors: { title: "h3 a", price: ".price_color" },
    status: "Idle",
    lastRunAt: "...",
    lastRunStatus: "Success",
    totalRecords: 1000,
    runs: [
      { startedAt: "...", finishedAt: "...", status: "Success", records: 1000 }
    ]
  }
];
```

### Job detail panel
Shows:
- Name, target  
- Description  
- Selectors  
- Run history list  

### “Run now” modal (simulated progress)
- Open modal  
- Fake progress bar goes 0 → 100%  
- status: “Queued → Running → Completed”  
- Update job object  
- Update table + detail panel  

### “New job” modal
- Simple form  
- Adds to jobs array  

### Empty state:
If no jobs: large message + “Create job” button.

---

## 4. Empty / loading / error states (Products, Analytics, Jobs, Product Details)

**Goal**  
Add proper UX states for loading, empty results, and errors.

### Shared helpers

```js
function showLoading(container) { ... }
function showError(container, msg) { ... }
function showEmpty(container, title, desc, actionLabel, actionFn) { ... }
```

### Skeleton classes:
`bg-white/5 animate-pulse rounded-xl`

---

## Products Page

### Loading:
Replace table/grid with skeleton rows/cards.

### Empty:
A card:

```html
<h3>No products match these filters</h3>
<button id="clearFiltersBtn">Clear filters</button>
```

### Error:
Red-tinted alert bar.

---

## Analytics Page

### Loading:
Skeleton chart cards.

### Empty:
One wide empty card: “Not enough data for analytics”.

### Error:
Per-chart error messages.

---

## Jobs Page

### Loading:
Skeleton rows.

### Empty:
“No jobs yet”.

### Error:
Red error banner with “Retry”.

---

## Product Details

If missing product:

```html
<h2>Product not found</h2>
<a href="products.html">Back to products</a>
```

---

**End of full Codex work plan.**
