# EcomScrape – E-commerce Product Scraper & Data Exporter

## 1. Project Overview

### 1.1 Project Title

**EcomScrape – E-commerce Product Scraper & Data Exporter**

### 1.2 Objective

To build a robust, configurable Python tool that scrapes product data from e-commerce sites, cleans and normalises it using Pandas, and exports ready-to-use CSV and Excel files, with optional JSON/API output for integration into other systems.

### 1.3 Problem Statement

Analysts, developers, and small businesses often need structured product data (prices, availability, ratings, etc.) from e-commerce sites. Manual collection is slow and error-prone, and many existing tools are either paid, difficult to customise, or provide messy, uncleaned data. There is a need for a reusable, configurable scraper that can reliably collect, clean, and export product data with minimal manual intervention.

### 1.4 Target Users

- Data analysts and data scientists performing pricing and competitor analysis.
- Backend developers integrating external product data into internal tools.
- Small e-commerce business owners monitoring competitor prices.
- Students/learners wanting a realistic web scraping + data cleaning project.

### 1.5 Value Proposition

EcomScrape provides an end-to-end pipeline: **Scrape → Clean → Validate → Export → (Optionally) Serve via API**.

Key value points:

- Config-driven (site selectors, headers, URLs) so it can be reused across multiple sites.
- Built-in error handling, retry logic, and rotating headers to improve robustness.
- Clean, normalised outputs suitable for Excel and data analysis tools.
- Optional REST API so the scraper can be used as a service, not just a script.

### 1.6 Success Criteria

- Successfully scrape and clean ≥ 200 products from at least one e-commerce site (or demo site).
- Export cleaned product data to both CSV and Excel with correct column types.
- Handle common network errors and parsing issues without crashing (graceful failure + logging).
- Implement rotating User-Agent headers and verify behaviour via logs.
- Provide at least one working API endpoint returning product data as JSON.
- Document installation, configuration, and usage clearly so another person can run the tool.

---

## 2. Requirements

### 2.1 Functional Requirements

The system shall:

- Fetch HTML content from one or more configured e-commerce URLs.
- Parse product attributes using selectors defined in a configuration file (YAML/JSON), including at minimum:
  - Product name
  - Product URL
  - Current price
  - (Optional) Original price
  - Availability status
  - Rating (if present)
  - Number of reviews (if present)
  - Category (if present)
  - Image URL (optional)
- Load scraped data into a Pandas DataFrame.
- Clean and normalise data, including:
  - Converting price strings to numeric values.
  - Converting review counts to integers.
  - Standardising availability values into a fixed set of categories.
- Export cleaned data to:
  - CSV files.
  - Excel files.
- Log key events and errors (e.g. failed requests, parse errors, export errors).
- Support rotating HTTP headers (e.g. multiple User-Agent strings) on requests.
- Implement retry logic and timeouts for HTTP requests.
- Provide a CLI interface to:
  - Select a configuration file.
  - Choose export format(s).
  - Optionally set a maximum number of products.
- (Optional) Provide a REST API to:
  - Return the latest product dataset as JSON.
  - Optionally filter results by price, category, or availability.

### 2.2 Non-Functional Requirements

**Performance**

- Able to scrape and process several hundred products within a reasonable time on a standard desktop and connection.

**Reliability**

- No unhandled exceptions for expected network or parsing errors.
- Clear logging to support troubleshooting.

**Maintainability**

- Modular structure (separate modules for fetching, parsing, cleaning, exporting, API).
- Site-specific details defined in external configuration files.

**Usability**

- Simple CLI usage with help text and examples.
- Clear error messages that indicate what went wrong and how to fix it.

**Portability**

- Runs on Windows (primary) and should work on other platforms with Python 3.10+ and minimal changes.

**Security**

- No hard-coded credentials or sensitive data in the codebase.
- Designed to respect target sites’ robots.txt and terms of use.

### 2.3 Constraints

- Must be implemented using Python and open-source libraries.
- Primary HTTP approach should use lightweight HTTP clients (`requests`/`httpx`) rather than heavy browser automation, except where absolutely necessary.
- Only publicly accessible product pages will be scraped (no login-protected or paywalled content).
- Project is intended for educational and portfolio purposes and must use conservative scraping practices (delays, limited volume).

### 2.4 Assumptions

