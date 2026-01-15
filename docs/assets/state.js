(() => {
  const defaultFilters = {
    minPrice: "",
    maxPrice: "",
    category: "",
    minRating: "",
    availability: "",
    sort: "title_asc",
  };

  const STORAGE_KEY = "ecomscrape_filters_v1";
  const THEME_KEY = "ecomscrape_theme";

  function getFilterState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? { ...defaultFilters, ...JSON.parse(raw) } : { ...defaultFilters };
    } catch {
      return { ...defaultFilters };
    }
  }

  function setFilterState(newState) {
    const merged = { ...getFilterState(), ...newState };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
    return merged;
  }

  function clearFilterState() {
    localStorage.removeItem(STORAGE_KEY);
    return { ...defaultFilters };
  }

  function getTheme() {
    const saved = localStorage.getItem(THEME_KEY);
    return saved || "light";
  }

  function applyTheme(theme) {
    document.body.classList.toggle("dark-theme", theme === "dark");
  }

  function setTheme(theme) {
    localStorage.setItem(THEME_KEY, theme);
    applyTheme(theme);
  }

  function toggleTheme() {
    const next = getTheme() === "dark" ? "light" : "dark";
    setTheme(next);
    syncThemeToggleText();
    return next;
  }

  function applyFilters(products, filters) {
    return products.filter(p => {
      const price = parseFloat(p.price_current ?? p.price ?? p.price_original);
      const rating = parseFloat(p.rating ?? 0);
      if (filters.minPrice && (isNaN(price) || price < parseFloat(filters.minPrice))) return false;
      if (filters.maxPrice && (isNaN(price) || price > parseFloat(filters.maxPrice))) return false;
      if (filters.category && String(p.category || "unknown").toLowerCase() !== filters.category.toLowerCase()) return false;
      if (filters.minRating && (!rating || rating < parseFloat(filters.minRating))) return false;
      if (filters.availability && filters.availability === "in_stock") {
        const avail = String(p.availability || "").toLowerCase();
        const isInStock = avail.includes("in stock") || avail.includes("available") || avail.includes("in_stock");
        if (!isInStock) return false;
      }
      return true;
    });
  }

  function applySorting(products, sortKey) {
    const list = [...products];
    switch (sortKey) {
      case "price_asc":
        return list.sort((a, b) => (parseFloat(a.price_current ?? a.price ?? 0) || 0) - (parseFloat(b.price_current ?? b.price ?? 0) || 0));
      case "price_desc":
        return list.sort((a, b) => (parseFloat(b.price_current ?? b.price ?? 0) || 0) - (parseFloat(a.price_current ?? a.price ?? 0) || 0));
      case "rating_desc":
        return list.sort((a, b) => (parseFloat(b.rating ?? 0) || 0) - (parseFloat(a.rating ?? 0) || 0));
      case "title_desc":
        return list.sort((a, b) => String(b.title || "").localeCompare(String(a.title || "")));
      case "title_asc":
      default:
        return list.sort((a, b) => String(a.title || "").localeCompare(String(b.title || "")));
    }
  }

  // Update any theme toggle button text/label
  function syncThemeToggleText() {
    const btns = document.querySelectorAll(".theme-toggle-btn");
    const theme = getTheme();
    const label = theme === "dark" ? "Light Mode" : "Dark Mode";
    btns.forEach(b => b.textContent = label);
  }

  window.EcomState = {
    getFilterState,
    setFilterState,
    clearFilterState,
    applyFilters,
    applySorting,
    getTheme,
    setTheme,
    toggleTheme,
    applyTheme,
    defaultFilters,
    syncThemeToggleText,
  };

  // Apply persisted theme immediately
  applyTheme(getTheme());
  syncThemeToggleText();
})();
