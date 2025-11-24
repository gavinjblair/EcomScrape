import textwrap

import pytest

from ecomscrape.config import ConfigError, load_config


def test_load_config_valid(tmp_path):
    # Ensure a minimal valid config loads and populates expected fields.
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        textwrap.dedent(
            """
            site_name: "test"
            start_urls: ["http://example.com"]
            parsing:
              product_container: "div.item"
              fields:
                name:
                  selector: ".name"
            """
        ),
        encoding="utf-8",
    )

    result = load_config(cfg)
    assert result.site_name == "test"
    assert result.parsing.product_container == "div.item"
    assert "name" in result.parsing.fields


def test_load_config_missing_required(tmp_path):
    # Omit site_name to confirm we raise a clear ConfigError.
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        textwrap.dedent(
            """
            start_urls: ["http://example.com"]
            parsing:
              product_container: "div.item"
              fields:
                name:
                  selector: ".name"
            """
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_config(cfg)
