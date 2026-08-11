#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pandas",
#     "openpyxl",
#     "requests",
# ]
# ///
"""Download EIA thermoelectric cooling water "Detail" spreadsheets (2014-2024)
and combine them into a single tidy CSV per worksheet tab.

Usage:
    uv run download_and_combine.py            # download (if needed) + combine
    uv run download_and_combine.py --force     # re-download everything, then combine
    uv run download_and_combine.py --no-download  # combine only, using files already on disk

Re-run this script whenever EIA adds a new year or revises an existing
spreadsheet: add the new year's URL to YEAR_URLS below, then run with
--force (or just delete the stale file from spreadsheets/) to refresh it.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).parent
SPREADSHEET_DIR = HERE / "spreadsheets"
OUTPUT_DIR = HERE

# EIA has used a few different file-naming and URL conventions over the
# years. The most recent year's file lives under the "current" data
# directory; prior years get moved into the "archive" directory once a new
# year is published. These URLs were confirmed by scraping the live
# download page at https://www.eia.gov/electricity/data/water/
BASE = "https://www.eia.gov/electricity/data/water"
YEAR_URLS: dict[int, str] = {
    2014: f"{BASE}/archive/xls/cooling_detail_2014.xlsx",
    2015: f"{BASE}/archive/xls/cooling_detail_2015.xlsx",
    2016: f"{BASE}/archive/xls/cooling_detail_2016.xlsx",
    2017: f"{BASE}/archive/xls/cooling_detail_2017.xlsx",
    2018: f"{BASE}/archive/xls/cooling_detail_2018.xlsx",
    2019: f"{BASE}/archive/xls/cooling_detail_2019.xlsx",
    2020: f"{BASE}/archive/xls/cooling_detail_2020.xlsx",
    2021: f"{BASE}/archive/xls/Cooling_Boiler_Generator_Data_Detail_2021.xlsx",
    2022: f"{BASE}/archive/xls/Cooling_Boiler_Generator_Data_Detail_2022.xlsx",
    2023: f"{BASE}/archive/xls/Cooling_Boiler_Generator_Data_Detail_2023.xlsx",
    2024: f"{BASE}/xls/Cooling_Boiler_Generator_Data_Detail_2024.xlsx",
}


def download_all(force: bool = False) -> dict[int, Path]:
    """Download every year's detail spreadsheet into SPREADSHEET_DIR.

    Skips files that already exist unless `force` is set, so re-running the
    script only fetches new or missing years.
    """
    SPREADSHEET_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[int, Path] = {}
    for year, url in sorted(YEAR_URLS.items()):
        dest = SPREADSHEET_DIR / f"cooling_detail_{year}.xlsx"
        paths[year] = dest
        if dest.exists() and not force:
            print(f"[{year}] already downloaded -> {dest.name}")
            continue
        print(f"[{year}] downloading {url}")
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        if response.content[:2] != b"PK":
            raise RuntimeError(
                f"[{year}] response from {url} doesn't look like an .xlsx file "
                "(EIA may have moved it, or is blocking the request)"
            )
        dest.write_bytes(response.content)
        print(f"[{year}] saved {len(response.content) / 1e6:.1f} MB -> {dest.name}")
    return paths


def normalize_column(name: object) -> str:
    """Collapse whitespace/newlines in raw EIA column headers."""
    text = re.sub(r"\s+", " ", str(name)).strip()
    return text


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug


def read_year(path: Path, year: int) -> dict[str, pd.DataFrame]:
    """Read every worksheet tab in one year's workbook.

    Returns a dict of {sheet_name: dataframe}, with columns normalized and
    fully-blank spacer columns dropped.
    """
    sheets = pd.read_excel(path, sheet_name=None)
    cleaned = {}
    for sheet_name, df in sheets.items():
        df = df.rename(columns=normalize_column)
        # EIA workbooks include a couple of unnamed, entirely-empty spacer
        # columns left over from merged header cells; drop them.
        blank_cols = [c for c in df.columns if c == "" or df[c].isna().all()]
        df = df.drop(columns=blank_cols)
        df.insert(0, "data_year", year)
        cleaned[sheet_name] = df
    return cleaned


def combine(paths: dict[int, Path]) -> dict[str, pd.DataFrame]:
    """Read all downloaded workbooks and concatenate matching tabs across years."""
    by_sheet: dict[str, list[pd.DataFrame]] = {}
    for year, path in sorted(paths.items()):
        if not path.exists():
            print(f"[{year}] {path.name} not found on disk, skipping", file=sys.stderr)
            continue
        print(f"[{year}] reading {path.name}")
        for sheet_name, df in read_year(path, year).items():
            by_sheet.setdefault(sheet_name, []).append(df)

    combined: dict[str, pd.DataFrame] = {}
    for sheet_name, frames in by_sheet.items():
        # Align on the union of columns seen across years, in the order
        # they first appear, so a column added/renamed in a later year
        # doesn't silently drop data from earlier years (or vice versa).
        all_columns: list[str] = []
        for df in frames:
            for col in df.columns:
                if col not in all_columns:
                    all_columns.append(col)
        aligned = [df.reindex(columns=all_columns) for df in frames]
        result = pd.concat(aligned, ignore_index=True)
        combined[sheet_name] = result
    return combined


def write_outputs(combined: dict[str, pd.DataFrame]) -> None:
    for sheet_name, df in combined.items():
        out_path = OUTPUT_DIR / f"eia_thermoelectric_cooling_{slugify(sheet_name)}.csv"
        df.to_csv(out_path, index=False)
        print(f"wrote {len(df):,} rows x {len(df.columns)} cols -> {out_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true", help="Re-download all spreadsheets, even if already present"
    )
    parser.add_argument(
        "--no-download", action="store_true", help="Skip downloading; combine whatever is already in spreadsheets/"
    )
    args = parser.parse_args()

    if args.no_download:
        paths = {year: SPREADSHEET_DIR / f"cooling_detail_{year}.xlsx" for year in YEAR_URLS}
    else:
        paths = download_all(force=args.force)

    combined = combine(paths)
    write_outputs(combined)


if __name__ == "__main__":
    main()
