from ecomscrape.config import FieldSelector, ParsingConfig
from ecomscrape.parser import Parser


HTML = """
<html>
  <body>
    <section>
      <article class="product_pod">
        <h3><a href="book-1.html" title="Book 1">Book 1</a></h3>
        <p class="price_color">£51.77</p>
        <p class="instock availability">
          In stock
        </p>
        <p class="star-rating Three">Three</p>
      </article>
      <article class="product_pod">
        <h3><a href="book-2.html" title="Book 2">Book 2</a></h3>
        <p class="price_color">£45.17</p>
        <p class="instock availability">
          In stock
        </p>
        <p class="star-rating Five">Five</p>
      </article>
    </section>
  </body>
</html>
"""


def test_parser_extracts_products():
    # Confirm parser pulls the expected number of items and key fields.
    parsing = ParsingConfig(
        product_container="article.product_pod",
        fields={
            "name": FieldSelector(selector="h3 a", attribute="title"),
            "url": FieldSelector(selector="h3 a", attribute="href", join_base_url=True),
            "price_current": FieldSelector(selector="p.price_color", attribute="text"),
            "availability": FieldSelector(selector="p.instock.availability", attribute="text"),
            "rating": FieldSelector(selector="p.star-rating", attribute="class"),
        },
    )
    parser = Parser(parsing, base_url="https://books.toscrape.com/")

    products = parser.parse(HTML, source_url="https://books.toscrape.com/catalogue/page-1.html")

    assert len(products) == 2
    assert products[0]["name"] == "Book 1"
    assert products[0]["url"].endswith("book-1.html")
    assert products[0]["price_current"].startswith("£")
