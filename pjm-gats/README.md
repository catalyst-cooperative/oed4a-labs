# PJM Renewable Generators Registered in GATS

PJM maintains a list of renewable generators registered in the Generation Attribute
Tracking System (GATS). This list includes information about the generators, such as
their capacity, location, and registration status. The data is publicly available and
can be accessed through the following link:

https://gats.pjm-eis.com/gats2/PublicReports/RenewableGeneratorsRegisteredinGATS

However, there is more data than can be displayed on a single page. You can ask the page
to generate a bulk download link for data meeting certain criteria, e.g. by state, or by
generator type. The bulk download link will provide a CSV file containing the requested
data.

I want to download ALL of the available data, but the page does not provide a direct
link for that. Write a python script that will scrape the page and download all
available data and put it into CSV files locally. The script may need to handle
pagination, or submitting multiple queries to obtain various subsets of the data that
can be recombined after download. Ultimately the goal is to have a single file with all
the data that can be used efficiently for highly performant bulk analysis.

## Dataset Documentation

### How to (re)build the data

Run `uv run download_and_combine.py` from this directory. It launches
headless Chromium via Playwright, loads the public report page, and clicks
the page's own "CSV" export button, which triggers a server-side export of
the *entire* unfiltered report as one file (this takes several minutes,
since as of 2026 the report has ~629,000 rows). The raw download is saved
into `raw/` with today's date in the filename, then cleaned into the final
`pjm_gats_renewable_generators.csv` in this directory.

One-time setup: `uv run --with playwright playwright install chromium` to
install the headless browser binary Playwright needs.

Useful flags:

- `--no-download`: skip the browser step and just re-clean the newest file
  already present in `raw/` (handy for iterating on the cleaning logic).

Why a browser instead of a plain HTTP request: the report's "bulk
download" feature the site advertises (filtering by state/fuel type, then
exporting) turns out to be unnecessary — the CSV export button exports all
rows regardless of any grid filter. However, issuing the same HTTP POST
that the export button's form submits (replicated with `curl`, reusing the
page's session cookies) is silently dropped by the server; the connection
either hangs indefinitely or is cancelled with no response. This looks
like bot/automation detection in front of the DevExpress-based reporting
app (gats.pjm-eis.com), so this script drives a real (headless) browser
instead of hitting the endpoint directly. Because the report reflects
live, unversioned system-of-record data rather than dated annual
publications, there's no historical archive to build up the way there is
for the EIA cooling-water dataset in this repo — each run just replaces
the current snapshot in `raw/` and regenerates the cleaned output.

### `pjm_gats_renewable_generators.csv`

Source: PJM Environmental Information Services' Generation Attribute
Tracking System (GATS) public report, "Renewable Generators Registered in
GATS"
(https://gats.pjm-eis.com/gats2/PublicReports/RenewableGeneratorsRegisteredinGATS).
GATS is the tracking system used to issue and trade renewable energy
certificates (RECs) for generators in the PJM Interconnection footprint
and neighboring states; this report lists every generating unit that has
ever registered in GATS to receive certificates; it is not limited to
units that are currently active or that participate in PJM's wholesale
power markets.

As of this snapshot (2026-08-10) the report has 629,028 rows, spanning 22
states (dominated by DC, MD, NJ, PA, VA, IL, and OH, reflecting PJM's
footprint plus a few states GATS also serves). The overwhelming majority
of rows (~623,000) are small, primary-fuel-type "SUN" (solar) systems,
including many individually-registered residential rooftop solar
installations — nameplate capacities range from a few kW up to large
utility-scale plants.

Grain: one row = one generating unit registered in GATS (`gats_unit_id` is
unique per row). A single physical plant can have multiple units/rows
(e.g. `orispl_plant_code` repeats across units at the same plant), and a
unit can be registered in more than one state/regional REC program
simultaneously (see the `*_certificate_id` columns below).

| Column | Description |
|---|---|
| `plant_name` | Name of the generating plant/facility. For small residential/behind-the-meter solar, this is often just the site address or a personal name, since the "plant" is a single installation. |
| `unit_name` | Name of the specific generating unit within the plant; for single-unit facilities this often duplicates `plant_name` or is a short capacity description (e.g. "7.92 kW"). |
| `orispl_plant_code` | EIA plant identifier (ORIS/plant code), when the facility is also registered with EIA (matches `plant_id_eia` in EIA datasets). Null for most small/residential systems, which aren't EIA-registered. |
| `gats_unit_id` | GATS's own unique identifier for this generating unit (e.g. `NON177006`). Primary key for this table. |
| `pjm_unit_id` | Identifier linking the unit to PJM's wholesale market unit registration, when applicable. Null for the large majority of rows (most registrants, especially residential solar, do not participate directly in PJM markets). |
| `state` | Two-letter postal abbreviation of the state where the generating unit is physically located. |
| `county` | County (or DC ward-equivalent) where the unit is located. |
| `balancing_authority` | Balancing authority the unit falls under (e.g. "PJM Interconnection", or a vertically-integrated utility like "Southern Company" for units located outside PJM's footprint). |
| `nameplate_capacity_mw` | Nameplate generating capacity, in megawatts. Values below 0.01 MW (10 kW) are common for small residential solar. |
| `date_online` | Date the unit began commercial operation (parsed to `YYYY-MM-DD`; source data was month/day/year with day always `01`, i.e. effectively month-granularity). |
| `primary_fuel_type` | Primary fuel/technology code for the unit, using short EIA-style codes, e.g. `SUN` (solar PV), `STH` (solar thermal), `WND` (wind), `WAT` (conventional hydro), `HPS` (hydro pumped storage), `GEO` (geothermal), `LFG` (landfill gas), `MSW` (municipal solid waste), `WDS` (wood/wood waste solids), `BLQ` (black liquor), `OBG` (other biogas), `WH` (waste heat), `WC` (waste coal), `NG` (natural gas), `EE` (energy efficiency credit). |
| `secondary_fuel_type` … `eighth_fuel_type` | Additional fuel/technology codes for units that co-fire or use multiple energy sources, in the same code system as `primary_fuel_type`. Almost always null; populated for a small number of multi-fuel units (e.g. biomass co-firing). |
| `nj_certificate_id` | New Jersey Class I/II REC program certificate ID for this unit, if registered in that program; null otherwise. |
| `md_certificate_id` | Maryland RPS program certificate ID, if registered. |
| `pa_certificate_id` | Pennsylvania AEPS (Alternative Energy Portfolio Standard) certificate ID, if registered. |
| `dc_certificate_id` | Washington DC RPS program certificate ID, if registered. This is the most common program in this dataset given the volume of DC residential solar registrants. |
| `de_certificate_id` | Delaware RPS program certificate ID, if registered. |
| `il_certificate_id` | Illinois RPS program certificate ID, if registered. |
| `oh_certificate_id` | Ohio RPS program certificate ID, if registered. |
| `va_certificate_id` | Virginia RPS/RPS Program certificate ID, if registered. Many DC-registered residential systems are dual-registered in Virginia's program too. |
| `efec_certificate_id` | EFEC ("Environmentally Friendly Energy Certificate," a PJM-GATS-specific attribute tracking product) certificate ID, if registered. |

A unit can hold certificate IDs in more than one of the state/EFEC columns
at once (e.g. a DC-based system dual-registered for both DC's and
Virginia's REC programs); these are independent, not mutually exclusive.
