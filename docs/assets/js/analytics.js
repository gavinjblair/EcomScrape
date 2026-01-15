import { loadDataset, humanDate, priceValue, showError, showEmpty } from "../ui.js";
import "../state.js";

const apexCharts = {};
const chartAnimations = {
  enabled: true,
  easing: "easeInOutQuad",
  speed: 800,
  animateGradually: { enabled: true, delay: 120 },
  dynamicAnimation: { enabled: true, speed: 400 },
};

let showFullLegend = false;
let categoryMetric = "count";
let lastSunburstData = { compactEntries: [], fullEntries: [], totalProducts: 0, otherCount: 0 };
let lastSunburstMeta = { labels: [], series: [], totalProducts: 0 };
let lastAnalyticsState = null;

function forceChartsResize() {
  window.dispatchEvent(new Event("resize"));
}

function formatNumber(val) {
  return Number(val || 0).toLocaleString();
}

function truncateLabel(value, maxLength = 12) {
  const text = String(value || "");
  if (text.length <= maxLength) return text;
  if (maxLength <= 3) return text.slice(0, maxLength);
  return `${text.slice(0, maxLength - 3)}...`;
}

function buildCategoryData(state, metric) {
  const neonPalette = ["#00f0ff", "#5b9dff", "#a855ff", "#22c55e", "#ffd666", "#f472b6", "#38bdf8", "#7c3aed", "#14b8a6", "#d946ef"];
  const entries = Object.entries(state.categoryStats).map(([label, stats]) => {
    const avgPrice = stats.priceCount ? stats.priceSum / stats.priceCount : 0;
    const avgRating = stats.ratingCount ? stats.ratingSum / stats.ratingCount : null;
    return {
      label,
      count: stats.count,
      avgPrice,
      avgRating,
      priceSum: stats.priceSum,
      priceCount: stats.priceCount,
    };
  });

  const otherEntry = entries.find((entry) => entry.label === "Other");
  const filteredEntries = entries.filter((entry) => entry.label !== "Other");
  const sorted = filteredEntries.sort((a, b) => {
    if (metric === "avg_price") return (b.avgPrice || 0) - (a.avgPrice || 0);
    return b.count - a.count;
  });

  const topLimit = 8;
  const topEntries = sorted.slice(0, topLimit);
  const remainingEntries = sorted.slice(topLimit);

  const otherCount = remainingEntries.reduce((sum, entry) => sum + entry.count, 0) + (otherEntry ? otherEntry.count : 0);
  const otherPriceSum = remainingEntries.reduce((sum, entry) => sum + entry.priceSum, 0) + (otherEntry ? otherEntry.priceSum : 0);
  const otherPriceCount =
    remainingEntries.reduce((sum, entry) => sum + entry.priceCount, 0) + (otherEntry ? otherEntry.priceCount : 0);
  const otherAvgPrice = otherPriceCount ? otherPriceSum / otherPriceCount : 0;
  const otherCategoryCount = remainingEntries.length + (otherEntry ? 1 : 0);

  const compactEntries = topEntries.map((entry, idx) => ({
    ...entry,
    color: neonPalette[idx % neonPalette.length],
  }));
  if (otherCount > 0) {
    compactEntries.push({
      label: "Other",
      count: otherCount,
      avgPrice: otherAvgPrice,
      avgRating: null,
      color: "rgba(148, 163, 184, 0.8)",
    });
  }

  const totalProducts = state.productsCount;
  const chartEntries = compactEntries.map((entry) => ({
    ...entry,
    sharePct: totalProducts ? (entry.count / totalProducts) * 100 : 0,
    metricValue: metric === "avg_price" ? entry.avgPrice : entry.count,
  }));

  const labels = chartEntries.map((entry) => entry.label);
  const series = chartEntries.map((entry) => entry.metricValue);
  const colors = chartEntries.map((entry) => entry.color);

  const fullEntries = entries.map((entry) => ({
    label: entry.label,
    value: entry.count,
  }));

  return {
    chartEntries,
    compactEntries,
    fullEntries,
    labels,
    series,
    colors,
    totalProducts,
    otherCategoryCount,
    otherCount,
    otherAvgPrice,
  };
}

