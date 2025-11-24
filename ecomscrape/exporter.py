from __future__ import annotations

import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd

LOGGER = logging.getLogger(__name__)


def _timestamp() -> str:
    # Use an immutable timestamp to version each export run.
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: Path) -> None:
    # Ensure target directories exist without erroring if already present.
    path.mkdir(parents=True, exist_ok=True)


def _to_dataframe(data: Any) -> pd.DataFrame:
    # Accept either DataFrames or lists of dataclasses/dicts to keep callers flexible.
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, list) and data and is_dataclass(data[0]):
        return pd.DataFrame([asdict(item) for item in data])
    return pd.DataFrame(data)


def export_dataframe(df: pd.DataFrame | Iterable[Dict[str, Any]], formats: Iterable[str], output_dir: Path) -> Dict[str, Path]:
    df = _to_dataframe(df)
    ensure_dir(output_dir)
    formats = set(fmt.lower() for fmt in formats)
    base = output_dir / f"products_{_timestamp()}"
    paths: Dict[str, Path] = {}

    if "csv" in formats:
        csv_path = base.with_suffix(".csv")
        df.to_csv(csv_path, index=False)
        paths["csv"] = csv_path
        LOGGER.info("Exported CSV: %s", csv_path)

    if "excel" in formats or "xlsx" in formats:
        xlsx_path = base.with_suffix(".xlsx")
        df.to_excel(xlsx_path, index=False, engine="openpyxl")
        paths["excel"] = xlsx_path
        LOGGER.info("Exported Excel: %s", xlsx_path)

    if "json" in formats:
        json_path = base.with_suffix(".json")
        df.to_json(json_path, orient="records", indent=2)
        paths["json"] = json_path
        LOGGER.info("Exported JSON: %s", json_path)

    return paths


def write_latest_json(df: pd.DataFrame, output_dir: Path) -> Optional[Path]:
    ensure_dir(output_dir)
    latest_path = output_dir / "latest_products.json"
    try:
        df.to_json(latest_path, orient="records", indent=2)
        LOGGER.debug("Wrote latest JSON snapshot: %s", latest_path)
        return latest_path
    except Exception as exc:  # keep scraping resilient
        LOGGER.warning("Failed to write latest JSON snapshot: %s", exc)
        return None
