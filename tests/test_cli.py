import logging
from types import SimpleNamespace

from ecomscrape.cli import _discover_link_pagination, _enrich_details
from ecomscrape.config import PaginationConfig
from ecomscrape.fetch import FetchRecord
from ecomscrape.site_adapters import DetailFields, SiteAdapter


class StubPaginationFetcher:
    def __init__(self, html_by_url):
        self.html_by_url = html_by_url

    def fetch(self, url):
        return FetchRecord(url=url, html=self.html_by_url.get(url), headers={}, status_code=200)


class StubEnrichmentFetcher:
    def __init__(self, results):
        self.settings = SimpleNamespace(delay_between_requests=0, max_workers=2)
        self._results = results

    def fetch_all(self, urls):
        return list(self._results)


class StubAdapter(SiteAdapter):
    def prepare_product_url(self, url: str) -> str:
        return url

    def extract_detail_fields(self, html: str) -> DetailFields:
        category, description = html.split("|", 1)
        return DetailFields(category=category, description=description)


def test_discover_link_pagination_follows_next_links():
    start_url = "https://example.com/page-1.html"
    page_2 = "https://example.com/page-2.html"
    page_3 = "https://example.com/page-3.html"
    fetcher = StubPaginationFetcher(
        {
            start_url: '<html><body><a class="next" href="page-2.html">Next</a></body></html>',
            page_2: '<html><body><a class="next" href="/page-3.html">Next</a></body></html>',
            page_3: "<html><body>No next page</body></html>",
        }
    )
    pagination = PaginationConfig(mode="link", next_selector="a.next", max_pages=5)

    urls, html_cache = _discover_link_pagination(
        start_url,
        pagination,
        fetcher,
        dry_run=False,
        logger=logging.getLogger("test_cli"),
    )

    assert urls == [start_url, page_2, page_3]
    assert html_cache[page_2].startswith("<html>")
    assert html_cache[page_3] == "<html><body>No next page</body></html>"


def test_enrich_details_matches_results_by_url_even_if_fetcher_returns_out_of_order():
    records = [
        {"product_url": "https://example.com/product-1", "category": "unknown"},
        {"product_url": "https://example.com/product-2", "category": "unknown"},
    ]
    fetcher = StubEnrichmentFetcher(
        [
            FetchRecord(
                url="https://example.com/product-2",
                html="Category Two|Description Two",
                headers={},
                status_code=200,
            ),
            FetchRecord(
                url="https://example.com/product-1",
                html="Category One|Description One",
                headers={},
                status_code=200,
            ),
        ]
    )

    _enrich_details(records, fetcher, logging.getLogger("test_cli"), StubAdapter())

    assert records[0]["category"] == "Category One"
    assert records[0]["description"] == "Description One"
    assert records[1]["category"] == "Category Two"
    assert records[1]["description"] == "Description Two"