function normaliseCategoryValue(value) {
  const raw = String(value || "").trim();
  if (!raw) return "unknown";
  const lower = raw.toLowerCase();
  if (lower === "default" || lower === "add a comment") return "Other";
  return raw;
}

function filterSummaryText(state) {
  const parts = [];
  if (state.minPrice) parts.push(`min GBP ${state.minPrice}`);
  if (state.maxPrice) parts.push(`max GBP ${state.maxPrice}`);
  if (state.category) parts.push(`category=${normaliseCategoryValue(state.category)}`);
  if (state.minRating) parts.push(`min rating=${state.minRating}`);
  if (state.availability) parts.push(`availability=${state.availability}`);
  return parts.length ? `Filters: ${parts.join(", ")}` : "Filters: none (showing full dataset)";
}

function median(values) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function computeAnalyticsState(products) {
  const prices = products.map(priceValue).filter((v) => v !== null);
  const ratings = products.map((p) => parseFloat(p.rating ?? 0)).filter((v) => v);
  const categoryStats = {};
  products.forEach((p) => {
    const c = normaliseCategoryValue(p.category);
    if (!categoryStats[c]) {
      categoryStats[c] = { count: 0, priceSum: 0, priceCount: 0, ratingSum: 0, ratingCount: 0 };
    }
    categoryStats[c].count += 1;
    const price = priceValue(p);
    if (Number.isFinite(price)) {
      categoryStats[c].priceSum += price;
      categoryStats[c].priceCount += 1;
    }
    const rating = parseFloat(p.rating ?? 0);
    if (Number.isFinite(rating) && rating > 0) {
      categoryStats[c].ratingSum += rating;
      categoryStats[c].ratingCount += 1;
    }
  });
  const categoryCounts = Object.fromEntries(
    Object.entries(categoryStats).map(([label, stats]) => [label, stats.count])
  );

  const avgPricePerCategory = Object.entries(categoryStats)
    .map(([label, stats]) => ({
      label,
      value: stats.priceCount ? stats.priceSum / stats.priceCount : 0,
      count: stats.count,
      avgRating: stats.ratingCount ? stats.ratingSum / stats.ratingCount : null,
    }))
    .filter((item) => Number.isFinite(item.value));

  const bins = 12;
  const dist = new Array(bins).fill(0);
  let distLabels = [];
  if (prices.length) {
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const size = (max - min) / bins || 1;
    prices.forEach((v) => {
      let idx = Math.floor((v - min) / size);
      if (idx >= bins) idx = bins - 1;
      dist[idx] += 1;
    });
    distLabels = dist.map((_, i) => `${(min + i * size).toFixed(2)}-${(min + (i + 1) * size).toFixed(2)}`);
  }

  const ratingDistribution = products.reduce((acc, p) => {
    const r = Math.round(parseFloat(p.rating ?? 0));
    if (!r) return acc;
    acc[r] = (acc[r] || 0) + 1;
    return acc;
  }, {});

  const availabilityCounts = products.reduce((acc, p) => {
    const a = String(p.availability || "unknown").toLowerCase();
    const key = a.includes("in stock") || a.includes("available") ? "in stock" : "other";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  return {
    productsCount: products.length,
    avgPrice: prices.length ? prices.reduce((a, b) => a + b, 0) / prices.length : null,
    medianPrice: prices.length ? median(prices) : null,
    avgRating: ratings.length ? ratings.reduce((a, b) => a + b, 0) / ratings.length : null,
    numCategories: Object.keys(categoryCounts).length,
    categoryStats,
    categoryCounts,
    avgPricePerCategory,
    priceDist: { labels: distLabels, values: dist },
    ratingDistribution,
    availabilityCounts,
    prices,
    ratings,
  };
}

function generateInsights(state) {
  const insights = [];
  if (state.avgPricePerCategory.length) {
    const sorted = [...state.avgPricePerCategory].sort((a, b) => b.value - a.value);
    const top = sorted[0];
    const low = sorted[sorted.length - 1];
    insights.push({
      title: "High-value category",
      subtitle: `${top.label} - GBP ${top.value.toFixed(2)}`,
      description: `${top.label} is the top-priced category in this view, indicating premium positioning.`,
      icon: "HOT",
    });
    if (low && low.label !== top.label) {
      insights.push({
        title: "Value-friendly category",
        subtitle: `${low.label} - GBP ${low.value.toFixed(2)}`,
        description: `${low.label} offers the most budget-friendly titles right now.`,
        icon: "LOW",
      });
    }
  }
  if (state.avgRating) {
    insights.push({
      title: "Customer sentiment",
      subtitle: `Average rating ${state.avgRating.toFixed(2)}`,
      description: `Current selection trends toward ${state.avgRating >= 4 ? "favourable" : "mixed"} reviews.`,
      icon: "RATE",
    });
  }
  if (state.availabilityCounts) {
    const entries = Object.entries(state.availabilityCounts);
    if (entries.length) {
      const minAvail = entries.sort((a, b) => a[1] - b[1])[0];
      insights.push({
        title: "Availability alert",
        subtitle: `${minAvail[0]}: ${minAvail[1]} item(s)`,
        description: `${minAvail[0]} has the lowest availability; consider re-stocking focus.`,
        icon: "WARN",
      });
    }
  }
  if (state.prices && state.prices.length) {
    const skew = Math.abs((state.avgPrice || 0) - (state.medianPrice || 0));
    insights.push({
      title: "Price balance",
      subtitle: `Mean GBP ${(state.avgPrice || 0).toFixed(2)} vs Median GBP ${(state.medianPrice || 0).toFixed(2)}`,
      description: skew > 5 ? "Pricing shows some skew; consider normalising outliers." : "Pricing is balanced across the catalogue.",
      icon: "BAL",
    });
  }
  return insights.length
    ? insights.slice(0, 6)
    : [{ title: "Not enough data", subtitle: "", description: "Adjust filters to see insights.", icon: "AI" }];
}

function renderInsights(items) {
  const grid = document.getElementById("insightsGrid");
  grid.innerHTML = "";
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "text-sm text-white/60";
    empty.textContent = "No insights available for this filter.";
    grid.appendChild(empty);
    return;
  }
  items.forEach((ins) => {
    const card = document.createElement("div");
    card.className =
      "bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 shadow-lg shadow-black/40 p-4 flex flex-col gap-2 hover:-translate-y-[1px] hover:shadow-black/60 transition-transform glass-topline";

    const header = document.createElement("div");
    header.className = "flex items-center gap-2 text-sm font-semibold text-white";

    const icon = document.createElement("span");
    icon.className = "text-lg";
    icon.textContent = ins.icon || "AI";

    const title = document.createElement("span");
    title.textContent = ins.title;

    const subtitle = document.createElement("p");
    subtitle.className = "text-xs text-white/60";
    subtitle.textContent = ins.subtitle || "";

    const description = document.createElement("p");
    description.className = "text-xs text-white/70 leading-relaxed";
    description.textContent = ins.description || "";

    header.append(icon, title);
    card.append(header, subtitle, description);
    grid.appendChild(card);
  });
}

function renderInsightsEmpty() {
  const grid = document.getElementById("insightsGrid");
  grid.innerHTML = `<div class="bg-white/5 border border-white/10 rounded-xl p-4 text-sm text-white/70">Not enough data for analytics.</div>`;
}

function renderSkeletons() {
  const skeletonCard = `<div class="bg-white/5 animate-pulse rounded-2xl h-64"></div>`;
  ["categorySunburstChart", "avgPriceAreaChart", "priceDistChart", "ratingDistChart"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = skeletonCard;
  });
  document.getElementById("insightsGrid").innerHTML = skeletonCard;
  const hoverDetail = document.getElementById("sunburstHoverDetail");
  if (hoverDetail) hoverDetail.textContent = "";
  const list = document.getElementById("topCategoriesList");
  if (list) list.innerHTML = "";
  const kpis = document.getElementById("categoryKpis");
  if (kpis) kpis.innerHTML = "";
  const note = document.getElementById("categoryOtherNote");
  if (note) note.textContent = "";
}