- Target e-commerce pages use reasonably consistent HTML structure within a site.
- Target sites do not aggressively block polite, low-frequency scraping with rotating headers.
- The volume of data (hundreds to low thousands of rows) is manageable on a typical local machine using Pandas.
- Users are able to edit configuration files and run Python scripts from the command line.

### 2.5 Out of Scope

- Bypassing sophisticated anti-bot systems (e.g. CAPTCHAs, advanced JavaScript challenges).
- Scraping authenticated or paywalled areas requiring login.
- Large-scale crawling of entire domains or thousands of pages.
- Advanced analytics or machine learning on top of scraped data (could be a separate project).
- A fully polished graphical desktop application.

---

## 3. User Personas

### Persona 1 – Alex

- **Role:** Junior Data Analyst  
- **Goals:**
  - Quickly obtain structured product data for pricing and competitor analysis.
- **Needs:**
  - Simple commands to run the scraper.
  - Clean CSV/Excel files that load into Excel, Power BI, or Python notebooks.
- **Frustrations:**
  - Manual copy-and-paste from websites.
  - Inconsistent data formats causing spreadsheet errors.
- **Technical Ability:**
  - Comfortable with basic Python and command line.
- **Scenario of Use:**
  - Alex runs `python cli.py --config configs/site1.yaml --format csv excel`, then opens the resulting files in Excel to compare prices across categories.

### Persona 2 – Priya

- **Role:** Backend Developer  
- **Goals:**
  - Integrate competitor product data into an internal service.
- **Needs:**
  - A scriptable tool that can be automated and, ideally, exposed via a REST API.
- **Frustrations:**
  - Having to rewrite one-off scrapers for each new site.
  - Brittle code that breaks when page structure changes.
- **Technical Ability:**
  - Strong Python and web service experience.
- **Scenario of Use:**
  - Priya deploys the scraper, runs it regularly, and queries `GET /products` from another service to pull in structured product data.

### Persona 3 – Jamie

- **Role:** Small E-commerce Business Owner  
- **Goals:**
  - Track competitor pricing for key products without paying for expensive SaaS tools.
- **Needs:**
  - Clear instructions and outputs in Excel format.
- **Frustrations:**
  - Time-consuming manual checks of competitor websites.
  - Tools that are too technical or require coding.
- **Technical Ability:**
  - Basic computer skills; can follow step-by-step instructions.
- **Scenario of Use:**
  - Jamie uses a pre-configured script or batch file that runs the scraper and produces an Excel file of competitor prices for weekly review.

---

## 4. User Stories & Acceptance Criteria

### User Story 1 – Export Cleaned Product Data

**Story**

> As a data analyst, I want to export cleaned product data to CSV and Excel so that I can easily analyse it in Excel or BI tools.

**Acceptance Criteria**

- When I run the CLI with `--format csv excel`, the system generates:
  - A timestamped CSV file in an `outputs/processed/` directory.
  - A timestamped Excel file in an `outputs/processed/` directory.
- Both files contain consistent column headers (e.g. `name`, `url`, `price_current`, `availability`, `rating`, etc.).
- Price columns are numeric, and review counts are integers where possible.
- If export fails, a clear error message is displayed and logged.

### User Story 2 – Rotating Request Headers

**Story**

> As a developer, I want the scraper to rotate request headers so that it behaves more like genuine browser traffic and is less likely to be blocked.

**Acceptance Criteria**

- A list of User-Agent strings is defined in the configuration file.
- Each outgoing HTTP request uses one of the configured User-Agent values.
- The header used per request is visible in debug logs.
- If header rotation is disabled in configuration, a default header is used.

### User Story 3 – Robust Network Error Handling

**Story**

> As a user, I want the scraper to handle network errors without crashing so that temporary issues do not stop the entire scrape.

**Acceptance Criteria**

- Network timeouts and 5xx responses trigger retries up to a configured maximum.
- Failed URLs after all retries are logged, and the script continues with other URLs.
- At the end of the run, the script outputs a summary (e.g. successful pages, failed pages).
- No unhandled exceptions are raised for standard network error conditions.

### User Story 4 – Optional REST API

**Story**

> As a backend developer, I want to retrieve scraped product data via a REST API so that I can integrate it into other systems.

**Acceptance Criteria**

