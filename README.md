# OTC Tracker

A Python tool to fetch and analyze SEC filings for NASDAQ-listed companies, specifically focusing on identifying **convertible notes** in 10-Q filings.

---

## What Does This Code Do?

1. **Fetches CIK (Central Index Key)** for a given ticker using:
   - SEC's `company_tickers.json`
   - Yahoo Finance
   - Direct SEC API lookup

2. **Fetches 10-Q Filings** from the SEC's EDGAR database for a given CIK.

3. **Extracts Convertible Notes** from the filing text using regex patterns.

4. **Processes Multiple Tickers** and outputs results in a structured JSON format.

---

## How to Use

1. Install dependencies:
   ```bash
   pip install requests pandas yfinance beautifulsoup4
   ```

## TODO

explain the extracting notes from filing ? example url added
https://www.sec.gov/ix?doc=/Archives/edgar/data/320193/000032019324000081/aapl-20240629.htm