function renderEmptyCharts(message = "Not enough data for analytics.") {
  ["categorySunburstChart", "avgPriceAreaChart", "priceDistChart", "ratingDistChart"].forEach((id) => {
    const el = document.getElementById(id);
    showEmpty(el, message, "Adjust filters to see analytics.");
  });
  const hoverDetail = document.getElementById("sunburstHoverDetail");
  if (hoverDetail) hoverDetail.textContent = "";
  const list = document.getElementById("topCategoriesList");
  if (list) list.innerHTML = "";
  const kpis = document.getElementById("categoryKpis");
  if (kpis) kpis.innerHTML = "";
  const note = document.getElementById("categoryOtherNote");
  if (note) note.textContent = "";
}

function baseChartConfig(type) {
  return {
    chart: {
      type,
      height: "100%",
      parentHeightOffset: 0,
      toolbar: { show: false },
      foreColor: "#e5edff",
      animations: chartAnimations,
    },
    grid: { borderColor: "rgba(255,255,255,0.05)" },
    tooltip: {
      enabled: true,
      theme: "dark",
      style: { fontSize: "12px" },
    },
  };
}

function updateChart(id, options, seriesOnly = false) {
  const existing = apexCharts[id];
  if (existing) {
    if (seriesOnly && options.series) {
      existing.updateSeries(options.series, true);
    } else {
      existing.updateOptions(options, true, true);
    }
  } else {
    const chartEl = document.getElementById(id);
    if (!chartEl) return;
    const chart = new ApexCharts(chartEl, options);
    chart.render();
    apexCharts[id] = chart;
  }
}

