from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .cleaner import clean_products
from .config import ConfigError, ScraperConfig, load_config
from .exporter import export_dataframe, write_latest_json
from .fetch import Fetcher
from .parser import Parser


def setup_logging(debug: bool, log_file: Path) -> logging.Logger:
    # Configure console and file logging so users get both immediate and persistent feedback.
    logger = logging.getLogger("ecomscrape")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if debug else logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )

    logger.addHandler(console)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    # Expose a friendly CLI with short flags for common options.
    parser = argparse.ArgumentParser(description="Scrape e-commerce products and export cleaned data.")
    parser.add_argument("-c", "--config", required=True, help="Path to YAML/JSON config file.")
    parser.add_argument(
        "-f",
        "--format",
        nargs="+",
        default=["csv", "excel"],
        choices=["csv", "excel", "json"],
        help="Export formats.",
    )
    parser.add_argument("--max-products", type=int, help="Maximum number of products to keep from the scrape.")
    parser.add_argument("-o", "--output-dir", default="outputs/processed", help="Directory for exported files.")
    parser.add_argument("--log-file", default="outputs/scrape.log", help="Path for the log file.")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and parse without exporting files.")
    parser.add_argument(
        "--save-raw-html",
        action="store_true",
        help="Persist raw HTML responses to outputs/raw for debugging.",
    )
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging.")
    return parser.parse_args(argv)


def _generate_format_urls(pagination, logger: logging.Logger) -> List[str]:
    # Expand templated URLs for simple numbered pagination.
    start = pagination.start or 1
    end = pagination.end or start
    if not pagination.url_template:
        raise ConfigError("pagination.url_template is required when pagination.mode == 'format'")
    urls = [pagination.url_template.format(i) for i in range(start, end + 1)]
    logger.debug("Generated %s URLs from pagination template", len(urls))
    return urls


def _discover_link_pagination(
    start_url: str, pagination, fetcher: Fetcher, dry_run: bool, logger: logging.Logger
) -> Tuple[List[str], Dict[str, str]]:
    # Walk next-page links until exhausted or max_pages reached, caching HTML where possible.
    urls: List[str] = []
    html_cache: Dict[str, str] = {}
    current_url = start_url
    pages = 0
    max_pages = pagination.max_pages or 1

    while current_url and pages < max_pages:
        record = fetcher.fetch(current_url)
        if not record.html:
            break
        urls.append(current_url)
        html_cache[current_url] = record.html
        pages += 1
        if dry_run:
            logger.debug("Dry run pagination: stopping after first page.")
            break
        soup = BeautifulSoup(record.html, "lxml")
        next_node = soup.select_one(pagination.next_selector) if pagination.next_selector else None
        if not next_node:
            break
        href = next_node.get("href")
        if not href:
            break
        next_url = urljoin(current_url, href)
        if next_url in urls:
            break
        current_url = next_url

    logger.debug("Discovered %s paginated URLs starting from %s", len(urls), start_url)
    return urls, html_cache


def _build_url_plan(
    scraper_config: ScraperConfig, fetcher: Fetcher, dry_run: bool, logger: logging.Logger
) -> Tuple[List[str], Dict[str, str]]:
    # Decide whether to use provided URLs, expand templates, or discover links.
    pagination = scraper_config.pagination
    html_cache: Dict[str, str] = {}
    if not pagination or not pagination.mode:
        return list(scraper_config.start_urls), html_cache

    if pagination.mode == "format":
        return _generate_format_urls(pagination, logger), html_cache

    if pagination.mode == "link":
        all_urls: List[str] = []
        for start_url in scraper_config.start_urls:
            urls, cache = _discover_link_pagination(start_url, pagination, fetcher, dry_run, logger)
            all_urls.extend(urls)
            html_cache.update(cache)
        return all_urls, html_cache

    raise ConfigError(f"Unsupported pagination mode: {pagination.mode}")


def run(argv: List[str] | None = None) -> int:
    # Main orchestration for CLI usage.
    args = parse_args(argv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = Path(args.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(debug=args.debug, log_file=log_file)

    try:
        scraper_config = load_config(args.config)
    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        return 1

    logger.info("Starting scrape for site '%s'", scraper_config.site_name)
    fetcher = Fetcher(scraper_config.request, logger=logger)
    parser = Parser(scraper_config.parsing, base_url=scraper_config.base_url, logger=logger)

    urls_to_fetch, html_cache = _build_url_plan(scraper_config, fetcher, args.dry_run, logger)

    raw_records: List[dict] = []
    raw_html_dir = Path("outputs/raw")
    if args.save_raw_html:
        raw_html_dir.mkdir(parents=True, exist_ok=True)

    pages: List[Tuple[str, str]] = []
    if (
        scraper_config.request.max_workers > 1
        and not html_cache
        and not args.dry_run
        and len(urls_to_fetch) > 1
    ):
        records = fetcher.fetch_all(urls_to_fetch)
        pages = [(rec.url, rec.html) for rec in records if rec.html]
    else:
        for url in urls_to_fetch:
            cached_html = html_cache.get(url)
            record = fetcher.fetch(url) if cached_html is None else None
            html = cached_html or (record.html if record else None)
            if html:
                pages.append((url, html))
            if args.dry_run:
                logger.info("Dry run enabled; fetched first page only.")
                break

    for idx, (url, html) in enumerate(pages, start=1):
        if args.save_raw_html:
            raw_path = raw_html_dir / f"page_{idx}.html"
            raw_path.write_text(html, encoding="utf-8")
            logger.debug("Saved raw HTML for %s to %s", url, raw_path)
        records = parser.parse(html, source_url=url)
        raw_records.extend(records)
        if scraper_config.max_products and len(raw_records) >= scraper_config.max_products:
            raw_records = raw_records[: scraper_config.max_products]
            break
        if args.max_products and len(raw_records) >= args.max_products:
            raw_records = raw_records[: args.max_products]
            break

    if args.dry_run:
        logger.info("Dry run: parsed %s products; skipping export.", len(raw_records))
        return 0

    products, cleaned_df = clean_products(
        raw_records, currency=scraper_config.currency, cleaning=scraper_config.cleaning
    )
    if cleaned_df.empty:
        logger.warning("No products were parsed; exports will be empty.")

    exported_paths = export_dataframe(cleaned_df, args.format, output_dir=output_dir)
    latest_json = write_latest_json(cleaned_df, output_dir=output_dir)

    summary = fetcher.summary()
    logger.info("Requests completed: %s success, %s failure", summary["successes"], summary["failures"])
    logger.info("Exported files: %s", ", ".join(str(p) for p in exported_paths.values()))
    if latest_json:
        logger.info("Latest snapshot: %s", latest_json)
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
