from typing import Dict, List

from otc_tracker import extract_notes_from_filing, fetch_edgar_filings, get_cik_number
import json, requests


def process_tickers(tickers: List[str]) -> Dict:
    """Process a list of tickers to find convertible notes."""
    results = {}

    for ticker in tickers:
        try:
            # Get CIK
            cik = get_cik_number(ticker)
            if not cik:
                results[ticker] = {
                    "status": "error",
                    "message": f"No CIK found for {ticker}.",
                }
                continue

            # Fetch filings
            filings = fetch_edgar_filings(ticker, cik)
            if not filings:
                results[ticker] = {
                    "status": "no_filings",
                    "message": f"No 10-Q filings found for {ticker}.",
                }
                continue

            # Extract notes from filings
            notes = []
            for filing in filings:
                response = requests.get(
                    filing["url"],
                    headers={"User-Agent": "OTCTracker contact@yourcompany.com"},
                )
                if response.ok:
                    notes.extend(extract_notes_from_filing(response.text))

            results[ticker] = {
                "status": "success",
                "notes": notes,
                "message": f"Found {len(notes)} notes for {ticker}.",
            }

        except Exception as e:
            results[ticker] = {"status": "error", "message": str(e)}

    return results


# Test the function
tickers = ["AAPL", "MSFT", "GOOGL"]
results = process_tickers(tickers)
print(json.dumps(results, indent=4))