function destroyChart(id) {
  const existing = apexCharts[id];
  if (existing) {
    existing.destroy();
    delete apexCharts[id];
  }
}

function renderSunburstLegend(compactEntries, fullEntries, totalProducts, otherCount, showFull) {
  const legendContainer = document.getElementById("sunburstLegend");
  const summary = document.getElementById("legendSummary");
  const hiddenCount = Math.max(0, otherCount);

  const pct = (val) => (totalProducts ? ((val / totalProducts) * 100).toFixed(1) : "0.0");
  const entryValue = (entry) => entry.value ?? entry.count ?? 0;

  legendContainer.innerHTML = "";
  if (showFull) {
    legendContainer.classList.remove("legend-compact");
    legendContainer.classList.add("legend-scroll");
    const wrapper = document.createElement("div");
    wrapper.className = "bg-white/5 border border-white/10 rounded-xl p-3";
    fullEntries.forEach((entry) => {
      const row = document.createElement("div");
      row.className = "legend-item-full";

      const label = document.createElement("span");
      label.textContent = entry.label;

      const value = document.createElement("span");
      value.className = "text-white/60";
      const rawValue = entryValue(entry);
      value.textContent = `${rawValue} (${pct(rawValue)}%)`;

      row.append(label, value);
      wrapper.appendChild(row);
    });
    legendContainer.appendChild(wrapper);
  } else {
    legendContainer.classList.remove("legend-scroll");
    legendContainer.classList.add("legend-compact");
    compactEntries.forEach((entry) => {
      const item = document.createElement("div");
      item.className = "legend-item";
      const rawValue = entryValue(entry);
      if (totalProducts) {
        const pctVal = pct(rawValue);
        item.title = `${entry.label} - ${formatNumber(rawValue)} (${pctVal}%)`;
      }

      const left = document.createElement("div");
      left.className = "legend-item-left";

      const dot = document.createElement("span");
      dot.className = "legend-dot";
      dot.style.backgroundColor = entry.color || "rgba(148, 163, 184, 0.8)";

      const label = document.createElement("span");
      label.textContent = entry.label;

      const value = document.createElement("span");
      value.className = "legend-item-value";
      value.textContent = totalProducts ? `${formatNumber(rawValue)} (${pct(rawValue)}%)` : formatNumber(rawValue);

      left.append(dot, label);
      item.append(left, value);
      legendContainer.appendChild(item);
    });
  }

  summary.textContent = hiddenCount > 0 ? `Other + ${hiddenCount} categories` : `Top ${compactEntries.length} categories`;
}

