#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "playwright",
# ]
# ///
"""Download PJM GATS's "Renewable Generators Registered in GATS" public
report and produce a single, analysis-ready CSV.

The public report page (https://gats.pjm-eis.com/gats2/PublicReports/
RenewableGeneratorsRegisteredinGATS) only displays 50 rows at a time in an
interactive DevExpress grid, but its "CSV" toolbar button triggers a
server-side export of the *entire* unfiltered report (~629k rows as of
2026) as a single file. That export takes several minutes to generate and
is only reachable by driving a real browser: plain HTTP POSTs to the same
export endpoint (replicating the form the button submits) are silently
dropped, apparently by bot detection in front of the site. This script
uses Playwright to load the page in headless Chromium and click the real
button, then waits for the resulting download.

Setup (one-time): `uv run --with playwright playwright install chromium`

Usage:
    uv run download_and_combine.py            # download + clean
    uv run download_and_combine.py --no-download  # clean only, using the newest file already in raw/

Re-run this script anytime to pick up new/changed registrations; PJM does
not version this report, so there's no year-by-year download to manage
(unlike the EIA cooling-water dataset in this repo) -- each run simply
replaces the current snapshot.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
RAW_DIR = HERE / "raw"
OUTPUT_PATH = HERE / "pjm_gats_renewable_generators.csv"

REPORT_URL = "https://gats.pjm-eis.com/gats2/PublicReports/RenewableGeneratorsRegisteredinGATS"


def download_raw(timeout_minutes: int = 20) -> Path:
    """Drive headless Chromium to the report page and click its CSV export
    button, saving the resulting file into RAW_DIR."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = RAW_DIR / f"renewable_generators_registered_in_gats_{date.today():%Y%m%d}.csv"

    print(f"launching browser, navigating to {REPORT_URL}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(REPORT_URL, wait_until="networkidle", timeout=60 * timeout_minutes)
        print("page loaded, clicking CSV export button (this can take several minutes for ~600k rows)")

        with page.expect_download(timeout=timeout_minutes * 60) as download_info:
            # The export button submits a plain (non-XHR) form whose
            # response is the file download; don't let Playwright wait on
            # a same-page navigation that will never resolve the normal way.
            page.click("#CSV", no_wait_after=True)
        download = download_info.value
        download.save_as(dest)
        browser.close()

    print(f"saved raw export -> {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest


def latest_raw_file() -> Path:
    candidates = sorted(RAW_DIR.glob("renewable_generators_registered_in_gats_*.csv"))
    if not candidates:
        raise SystemExit(f"no raw export found in {RAW_DIR}; run without --no-download first")
    return candidates[-1]


# Raw column name -> tidy snake_case name. The trailing "New Jersey" ...
# "EFEC Eligible" columns hold each state (or EFEC) program's GATS
# certificate ID for this unit when it's registered in that program, not a
# yes/no flag, so they're named accordingly.
COLUMN_RENAMES = {
    "Plant Name": "plant_name",
    "Unit Name": "unit_name",
    "ORISPL (Plant Code)": "orispl_plant_code",
    "GATS Unit ID": "gats_unit_id",
    "PJM Unit?": "pjm_unit_id",
    "State": "state",
    "County": "county",
    "Balancing Authority": "balancing_authority",
    "Nameplate": "nameplate_capacity_mw",
    "Date Online": "date_online",
    "Primary Fuel Type": "primary_fuel_type",
    "Secondary": "secondary_fuel_type",
    "Tertiary": "tertiary_fuel_type",
    "Quaternary": "quaternary_fuel_type",
    "Fifth": "fifth_fuel_type",
    "Sixth": "sixth_fuel_type",
    "Seventh": "seventh_fuel_type",
    "Eighth": "eighth_fuel_type",
    "New Jersey": "nj_certificate_id",
    "Maryland": "md_certificate_id",
    "Pennsylvania": "pa_certificate_id",
    "District of Columbia": "dc_certificate_id",
    "Delaware": "de_certificate_id",
    "Illinois": "il_certificate_id",
    "Ohio": "oh_certificate_id",
    "Virginia": "va_certificate_id",
    "EFEC Eligible": "efec_certificate_id",
}

STRING_COLUMNS = [
    "plant_name",
    "unit_name",
    "gats_unit_id",
    "pjm_unit_id",
    "state",
    "county",
    "balancing_authority",
    "primary_fuel_type",
    "secondary_fuel_type",
    "tertiary_fuel_type",
    "quaternary_fuel_type",
    "fifth_fuel_type",
    "sixth_fuel_type",
    "seventh_fuel_type",
    "eighth_fuel_type",
    "nj_certificate_id",
    "md_certificate_id",
    "pa_certificate_id",
    "dc_certificate_id",
    "de_certificate_id",
    "il_certificate_id",
    "oh_certificate_id",
    "va_certificate_id",
    "efec_certificate_id",
]


def clean(raw_path: Path) -> pd.DataFrame:
    # PJM's export isn't UTF-8; plant/owner names occasionally contain
    # Windows-1252 characters (curly quotes, accented letters, etc).
    df = pd.read_csv(raw_path, dtype=str, keep_default_na=False, encoding="cp1252")
    df = df.rename(columns=COLUMN_RENAMES)

    for col in STRING_COLUMNS:
        df[col] = df[col].str.strip().replace("", pd.NA)

    df["orispl_plant_code"] = pd.to_numeric(df["orispl_plant_code"].str.strip(), errors="coerce").astype("Int64")
    df["nameplate_capacity_mw"] = pd.to_numeric(df["nameplate_capacity_mw"], errors="coerce")
    df["date_online"] = pd.to_datetime(df["date_online"], format="%m/%d/%Y", errors="coerce")

    ordered = list(COLUMN_RENAMES.values())
    return df[ordered]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-download", action="store_true", help="Skip the browser download; clean the newest file already in raw/"
    )
    args = parser.parse_args()

    raw_path = latest_raw_file() if args.no_download else download_raw()

    print(f"cleaning {raw_path.name}")
    df = clean(raw_path)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"wrote {len(df):,} rows x {len(df.columns)} cols -> {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
