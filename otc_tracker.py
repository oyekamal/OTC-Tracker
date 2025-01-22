from typing import Dict, List, Optional
import requests
import yfinance as yf
from bs4 import BeautifulSoup
import re
from datetime import datetime


def get_cik_number(ticker: str) -> Optional[str]:
    """Get CIK for a given ticker using multiple methods."""
    headers = {
        "User-Agent": "OTCTracker contact@yourcompany.com"  # Replace with your email
    }

    try:
        # Method 1: Try SEC's company tickers JSON
        response = requests.get(
            "https://www.sec.gov/files/company_tickers.json", headers=headers
        )
        if response.ok:
            companies = response.json()
            ticker_upper = ticker.upper()

            for company in companies.values():
                if company["ticker"].upper() == ticker_upper:
                    cik = str(company["cik_str"]).zfill(10)
                    print(f"Found CIK {cik} for {ticker} in SEC tickers JSON")
                    return cik

        # Method 2: Try Yahoo Finance
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if "cik" in info and info["cik"]:
                cik = str(info["cik"]).zfill(10)
                print(f"Found CIK {cik} for {ticker} in Yahoo Finance")
                return cik
        except Exception as e:
            print(f"Yahoo Finance lookup failed for {ticker}: {str(e)}")

        # Method 3: Try direct SEC CIK lookup
        search_url = f"https://data.sec.gov/submissions/CIK{ticker.upper()}.json"
        response = requests.get(search_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if "cik" in data:
                cik = str(data["cik"]).zfill(10)
                print(f"Found CIK {cik} for {ticker} in direct SEC lookup")
                return cik

        print(f"No CIK found for ticker {ticker} using any method")
        return None

    except Exception as e:
        raise Exception(f"Failed to fetch CIK: {str(e)}")


def fetch_edgar_filings(ticker: str, cik: str) -> List[Dict]:
    """Fetch the most recent 10-Q filing for a given CIK."""
    headers = {"User-Agent": "OTCTracker contact@yourcompany.com"}
    padded_cik = cik.zfill(10)
    filings = []

    try:
        submissions_url = f"https://data.sec.gov/submissions/CIK{padded_cik}.json"
        response = requests.get(submissions_url, headers=headers)

        if response.ok:
            data = response.json()
            recent_filings = data.get("filings", {}).get("recent", {})

            if recent_filings:
                forms = recent_filings.get("form", [])
                dates = recent_filings.get("filingDate", [])
                accessions = recent_filings.get("accessionNumber", [])

                # Find the most recent 10-Q
                for form, date, accession in zip(forms, dates, accessions):
                    if form == "10-Q":
                        clean_accession = accession.replace("-", "")
                        primary_doc_url = f"https://www.sec.gov/Archives/edgar/data/{padded_cik}/{clean_accession}/{accession}-index.htm"

                        try:
                            doc_response = requests.get(
                                primary_doc_url, headers=headers
                            )
                            if doc_response.ok:
                                doc_soup = BeautifulSoup(
                                    doc_response.text, "html.parser"
                                )
                                for row in doc_soup.select("tr"):
                                    if row.text and "10-q" in row.text.lower():
                                        doc_link = row.find("a")
                                        if doc_link and doc_link.get("href"):
                                            filing_url = (
                                                f"https://www.sec.gov{doc_link['href']}"
                                            )
                                            filings.append(
                                                {
                                                    "type": "10-Q",
                                                    "date": date,
                                                    "url": filing_url,
                                                }
                                            )
                                            break
                        except Exception as e:
                            print(f"Error getting document URL: {str(e)}")
                        break  # Only fetch the most recent 10-Q

    except Exception as e:
        print(f"Error with SEC API: {str(e)}")

    return filings


def extract_notes_from_filing(filing_text: str) -> List[Dict]:
    """
    Extract convertible notes from the filing text.
    Extract Convertible Notes from Filings

    """
    notes = []

    # Regex pattern to capture convertible notes
    note_pattern = r"(?i)(?:convertible\s+note|note\s+payable).*?\$([\d,]+(?:\.\d{2})?)[\s\S]*?(?:due|matur[es].*?)(?:on\s+)?(\w+\s+\d{1,2},?\s*\d{4})"
    notes_found = re.finditer(note_pattern, filing_text)

    for note_match in notes_found:
        try:
            principal_str = note_match.group(1).replace(",", "")
            date_str = note_match.group(2)

            principal = float(principal_str)

            # Parse maturity date
            date_formats = ["%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y"]
            maturity_date = None
            for fmt in date_formats:
                try:
                    maturity_date = datetime.strptime(date_str, fmt).strftime(
                        "%Y-%m-%d"
                    )
                    break
                except ValueError:
                    continue

            if maturity_date:
                note_data = {
                    "note_type": "Convertible Note",
                    "principal_amount": principal,
                    "maturity_date": maturity_date,
                }

                # Capture interest rate if available
                interest_match = re.search(r"(\d+(?:\.\d+)?)\s*%", note_match.group(0))
                if interest_match:
                    note_data["interest_rate"] = float(interest_match.group(1))

                notes.append(note_data)

        except Exception as e:
            print(f"Error parsing note: {str(e)}")

    return notes


# Test the function
ticker = "AAPL"
cik = get_cik_number(ticker)
if cik:
    filings = fetch_edgar_filings(ticker, cik)
    print(f"Filings for {ticker}: {filings}")
# Test the function
if cik and filings:
    filing_url = filings[0]["url"]
    response = requests.get(
        filing_url, headers={"User-Agent": "OTCTracker contact@yourcompany.com"}
    )
    if response.ok:
        notes = extract_notes_from_filing(response.text)
        print(f"Notes found in filing: {notes}")