function renderCategoryKpis(state, topEntry) {
  const container = document.getElementById("categoryKpis");
  if (!container || !topEntry) return;
  container.innerHTML = "";

  const topShare = state.productsCount ? (topEntry.count / state.productsCount) * 100 : 0;
  const topAvgPrice = Number.isFinite(topEntry.avgPrice) ? topEntry.avgPrice.toFixed(2) : "-";
  const topAvgRating = Number.isFinite(topEntry.avgRating) ? topEntry.avgRating.toFixed(2) : "-";

  const items = [
    { label: "Top category", value: topEntry.label },
    { label: "Top share", value: `${topShare.toFixed(1)}%` },
    { label: "Top avg price", value: `GBP ${topAvgPrice}` },
  ];

  if (topAvgRating !== "-") {
    items.push({ label: "Top avg rating", value: topAvgRating });
  }

  items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "bg-white/5 border border-white/10 rounded-xl p-3";

    const label = document.createElement("div");
    label.className = "text-[0.7rem] uppercase tracking-wide text-white/60";
    label.textContent = item.label;

    const value = document.createElement("div");
    value.className = "text-sm font-semibold text-white";
    value.textContent = item.value;

    card.append(label, value);
    container.appendChild(card);
  });
}

function renderTopCategoriesList(entries, metric, totalProducts) {
  const list = document.getElementById("topCategoriesList");
  if (!list) return;
  list.innerHTML = "";

  const visible = entries.filter((entry) => entry.label !== "Other").slice(0, 5);
  const maxMetric = Math.max(
    ...visible.map((entry) => (metric === "avg_price" ? entry.avgPrice || 0 : entry.count || 0)),
    1
  );

  visible.forEach((entry) => {
    const row = document.createElement("div");
    row.className = "space-y-1";
    row.title = metric === "avg_price"
      ? `${entry.label} - ${formatNumber(entry.count)} products`
      : `${entry.label} - ${formatNumber(entry.count)} products`;

    const header = document.createElement("div");
    header.className = "flex items-center justify-between text-xs text-white/80";

    const name = document.createElement("span");
    name.textContent = entry.label;

    const value = document.createElement("span");
    if (metric === "avg_price") {
      value.textContent = `GBP ${(entry.avgPrice || 0).toFixed(2)}`;
    } else {
      const pct = totalProducts ? ((entry.count / totalProducts) * 100).toFixed(1) : "0.0";
      value.textContent = `${formatNumber(entry.count)} (${pct}%)`;
    }

    const track = document.createElement("div");
    track.className = "bg-white/10 rounded-full";
    track.style.height = "6px";

    const fill = document.createElement("div");
    fill.className = "bg-primary/40 rounded-full";
    const metricValue = metric === "avg_price" ? entry.avgPrice || 0 : entry.count || 0;
    const widthPct = Math.max(6, (metricValue / maxMetric) * 100);
    fill.style.height = "100%";
    fill.style.width = `${widthPct}%`;

    track.appendChild(fill);
    header.append(name, value);
    row.append(header, track);
    list.appendChild(row);
  });
}

function renderOtherNote(otherCategoryCount, otherCount, totalProducts, otherAvgPrice, metric) {
  const note = document.getElementById("categoryOtherNote");
  if (!note) return;
  if (!otherCategoryCount) {
    note.textContent = "";
    return;
  }
  const pct = totalProducts ? ((otherCount / totalProducts) * 100).toFixed(1) : "0.0";
  const priceNote = metric === "avg_price" ? ` Avg price GBP ${otherAvgPrice.toFixed(2)}.` : "";
  note.textContent = `Other combines ${otherCategoryCount} categories (${pct}% of products).${priceNote}`;
}

function updateMetricButtons() {
  const countBtn = document.getElementById("metricCountBtn");
  const priceBtn = document.getElementById("metricPriceBtn");
  if (!countBtn || !priceBtn) return;
  const baseClass = "inline-flex items-center px-3 py-1.5 rounded-full border border-white/30 text-xs transition";
  if (categoryMetric === "avg_price") {
    countBtn.className = `${baseClass} bg-white/5 text-white/75 hover:bg-white/10`;
    priceBtn.className = `${baseClass} bg-primary/40 text-white shadow-[0_0_20px_rgba(58,123,255,0.45)]`;
  } else {
    countBtn.className = `${baseClass} bg-primary/40 text-white shadow-[0_0_20px_rgba(58,123,255,0.45)]`;
    priceBtn.className = `${baseClass} bg-white/5 text-white/75 hover:bg-white/10`;
  }
}

