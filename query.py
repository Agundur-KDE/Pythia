#!/usr/bin/env python3
"""Query Google Search Console performance data via a service account.

Usage:
    query.py <site-url> [--days N] [--dimensions query,page,country,device] [--limit N]

Examples:
    query.py sc-domain:example.com --days 28 --dimensions page
    query.py sc-domain:example.com --days 7 --dimensions query --limit 20

Note: --days N covers N+1 calendar days (both start and end date are
inclusive), and Search Console data usually lags 1-3 days behind today.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    sys.exit(
        "Missing dependency: google-auth / google-api-python-client are not installed.\n"
        "Fix: pip install -r requirements.txt (ideally inside a venv)."
    )

KEY_FILE = Path(__file__).parent / "service-account.json"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
VALID_DIMENSIONS = {"query", "page", "country", "device", "date", "searchAppearance"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("site", help="e.g. sc-domain:example.com or https://www.example.com/")
    parser.add_argument("--days", type=int, default=28)
    parser.add_argument("--dimensions", default="page", help="comma-separated: query,page,country,device,date")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()

    if args.days < 1:
        sys.exit("--days must be at least 1.")
    if not 1 <= args.limit <= 25000:
        sys.exit("--limit must be between 1 and 25000 (Search Console API limit).")
    dims = args.dimensions.split(",")
    unknown = [d for d in dims if d not in VALID_DIMENSIONS]
    if unknown:
        sys.exit(f"Unknown dimension(s): {', '.join(unknown)}. Valid: {', '.join(sorted(VALID_DIMENSIONS))}")

    if not KEY_FILE.exists():
        sys.exit(
            f"Missing service account key: {KEY_FILE} not found.\n"
            "Fix: download a JSON key for your service account in Google Cloud Console "
            "(IAM & Admin -> Service Accounts -> Keys) and save it at this path."
        )

    try:
        creds = service_account.Credentials.from_service_account_file(str(KEY_FILE), scopes=SCOPES)
        service = build("searchconsole", "v1", credentials=creds)
    except ValueError as e:
        sys.exit(f"Invalid service account key file ({KEY_FILE}): {e}")

    end = datetime.date.today()
    start = end - datetime.timedelta(days=args.days)

    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": dims,
        "rowLimit": args.limit,
    }

    try:
        resp = service.searchanalytics().query(siteUrl=args.site, body=body).execute()
    except HttpError as e:
        if e.resp.status == 403:
            sys.exit(
                f"Permission denied for site '{args.site}'.\n"
                "Fix: add this service account's email as a (Restricted/read-only) user "
                "under Settings -> Users and permissions in Search Console for that exact property."
            )
        if e.resp.status == 404:
            sys.exit(
                f"Site not found: '{args.site}'.\n"
                "Fix: check the exact property syntax — sc-domain:example.com for a Domain "
                "property, or https://www.example.com/ (with trailing slash) for a URL-prefix property."
            )
        sys.exit(f"Search Console API request failed ({e.resp.status}): {e}")

    print(json.dumps(resp.get("rows", []), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
