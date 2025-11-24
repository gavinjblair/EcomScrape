from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
]


class ConfigError(Exception):
    """Raised when a configuration file is invalid."""


@dataclass
class RequestSettings:
    timeout: float = 10.0
    max_retries: int = 3
    backoff_factor: float = 0.5
    delay_between_requests: float = 0.0
    max_workers: int = 1
    retry_status_forcelist: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    user_agents: List[str] = field(default_factory=lambda: DEFAULT_USER_AGENTS.copy())
    headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class PaginationConfig:
    mode: Optional[str] = None  # link | format
    next_selector: Optional[str] = None
    max_pages: int = 20
    url_template: Optional[str] = None
    start: int = 1
    end: int = 1


@dataclass
class CleaningConfig:
    rating_words: Dict[str, float] = field(default_factory=dict)
    availability_map: Dict[str, str] = field(default_factory=dict)


@dataclass
class FieldSelector:
    selector: str
    attribute: Optional[str] = None  # None or "text" will use the node text
    join_base_url: bool = False


@dataclass
class ParsingConfig:
    product_container: str
    fields: Dict[str, FieldSelector]


@dataclass
class ScraperConfig:
    site_name: str
    start_urls: List[str]
    base_url: Optional[str]
    request: RequestSettings
    parsing: ParsingConfig
    pagination: Optional[PaginationConfig] = None
    cleaning: CleaningConfig = field(default_factory=CleaningConfig)
    currency: Optional[str] = None
    max_products: Optional[int] = None


def _load_raw_config(path: Path) -> Dict[str, Any]:
    # Guard against missing or unsupported config files to fail early for users.
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    raise ConfigError(f"Unsupported config extension: {path.suffix}")


def _require(value: Any, key: str) -> Any:
    # Enforce mandatory keys with a clear message.
    if value is None:
        raise ConfigError(f"Missing required config key: {key}")
    return value


def load_config(path: Path | str) -> ScraperConfig:
    """
    Load and validate a scraper configuration file.
    """
    config_path = Path(path)
    raw = _load_raw_config(config_path) or {}

    site_name = _require(raw.get("site_name"), "site_name")
    start_urls = _require(raw.get("start_urls"), "start_urls")
    if not isinstance(start_urls, list) or not start_urls:
        raise ConfigError("start_urls must be a non-empty list")

    base_url = raw.get("base_url") or None
    max_products = raw.get("max_products")
    currency = raw.get("currency")

    # Request settings with defaults
    request_raw = raw.get("request", {}) or {}
    request = RequestSettings(
        timeout=float(request_raw.get("timeout", 10.0)),
        max_retries=int(request_raw.get("max_retries", 3)),
        backoff_factor=float(request_raw.get("backoff_factor", 0.5)),
        delay_between_requests=float(request_raw.get("delay_between_requests", 0.0)),
        max_workers=int(request_raw.get("max_workers", 1)),
        retry_status_forcelist=list(request_raw.get("retry_status_forcelist", [429, 500, 502, 503, 504])),
        user_agents=request_raw.get("user_agents") or DEFAULT_USER_AGENTS.copy(),
        headers=request_raw.get("headers") or {},
    )

    pagination_cfg = None
    if raw.get("pagination"):
        pagination_raw = raw["pagination"] or {}
        pagination_cfg = PaginationConfig(
            mode=pagination_raw.get("mode"),
            next_selector=pagination_raw.get("next_selector"),
            max_pages=int(pagination_raw.get("max_pages", 20)),
            url_template=pagination_raw.get("url_template"),
            start=int(pagination_raw.get("start", 1)),
            end=int(pagination_raw.get("end", pagination_raw.get("start", 1))),
        )

    cleaning_raw = raw.get("cleaning") or {}
    cleaning_cfg = CleaningConfig(
        rating_words=cleaning_raw.get("rating_words") or {},
        availability_map=cleaning_raw.get("availability_map") or {},
    )

    parsing_raw = _require(raw.get("parsing"), "parsing")
    product_container = _require(parsing_raw.get("product_container"), "parsing.product_container")
    fields_raw = _require(parsing_raw.get("fields"), "parsing.fields")
    fields: Dict[str, FieldSelector] = {}
    for key, val in fields_raw.items():
        if not isinstance(val, dict) or "selector" not in val:
            raise ConfigError(f"Each field under parsing.fields must define a selector ({key})")
        fields[key] = FieldSelector(
            selector=val["selector"],
            attribute=val.get("attribute"),
            join_base_url=bool(val.get("join_base_url", False)),
        )
    parsing = ParsingConfig(product_container=product_container, fields=fields)

    logging.debug("Loaded config for site '%s' from %s", site_name, config_path)
    return ScraperConfig(
        site_name=site_name,
        start_urls=start_urls,
        base_url=base_url,
        request=request,
        parsing=parsing,
        pagination=pagination_cfg,
        cleaning=cleaning_cfg,
        currency=currency,
        max_products=max_products,
    )