function setCategoryMetric(metric) {
  if (metric === categoryMetric) return;
  categoryMetric = metric;
  updateMetricButtons();
  if (lastAnalyticsState) updateCharts(lastAnalyticsState);
}

function renderAvgPriceTable(entries) {
  const container = document.getElementById("avgPriceAreaChart");
  if (!container) return;

  destroyChart("avgPriceAreaChart");
  container.innerHTML = "";

  if (!entries.length) {
    showEmpty(container, "Not enough data for analytics.", "Adjust filters to see analytics.");
    return;
  }

  const maxValue = Math.max(...entries.map((entry) => entry.value), 1);
  const list = document.createElement("div");
  list.className = "text-xs";
  list.style.display = "flex";
  list.style.flexDirection = "column";
  list.style.height = "100%";
  list.style.minHeight = "100%";
  list.style.rowGap = "6px";
  list.style.gap = "6px";

  entries.forEach((entry) => {
    const row = document.createElement("div");
    row.className = "flex items-center gap-2";
    row.style.minHeight = "22px";

    const name = document.createElement("div");
    name.className = "text-xs text-white/75";
    name.textContent = entry.label;
    name.title = entry.label;
    name.style.flex = "0 0 150px";
    name.style.whiteSpace = "nowrap";
    name.style.overflow = "hidden";
    name.style.textOverflow = "ellipsis";

    const barWrap = document.createElement("div");
    barWrap.className = "flex-1 bg-white/10 rounded-full";
    barWrap.style.height = "12px";

    const bar = document.createElement("div");
    bar.className = "bg-primary/40 rounded-full";
    bar.style.height = "100%";
    bar.style.width = `${Math.max(8, (entry.value / maxValue) * 100)}%`;

    const value = document.createElement("div");
    value.className = "text-xs text-white/60";
    value.textContent = `GBP ${entry.value.toFixed(2)}`;
    value.style.flex = "0 0 84px";
    value.style.textAlign = "right";

    barWrap.appendChild(bar);
    row.append(name, barWrap, value);
    list.appendChild(row);
  });

  container.appendChild(list);
}

