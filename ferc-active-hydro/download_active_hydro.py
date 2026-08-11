#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "requests",
# ]
# ///
"""Download all FERC "Active Hydropower Projects" datasets to local CSVs.

https://data.ferc.gov/active-hydropower-projects/ is a JavaScript-rendered index page
linking to four datasets (active exemptions, active licenses, projects by relicensing
due date, and licensed marine/hydrokinetic projects). There's no public bulk-download
URL, so this script talks to the same-origin JSON endpoint the web app itself uses to
populate its data grid (https://data.ferc.gov/api/v1/dataset/<id>/), which proxies to
the real API server-side and doesn't require a key. It's an undocumented, unversioned
endpoint discovered by inspecting the site's compiled JavaScript, so it may break if
FERC changes the site.

Each dataset's column list and metadata (title, description, last-updated timestamp) are
scraped from the Next.js `__NEXT_DATA__` JSON embedded in each dataset's page, so the
script adapts automatically if FERC adds/renames columns.

Usage:
    uv run download_active_hydro.py

Re-run to refresh the local CSVs -- each run does a full re-download and overwrite, so
new/updated/removed records are picked up automatically. There's no per-record
change-tracking or filtering available in this API, so an incremental update isn't
possible; a full refresh is cheap since the datasets only have a few hundred to a few
thousand rows each.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

HERE = Path(__file__).parent

SITE_BASE = "https://data.ferc.gov"
ASSET_SLUG = "active-hydropower-projects"

# The four dataset pages linked from https://data.ferc.gov/active-hydropower-projects/
DATASET_SLUGS = [
    "active-exemptions",
    "active-licenses",
    "projects-by-relicensing-due-date",
    "licensed-marine-and-hydrokinetic-projects",
]

PAGE_SIZE = 100  # the API rejects requests for more than 100 rows at a time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
}


def fetch_dataset_metadata(session: requests.Session, slug: str) -> dict[str, Any]:
    """Scrape a dataset page's embedded Next.js props for its ID, columns, and metadata."""
    url = f"{SITE_BASE}/{ASSET_SLUG}/{slug}/"
    response = session.get(url, headers=HEADERS)
    response.raise_for_status()
    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', response.text, re.S
    )
    if match is None:
        raise RuntimeError(f"couldn't find __NEXT_DATA__ on {url}")
    next_data = json.loads(match.group(1))
    props = next_data["props"]["pageProps"]
    return {
        "dataset_id": props["datasetId"],
        "title": props["metadata"]["dataset_title"],
        "description": props["metadata"]["description"],
        "data_last_updated": props["metadata"]["data_last_updated"],
        "columns": [col["column_name"] for col in props["format"]],
    }


def fetch_dataset_rows(
    session: requests.Session, dataset_id: int, columns: list[str], referer: str
) -> list[dict[str, Any]]:
    """Page through the dataset's grid-data endpoint and return all rows."""
    url = f"{SITE_BASE}/api/v1/dataset/{dataset_id}/"
    headers = {**HEADERS, "Content-Type": "application/json", "Referer": referer}
    rows: list[dict[str, Any]] = []
    start_row = 0
    total_count: int | None = None
    while total_count is None or start_row < total_count:
        payload = {
            "startRow": start_row,
            "endRow": start_row + PAGE_SIZE,
            "sortModel": [],
            "filterModel": {},
            "columns": columns,
            "castData": [],
        }
        response = session.post(url, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()
        rows.extend(body["rowData"])
        total_count = body["totalCount"]
        start_row += PAGE_SIZE
        time.sleep(0.2)  # be polite
    return rows


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def main() -> None:
    session = requests.Session()

    for slug in DATASET_SLUGS:
        print(f"[{slug}] fetching metadata")
        meta = fetch_dataset_metadata(session, slug)
        referer = f"{SITE_BASE}/{ASSET_SLUG}/{slug}/"

        print(
            f"[{slug}] downloading dataset {meta['dataset_id']} "
            f"({len(meta['columns'])} columns)"
        )
        rows = fetch_dataset_rows(session, meta["dataset_id"], meta["columns"], referer)

        df = pd.DataFrame(rows, columns=meta["columns"])
        out_path = HERE / f"ferc_active_hydro_{slugify(slug)}.csv"
        df.to_csv(out_path, index=False)
        print(f"[{slug}] wrote {len(df):,} rows x {len(df.columns)} cols -> {out_path.name}")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as exc:
        print(f"HTTP error: {exc}", file=sys.stderr)
        sys.exit(1)