- `GET /products` returns a JSON response containing an array of product objects matching the defined schema.
- The endpoint returns HTTP 200 on success.
- If no data is available, the endpoint returns an empty list or an informative message.
- (Optional) Query parameters such as `min_price`, `max_price`, or `category` filter the results.

---

## 5. System Architecture

### 5.1 High-Level Architecture Overview

The system follows a modular pipeline:

1. **Configuration Loader** – Reads a YAML/JSON file specifying site URLs, selectors, headers, and settings.
2. **HTTP Client (Fetcher)** – Sends HTTP requests with timeouts, retries, and rotating headers to retrieve HTML.
3. **Parser** – Extracts raw product fields from HTML using selectors defined in the configuration.
4. **Data Cleaner (Pandas)** – Loads raw records into a DataFrame and applies cleaning, normalisation, and validation.
5. **Exporter** – Writes cleaned data to CSV and Excel.
6. **API Layer (optional)** – Exposes the cleaned dataset via REST endpoints.
7. **CLI Interface** – Orchestrates the above components based on user arguments.

### 5.2 Architecture Diagram (Textual)

Suggested diagram:

```text
Config File → HTTP Client → Parser → Data Cleaner (Pandas) → Exporter (CSV/Excel)
        ↘ Optional API (JSON responses)
```

### 5.3 Component Descriptions

- **config.py** – Loads and validates configuration files, exposes site settings to other modules.
- **fetch.py** – Handles HTTP requests, header rotation, retries, and logging of responses/errors.
- **parser.py** – Uses an HTML parser (e.g. BeautifulSoup/lxml) and config-defined selectors to extract product attributes.
- **cleaner.py** – Contains Pandas functions to convert and standardise prices, availability, ratings, review counts, etc.
- **exporter.py** – Exports DataFrames to CSV and Excel, applies basic formatting (e.g. header row, numeric formats).
- **api.py** – Implements a FastAPI/Flask app providing `GET /products` (and possibly other endpoints).
- **cli.py** – Provides a command-line interface (argument parsing) and orchestrates the scrape–clean–export workflow.

### 5.4 Tech Stack Justification

- **Python** – Mature ecosystem for web scraping and data processing.
- **requests/httpx** – Lightweight, flexible HTTP client libraries well suited to scraping tasks.
- **BeautifulSoup / lxml** – Widely used HTML parsing libraries with good performance and community support.
- **Pandas** – Industry-standard library for tabular data cleaning, transformation, and exporting.
- **openpyxl/XlsxWriter** – Enable more control over Excel generation than default Pandas output alone.
- **FastAPI/Flask** – Allow quick creation of REST APIs; FastAPI also offers automatic documentation.
- **argparse/typer** – Support a clean, user-friendly CLI interface.

---

## 6. Data Model & Schema Design

### 6.1 Entities & Relationships

Primary entity: **Product**

Suggested attributes:

- `id` (internal integer or UUID; optional)
- `name` (string)
- `url` (string)
- `price_current` (float)
- `price_original` (float, nullable)
- `currency` (string, nullable or derived)
- `availability` (string; e.g. `in_stock`, `out_of_stock`, `preorder`, `unknown`)
- `rating` (float, nullable)
- `review_count` (integer, nullable)
- `category` (string, nullable)
- `image_url` (string, nullable)
- `scraped_at` (datetime)

In a simple version, each product is independent. If extended, additional entities might include **Site** (metadata about the e-commerce site) or **Category** as separate tables.

### 6.2 ER Diagram (Textual)

Suggested ER diagram:

- **Product** (single entity) with attributes listed above.
- Optional **Site** entity with a one-to-many relationship to Product.

### 6.3 API Data Contracts / JSON Schemas

**Example Product JSON shape:**

```json
{
  "name": "Example Product",
  "url": "https://example.com/product/123",
  "price_current": 19.99,
  "price_original": 29.99,
  "currency": "GBP",
  "availability": "in_stock",
  "rating": 4.5,
  "review_count": 123,
  "category": "Headphones",
  "image_url": "https://example.com/images/123.jpg",
  "scraped_at": "2025-01-01T12:00:00Z"
}
```

**Example `GET /products` response:**

```json
{
  "products": [ /* array of products */ ],
  "count": 250,
  "generated_at": "2025-01-01T12:05:00Z"
}
```

---

## 7. UI/UX Planning

### 7.1 Wireframes (Conceptual)

Planned interfaces:

1. **CLI Interface (Text-based)**
   - Clear help text (`--help`) describing all options.
   - Concise summary at the end of a run (number of products, files created, any failures).

2. **Optional Streamlit Web UI (Stretch Goal)**
   - Simple page with:
     - Dropdown to select configuration/site.
     - "Run Scrape" button.
     - Summary statistics (e.g. product count, average price).
     - Data preview table.
     - Buttons to download CSV and Excel files.

### 7.2 User Flows

**Flow 1 – Analyst Running a One-off Scrape**

1. Selects or edits a config file for the target site.
2. Runs the CLI: `python cli.py --config configs/site1.yaml --format csv excel`.
3. Waits for the scrape and cleaning to complete.
4. Opens the generated CSV/Excel in Excel or BI tools.

**Flow 2 – Developer Using the API**

1. Ensures configuration and scraper logic work via CLI.
2. Starts the API: `uvicorn ecomscrape.api:app --reload`.
3. Calls `GET /products` from another service or Postman.
4. Receives JSON data and integrates it into downstream processes.

### 7.3 Design Notes

- CLI output should be readable and not overly verbose by default; a `--debug` flag can enable detailed logging.
- Errors should be described in plain language where possible, pointing users to log files for more detail.
- If a web UI is implemented, keep it minimal and focused on core actions: run scrape, inspect, download.

---

## 8. Development Plan

### 8.1 Feature Breakdown

- Project setup and environment configuration.
- Configuration loader (YAML/JSON) with basic schema validation.
- HTTP request module with header rotation, timeouts, and retries.
- HTML parsing module using configurable selectors.
- Pandas-based cleaning and normalisation functions.
- CSV exporter.
- Excel exporter with basic formatting.
- CLI entry point and argument parsing.
- Optional REST API (FastAPI/Flask).
- Unit tests and integration tests.
- Documentation (README, example configs, usage examples).

### 8.2 Timeline & Roadmap (Example ~3–4 Weeks)

**Week 1**

- Set up project structure and version control.
- Implement configuration loader and basic HTTP client.
- Prototype a simple scrape of a single page.

**Week 2**

- Develop parsing module with selectors from config.
- Implement Pandas cleaning and normalisation.
- Implement CSV and Excel export.
- Begin writing unit tests for parsing and cleaning.

**Week 3**

- Add header rotation, retries, and improved logging.
- Finalise CLI interface and options.
- Implement optional API endpoints.
- Add integration test covering end-to-end flow.

**Week 4**

- Polish documentation (README, screenshots).
- Run manual tests on one or more real sites (within ethical limits).
- Prepare portfolio case study text and images.

### 8.3 Risk Assessment & Mitigation

- **Risk:** Target site changes its HTML structure.  
  **Mitigation:** Use configuration-driven selectors so fixes require only config updates, not code changes.

- **Risk:** Site blocks or rate-limits scraping.  
  **Mitigation:** Use delays between requests, rotating headers, obey robots.txt, and keep scrape volumes low.

- **Risk:** Excel exports become slow or unwieldy for large datasets.  
  **Mitigation:** Default to CSV for large exports and document recommended data size limits.

- **Risk:** Users struggle with configuration files.  
  **Mitigation:** Provide well-commented example configs and step-by-step instructions.

---

## 9. Testing

### 9.1 Testing Strategy

Combine automated tests for core logic with manual tests against sample and real pages. Focus on:

- Correctness of parsing/cleaning.
- Robustness to errors.
- Validity of exported files.

### 9.2 Test Types

- **Unit**
  - Individual functions for parsing HTML fragments.
  - Cleaning functions (e.g. price conversions, rating extraction).
- **Integration**
  - Full pipeline using local sample HTML: parse → clean → export.
- **End-to-End**
  - Run CLI against a controlled test site or static pages, verifying outputs and logs.
- **Manual**
  - Run against a live e-commerce site (in a limited, ethical way) and inspect generated CSV/Excel manually.

### 9.3 Test Cases

**Parsing**

- Given a known product HTML snippet, all required fields are extracted correctly.
- If a field is missing, appropriate defaults or `None` are used.

**Cleaning**

- `'£1,234.56'` → `1234.56` (float).
- `'4.5 out of 5 stars'` → `4.5` (float).
- `'1,234 reviews'` → `1234` (int).
- Missing prices or names are flagged or the row is excluded according to rules.

