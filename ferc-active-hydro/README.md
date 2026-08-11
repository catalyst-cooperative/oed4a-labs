# FERC Active Hydropower Projects

FERC publishes a number of datasets about hydropower projects in the US. This page is an
index that points to several of them, covering currently active hydropower projects.

https://data.ferc.gov/active-hydropower-projects/

## Dataset Documentation

### Source

All data comes from FERC's Data Catalog site, [data.ferc.gov](https://data.ferc.gov/),
under the "Active Hydropower Projects" data asset:
https://data.ferc.gov/active-hydropower-projects/

Run `uv run download_active_hydro.py` to (re-)download all four datasets. Each run does
a full refresh and overwrites the local CSVs — the API offers no filtering or per-record
change-tracking, so there's no way to fetch only new/changed rows, but a full
re-download is cheap since these datasets only run from a few rows up to about a
thousand.

### Contents

Downloaded as of 2026-08-10, all four datasets are licensed/exempted/tracked hydropower
projects regulated by FERC's Office of Energy Projects. `Project_Number` (FERC's docket
number, e.g. `P-2005`) is the natural key and can be used to join across the four tables
and against other FERC project data.

#### `ferc_active_hydro_active_licenses.csv` (1,006 rows)

Active licensed hydropower projects (conventional dams/hydro, the largest of the four
datasets).

| Column | Type | Description |
|---|---|---|
| `Project_Number` | string | FERC docket number, e.g. `P-11841` |
| `Project_Name` | string | Project name |
| `Licensee` | string | Entity holding the FERC license |
| `Issuance_Date` | date (ISO 8601) | Date the license was issued |
| `Expiration_Date` | date (ISO 8601) | Date the license expires |
| `Total_Authorized_Capacity___kW___` | decimal | Total authorized generating capacity, in kW |
| `State__s___` | string | State(s) the project is located in |
| `Waterway__s___` | string | Waterway(s) the project uses |
| `Description` | string | Project type, e.g. `Conventional` |

#### `ferc_active_hydro_active_exemptions.csv` (604 rows)

Active exempted hydropower projects — small conduit/hydro projects that are exempt from
full licensing but still tracked by FERC.

| Column | Type | Description |
|---|---|---|
| `Project_Number` | string | FERC docket number |
| `Project_Name` | string | Project name |
| `Exemptee` | string | Entity holding the exemption |
| `Issuance_Date` | date (ISO 8601) | Date the exemption was issued |
| `Total_Authorized_Capacity___kW___` | decimal | Total authorized generating capacity, in kW |
| `State__s___` | string | State(s) the project is located in |
| `Waterway__s___` | string | Waterway(s) the project uses |
| `Description` | string | Project type, e.g. `Conduit Exemption` |

Note: exemptions have no expiration date, unlike licenses.

#### `ferc_active_hydro_projects_by_relicensing_due_date.csv` (825 rows)

Active licensed projects with an upcoming relicensing milestone (Notice of Intent or license
application due) in or after the current fiscal year — a subset of `active_licenses` with
relicensing-specific columns added.

| Column | Type | Description |
|---|---|---|
| `Project_Number` | string | FERC docket number |
| `Project_Name` | string | Project name |
| `Licensee` | string | Entity holding the FERC license |
| `Issuance_Date` | date (ISO 8601) | Date the license was issued |
| `Expiration_Date` | date (ISO 8601) | Date the license expires |
| `NOI_Due_Date` | date (ISO 8601) | Date the Notice of Intent to relicense is due |
| `Relicense_NOI_Due_Date_Fiscal_Year` | string | Fiscal year of the NOI due date |
| `Relicense_Application_Due_Date` | date (ISO 8601) | Date the full relicense application is due |
| `Relicense_Application_Due_Date_Fiscal_Year` | string | Fiscal year of the application due date |
| `Total_Authorized_Capacity___kW___` | decimal | Total authorized generating capacity, in kW |
| `State__s___` | string | State(s) the project is located in |
| `Waterway__s___` | string | Waterway(s) the project uses |
| `Description` | string | Project type |
| `Branch` | string | FERC Office of Energy Projects regional branch handling the project |

#### `ferc_active_hydro_licensed_marine_and_hydrokinetic_projects.csv` (3 rows)

Active licensed projects that generate electricity from waves or directly from the flow of
water in ocean currents, tides, or inland waterways (wave/tidal/hydrokinetic, as opposed to
conventional dam-based hydro).

| Column | Type | Description |
|---|---|---|
| `Project_Number` | string | FERC docket number |
| `Project_Name` | string | Project name |
| `Expiration_Date` | date (ISO 8601) | Date the license expires |
| `Issuance_Date` | date (ISO 8601) | Date the license was issued |
| `Total_Authorized_Capacity___kW___` | decimal | Total authorized generating capacity, in kW |
| `Licensee` | string | Entity holding the FERC license |
| `Waterway__s___` | string | Waterway(s) the project uses |
| `State__s___` | string | State(s) the project is located in |
| `Description` | string | Project type, e.g. `Hydrokinetic Wave` |

### Caveats

- All four tables are point-in-time snapshots of FERC's *currently* active projects — they
  are not historical/versioned, so a project that's relicensed, surrendered, or terminated
  will simply disappear from these tables on a future run rather than being flagged as
  changed.
- Column names carry over FERC's raw internal naming, including doubled trailing
  underscores from parenthetical units, e.g. `Total_Authorized_Capacity___kW___` means
  "Total Authorized Capacity (kW)".