function updateCharts(state) {
  lastAnalyticsState = state;
  const {
    chartEntries,
    compactEntries,
    fullEntries,
    labels,
    series,
    colors,
    totalProducts,
    otherCategoryCount,
    otherCount,
    otherAvgPrice,
  } = buildCategoryData(state, categoryMetric);

  const topEntry = chartEntries.find((entry) => entry.label !== "Other") || chartEntries[0];
  renderCategoryKpis(state, topEntry);
  renderTopCategoriesList(chartEntries, categoryMetric, totalProducts);
  renderOtherNote(otherCategoryCount, otherCount, totalProducts, otherAvgPrice, categoryMetric);

  lastSunburstData = { compactEntries, fullEntries, totalProducts, otherCount: otherCategoryCount };
  lastSunburstMeta = { labels, series, totalProducts };

  updateChart("categorySunburstChart", {
    ...baseChartConfig("donut"),
    labels,
    series,
    colors,
    legend: { show: false },
    stroke: { show: false },
    dataLabels: { enabled: false },
    states: { hover: { filter: { type: "lighten", value: 0.15 } } },
    tooltip: {
      ...baseChartConfig("donut").tooltip,
      enabled: true,
      followCursor: false,
      fixed: { enabled: true, position: "topRight", offsetX: -12, offsetY: 0 },
      y: {
        formatter: (val, opts) => {
          const entry = chartEntries[opts.seriesIndex];
          if (!entry) return val;
          if (categoryMetric === "avg_price") {
            return `${entry.label} - GBP ${entry.avgPrice.toFixed(2)} avg price (${formatNumber(entry.count)} products)`;
          }
          const pct = totalProducts ? ((entry.count / totalProducts) * 100).toFixed(1) : 0;
          return `${entry.label} - ${formatNumber(entry.count)} products (${pct}%)`;
        },
      },
    },
    plotOptions: {
      pie: {
        donut: {
          size: "70%",
          labels: {
            show: true,
            name: {
              show: true,
              fontSize: "12px",
              offsetY: 8,
              formatter: () => "Products",
            },
            value: {
              show: true,
              fontSize: "22px",
              fontWeight: 700,
              formatter: () => formatNumber(totalProducts),
            },
            total: {
              show: true,
              label: "Categories",
              formatter: () => formatNumber(state.numCategories),
            },
          },
        },
      },
    },
    chart: {
      ...baseChartConfig("donut").chart,
      events: {
        dataPointMouseEnter: (event, chartContext, config) => {
          const idx = config?.dataPointIndex ?? -1;
          if (idx < 0) return;
          const detail = document.getElementById("sunburstHoverDetail");
          if (!detail) return;
          const entry = chartEntries[idx];
          if (!entry) return;
          const pct = totalProducts ? ((entry.count / totalProducts) * 100).toFixed(1) : "0.0";
          const avgPrice = Number.isFinite(entry.avgPrice) ? entry.avgPrice.toFixed(2) : "-";
          const avgRating = Number.isFinite(entry.avgRating) ? entry.avgRating.toFixed(2) : "-";
          detail.textContent = `${entry.label} - ${formatNumber(entry.count)} products (${pct}%) | GBP ${avgPrice} | Rating ${avgRating}`;
        },
        dataPointMouseLeave: () => {
          const detail = document.getElementById("sunburstHoverDetail");
          if (!detail) return;
          detail.textContent = "Hover a slice for details.";
        },
      },
    },
  });

  const hoverDetail = document.getElementById("sunburstHoverDetail");
  if (hoverDetail) hoverDetail.textContent = "Hover a slice for details.";

  renderSunburstLegend(compactEntries, fullEntries, totalProducts, lastSunburstData.otherCount, showFullLegend);

  const avgPriceAll = [...state.avgPricePerCategory]
    .sort((a, b) => b.value - a.value)
  const avgPriceTableEntries = avgPriceAll.map((item) => ({
    label: item.label,
    value: Number(item.value.toFixed(2)),
  }));
  renderAvgPriceTable(avgPriceTableEntries);

  updateChart("priceDistChart", {
    ...baseChartConfig("area"),
    series: [{ name: "Price distribution", data: state.priceDist.values }],
    xaxis: {
      labels: {
        style: { colors: "#e5edff", fontSize: "10px" },
        rotate: -45,
        hideOverlappingLabels: true,
        formatter: (val) => truncateLabel(val, 12),
      },
      categories: state.priceDist.labels,
      tickAmount: Math.min(8, state.priceDist.labels.length),
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: { labels: { style: { colors: "#e5edff", fontSize: "10px" } } },
    stroke: { curve: "smooth", width: 3 },
    markers: { size: 0 },
    fill: { type: "gradient", gradient: { shadeIntensity: 0.8, opacityFrom: 0.35, opacityTo: 0.05, stops: [0, 75, 100] } },
    colors: ["#00f0ff"],
    dataLabels: { enabled: false },
  });

  const ratingKeys = Object.keys(state.ratingDistribution).sort((a, b) => Number(a) - Number(b));
  const ratingValues = ratingKeys.map((key) => state.ratingDistribution[key]);

  updateChart("ratingDistChart", {
    ...baseChartConfig("bar"),
    series: [{ name: "Ratings", data: ratingValues }],
    xaxis: {
      labels: { style: { colors: "#e5edff", fontSize: "10px" } },
      categories: ratingKeys,
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: { labels: { style: { colors: "#e5edff", fontSize: "10px" } } },
    plotOptions: { bar: { columnWidth: "50%", borderRadius: 10 } },
    colors: ["#00f0ff"],
    dataLabels: { enabled: false },
  });

}

function setKpis(stats, filteredLength, generated_at) {
  document.getElementById("kpiCount").textContent = formatNumber(filteredLength);
  document.getElementById("kpiAvgPrice").textContent = stats.avgPrice ? stats.avgPrice.toFixed(2) : "-";
  document.getElementById("kpiMedPrice").textContent = stats.medianPrice ? stats.medianPrice.toFixed(2) : "-";
  document.getElementById("kpiAvgRating").textContent = stats.avgRating ? stats.avgRating.toFixed(2) : "-";
  document.getElementById("kpiCats").textContent = stats.numCategories;
  document.getElementById("generatedAt").textContent = generated_at ? `Generated: ${humanDate(generated_at)}` : "";
}

async function init() {
  const stateFilters = window.EcomState.getFilterState();
  const normalisedFilters = { ...stateFilters, category: normaliseCategoryValue(stateFilters.category) };
  document.getElementById("filterSummary").textContent = filterSummaryText(normalisedFilters);
  renderSkeletons();
  updateMetricButtons();
  updateLegendToggleText();
  try {
    const { products, generated_at } = await loadDataset();
    const normalisedProducts = products.map((p) => ({ ...p, category: normaliseCategoryValue(p.category) }));
    const categorySet = new Set(normalisedProducts.map((p) => p.category || "unknown"));
    if (normalisedFilters.category && !categorySet.has(normalisedFilters.category)) {
      normalisedFilters.category = "";
      window.EcomState.setFilterState(normalisedFilters);
      document.getElementById("filterSummary").textContent = filterSummaryText(normalisedFilters);
    }

    let filtered = window.EcomState.applyFilters(normalisedProducts, normalisedFilters);
    filtered = window.EcomState.applySorting(filtered, normalisedFilters.sort);

    const hasActiveFilters = Boolean(
      normalisedFilters.minPrice ||
        normalisedFilters.maxPrice ||
        normalisedFilters.category ||
        normalisedFilters.minRating ||
        normalisedFilters.availability
    );

    if (!filtered.length) {
      if (hasActiveFilters) {
        window.EcomState.clearFilterState();
        init();
        return;
      }
      document.getElementById("kpiCount").textContent = "0";
      document.getElementById("kpiAvgPrice").textContent = "-";
      document.getElementById("kpiMedPrice").textContent = "-";
      document.getElementById("kpiAvgRating").textContent = "-";
      document.getElementById("kpiCats").textContent = "0";
      document.getElementById("generatedAt").textContent = "";
      renderEmptyCharts();
      renderInsightsEmpty();
      return;
    }

    const stats = computeAnalyticsState(filtered);
    setKpis(stats, filtered.length, generated_at);
    updateCharts(stats);
    renderInsights(generateInsights(stats));
    setTimeout(forceChartsResize, 150);
  } catch (err) {
    document.getElementById("filterSummary").textContent = err.message;
    console.error(err);
    renderEmptyCharts(err.message);
    showError(document.getElementById("insightsGrid"), err.message);
  }
}

const clearBtn = document.getElementById("clearFilters");
if (clearBtn) {
  clearBtn.addEventListener("click", () => {
    window.EcomState.clearFilterState();
    init();
  });
}

const toggleBtn = document.getElementById("toggleLegend");
const toggleInlineBtn = document.getElementById("toggleLegendInline");
function updateLegendToggleText() {
  if (toggleBtn) toggleBtn.textContent = showFullLegend ? "Hide full legend" : "Show full legend";
  if (toggleInlineBtn) toggleInlineBtn.textContent = showFullLegend ? "Hide full legend" : "View all categories";
}
if (toggleBtn) {
  toggleBtn.addEventListener("click", () => {
    showFullLegend = !showFullLegend;
    updateLegendToggleText();
    renderSunburstLegend(
      lastSunburstData.compactEntries,
      lastSunburstData.fullEntries,
      lastSunburstData.totalProducts,
      lastSunburstData.otherCount,
      showFullLegend
    );
  });
}
if (toggleInlineBtn) {
  toggleInlineBtn.addEventListener("click", () => {
    showFullLegend = !showFullLegend;
    updateLegendToggleText();
    renderSunburstLegend(
      lastSunburstData.compactEntries,
      lastSunburstData.fullEntries,
      lastSunburstData.totalProducts,
      lastSunburstData.otherCount,
      showFullLegend
    );
  });
}

const metricCountBtn = document.getElementById("metricCountBtn");
if (metricCountBtn) {
  metricCountBtn.addEventListener("click", () => setCategoryMetric("count"));
}

const metricPriceBtn = document.getElementById("metricPriceBtn");
if (metricPriceBtn) {
  metricPriceBtn.addEventListener("click", () => setCategoryMetric("avg_price"));
}

window.addEventListener("load", () => {
  setTimeout(forceChartsResize, 150);
});

init();
