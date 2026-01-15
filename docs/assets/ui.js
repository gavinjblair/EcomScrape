// Simple helpers for loading dataset and common formatting
const DATASET_CACHE_KEY = "ecomscrape_dataset_cache_v1";
const DATASET_META_KEY = "ecomscrape_dataset_meta_v1";
let memoizedDataset = null;
let memoizedPath = null;

function reportDatasetError(path, err, useCache = false) {
  const message = `Dataset load failed (${path}). ${err?.message || err || "Unknown error"}`;
  console.error(message);

  const bannerId = "datasetErrorBanner";
  let banner = document.getElementById(bannerId);
  if (!banner) {
    banner = document.createElement("div");
    banner.id = bannerId;
    banner.className =
      "fixed top-4 right-4 z-50 max-w-md bg-red-500/20 text-red-200 border border-red-400/50 rounded-xl p-3 text-sm shadow-lg";
    document.body.appendChild(banner);
  }
  banner.textContent = useCache ? `${message} Showing cached data.` : message;
}

function clearDatasetError() {
  const banner = document.getElementById("datasetErrorBanner");
  if (banner) banner.remove();
}

function loadCachedDataset() {
  try {
    const raw = localStorage.getItem(DATASET_CACHE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function storeCachedDataset(path, data, res) {
  try {
    const meta = {
      url: path,
      etag: res.headers.get("ETag"),
      lastModified: res.headers.get("Last-Modified"),
      cachedAt: new Date().toISOString(),
    };
    localStorage.setItem(DATASET_CACHE_KEY, JSON.stringify(data));
    localStorage.setItem(DATASET_META_KEY, JSON.stringify(meta));
  } catch {
    // Ignore cache errors.
  }
}

function getCacheMeta(path) {
  try {
    const raw = localStorage.getItem(DATASET_META_KEY);
    if (!raw) return {};
    const meta = JSON.parse(raw);
    if (meta.url && meta.url !== path) return {};
    return meta;
  } catch {
    return {};
  }
}

export async function loadDataset(path = "./datasets/latest_products.json") {
  if (memoizedDataset && memoizedPath === path) return memoizedDataset;

  const meta = getCacheMeta(path);
  const headers = {};
  if (meta.etag) headers["If-None-Match"] = meta.etag;
  if (meta.lastModified) headers["If-Modified-Since"] = meta.lastModified;

  let res;
  try {
    res = await fetch(path, { headers });
  } catch (err) {
    const cached = loadCachedDataset();
    if (cached) {
      reportDatasetError(path, err, true);
      memoizedDataset = cached;
      memoizedPath = path;
      return cached;
    }
    reportDatasetError(path, err);
    throw err;
  }

  if (res.status === 304) {
    const cached = loadCachedDataset();
    if (cached) {
      memoizedDataset = cached;
      memoizedPath = path;
      clearDatasetError();
      return cached;
    }
  }

  if (!res.ok) {
    const err = new Error(`Request failed with status ${res.status}`);
    const cached = loadCachedDataset();
    if (cached) {
      reportDatasetError(path, err, true);
      memoizedDataset = cached;
      memoizedPath = path;
      return cached;
    }
    reportDatasetError(path, err);
    throw err;
  }

  const raw = await res.json();
  const data = Array.isArray(raw)
    ? { products: raw, generated_at: null }
    : { products: raw.products || [], generated_at: raw.generated_at || raw.generatedAt || null };

  storeCachedDataset(path, data, res);
  memoizedDataset = data;
  memoizedPath = path;
  clearDatasetError();
  return data;
}

export function sanitizeHtml(value) {
  const div = document.createElement("div");
  div.textContent = String(value ?? "");
  return div.innerHTML;
}

export function humanDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return "";
  return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function availabilityBadgeElement(avail) {
  const raw = String(avail || "").trim();
  const lower = raw.toLowerCase();
  const isInStock = lower.includes("in stock") || lower.includes("available") || lower.includes("in_stock");
  const text = raw ? (isInStock ? "In stock" : raw) : "-";
  const span = document.createElement("span");
  span.className = isInStock
    ? "inline-flex items-center px-2 py-1 rounded-full text-[0.7rem] font-semibold bg-emerald-400/20 text-emerald-300 border border-emerald-400/70"
    : "inline-flex items-center px-2 py-1 rounded-full text-[0.7rem] font-semibold bg-white/10 text-warning border border-white/20";
  span.textContent = text;
  return span;
}

export function availabilityBadge(avail) {
  return availabilityBadgeElement(avail).outerHTML;
}

export function priceValue(p) {
  const raw = p.price_current ?? p.price ?? p.price_original;
  const num = typeof raw === "string" ? parseFloat(raw) : raw;
  return Number.isFinite(num) ? num : null;
}

// UI helper snippets
export function showLoading(container, skeletonHtml = '<div class="bg-white/5 animate-pulse rounded-xl h-24"></div>') {
  if (!container) return;
  container.innerHTML = skeletonHtml;
}

export function showError(container, msg = "Something went wrong") {
  if (!container) return;
  container.innerHTML = `<div class="bg-red-500/10 text-red-200 border border-red-400/50 rounded-xl p-3 text-sm">${msg}</div>`;
}

export function showEmpty(container, title = "No data", desc = "", actionLabel = "", actionFn = null) {
  if (!container) return;
  const btn = actionLabel
    ? `<button class="mt-3 inline-flex items-center px-3 py-2 rounded-full border border-white/30 bg-white/5 text-white hover:bg-white/10 transition action-btn">${actionLabel}</button>`
    : "";
  container.innerHTML = `
    <div class="bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-white/70">
      <div class="font-semibold text-white mb-1">${title}</div>
      <div>${desc}</div>
      ${btn}
    </div>
  `;
  if (actionLabel && actionFn) {
    const button = container.querySelector(".action-btn");
    if (button) button.addEventListener("click", actionFn);
  }
}