**Error Handling**

- Simulated timeout and 500 responses trigger retries, then log failures without crashing.
- Invalid URLs are handled gracefully.

**Export**

- CSV and Excel outputs contain the expected number of rows and columns.
- Data types in exported files match expectations.

### 9.4 Bug Log

A simple log (e.g. in a Markdown or spreadsheet) recording:

- Bug ID
- Description
- Steps to reproduce
- Expected vs actual behaviour
- Severity
- Status (open/fixed)
- Fix version / date

---

## 10. Deployment

### 10.1 Environment Setup

- Install Python 3.10+ on the target machine.
- Create and activate a virtual environment.
- Install dependencies via `pip install -r requirements.txt` (or Poetry/other tool as used in the project).
- (Optional) Install `uvicorn` if running the FastAPI API server.

### 10.2 Build & Deployment Steps

- Clone or download the project repository.
- Configure `configs/site1.yaml` (or other config files) for target sites.
- Run tests (if included) to ensure environment is set up correctly.

**To use the CLI:**

```bash
python cli.py --config configs/site1.yaml --format csv excel
```

**To start the API (if implemented):**

```bash
uvicorn ecomscrape.api:app --host 0.0.0.0 --port 8000
```

### 10.3 Hosting Configuration

- **For CLI-only usage:**
  - No special hosting required; can run on a local machine or server.

- **For API usage:**
  - Host on a small server (VPS or on-prem) with Python environment.
  - Optionally use a process manager (e.g. systemd, supervisor) to keep the API running.
  - Optionally place Nginx/another reverse proxy in front if exposed publicly.

---

## 11. Portfolio Case Study

### 11.1 Project Summary

EcomScrape is a Python-based web scraping and automation tool that collects product data from e-commerce sites, cleans and normalises it using Pandas, and exports analysis-ready CSV and Excel files. It includes robust error handling, rotating headers, and an optional REST API for programmatic access to the data.

### 11.2 Your Role

- Sole designer and developer of the system.
- Responsible for:
  - Requirements analysis and planning.
  - Architecture and data model design.
  - Implementation of scraping, cleaning, exporting, and optional API.
  - Testing, documentation, and packaging as a portfolio project.

### 11.3 Tech Stack

- **Language:** Python  
- **Libraries:** `requests`/`httpx`, `BeautifulSoup`/`lxml`, `pandas`, `openpyxl`/`XlsxWriter`, `FastAPI` or `Flask`, `argparse`/`typer`  
- **Tools:** Git, virtualenv/Poetry, code editor (e.g. VS Code), possibly Streamlit for optional UI.

### 11.4 Development Process

- Started by defining the problem and filling out the project documentation template.
- Designed a modular architecture separating configuration, HTTP fetching, parsing, cleaning, and export.
- Implemented a minimal end-to-end pipeline, then added robustness (retries, logging, rotating headers).
- Built CSV and Excel export functionality, verifying data types and structure.
- Added an optional REST API to expose the results as JSON.
- Wrote unit and integration tests and performed manual testing on real pages.
- Finalised documentation and prepared screenshots/demos for portfolio use.

### 11.5 Challenges & Solutions

- **Challenge:** Parsing inconsistent HTML structures and formats for prices and ratings.  
  **Solution:** Developed configuration-driven selectors and robust cleaning functions with regex and explicit type conversions.

- **Challenge:** Preventing the scraper from crashing due to network errors or unexpected HTML changes.  
  **Solution:** Implemented retry logic, timeouts, and defensive parsing with clear logging and error handling.

- **Challenge:** Making the scraper reusable for different sites.  
  **Solution:** Moved all site-specific details (URLs, selectors, headers) into external configuration files.

### 11.6 Screenshots / Demo (To Be Added)

Suggested screenshots:

- CLI run showing progress and summary.
- CSV/Excel file open in Excel.
- API response in a browser or Postman.
- Optional Streamlit interface if implemented.

### 11.7 Lessons Learned

- The importance of separating scraping, parsing, and cleaning concerns to keep the system maintainable.
- How to design a configuration-driven scraping tool that can be adapted to different sites without code changes.
- Practical experience using Pandas for real-world data cleaning and export.
- How to expose a data-processing script as a simple HTTP API.
- Ethical and practical considerations when scraping websites, including rate limiting and respecting robots.txt.
