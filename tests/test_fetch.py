import time

from ecomscrape.config import RequestSettings
from ecomscrape.fetch import FetchRecord, Fetcher


def test_fetch_all_preserves_input_order_with_concurrency(monkeypatch):
    fetcher = Fetcher(RequestSettings(max_workers=2, delay_between_requests=0))

    def fake_fetch(url):
        if url.endswith("slow"):
            time.sleep(0.05)
        return FetchRecord(url=url, html=url, headers={}, status_code=200)

    monkeypatch.setattr(fetcher, "fetch", fake_fetch)

    urls = ["https://example.com/slow", "https://example.com/fast"]
    results = fetcher.fetch_all(urls)

    assert [record.url for record in results] == urls
