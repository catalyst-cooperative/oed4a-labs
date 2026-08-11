# EIA Thermoelectric Cooling Water Data

The EIA publishes data about thermoelectric cooling water use The data is available on
this page:

https://www.eia.gov/electricity/data/water/

The script in this directory downloads all of the spreadsheets and tries to convert them
into a single file with all the detailed data across all years.

## Dataset documentation

### How to (re)build the data

Run `uv run download_and_combine.py` from this directory. It downloads each
year's "Detail" workbook (2014-2024) from the EIA thermoelectric cooling
water page into `spreadsheets/` (skipping files already present), then
concatenates every worksheet tab across years into one CSV per tab in this
directory. Useful flags:

- `--force`: re-download every spreadsheet even if already on disk (use
  this if EIA revises a prior year's file).
- `--no-download`: skip downloading and just re-combine whatever is
  already in `spreadsheets/`.

To pick up a new year, add its URL to the `YEAR_URLS` dict in
`download_and_combine.py` and re-run the script.

Source data comes from EIA Form 923, Schedule 8 ("Annual Boiler Fuel
Consumption and Cooling System Information"), published as part of the
Cooling Water Data files at
https://www.eia.gov/electricity/data/water/. EIA has changed the workbook
file-naming convention several times over the years (`cooling_detail_YYYY`
through 2020, `Cooling_Boiler_Generator_Data_Detail_YYYY` from 2021
onward), but the underlying "Detail" tab's column layout has stayed
identical (70 raw columns) across all 11 years, so no column renaming was
needed beyond normalizing whitespace/newlines in the header text and
dropping two always-blank spacer columns left over from merged header
cells.

### `eia_thermoelectric_cooling_detail.csv`

One row per generator/boiler/cooling-system/month combination at a given
power plant, for report years 2014-2024 (~83,000 rows/year, ~917,000 rows
total). This is monthly data collected on EIA Form 923, Schedule 8, from
thermoelectric generating units that use water for cooling; it reports how
each unit's cooling system withdraws and consumes water, alongside the
generation, fuel consumption, and equipment identifiers needed to join
back to other EIA-860/923 tables.

Grain: one row = one plant + generator + boiler + cooling system, for one
month of one report year. `data_year` records which annual file a row came
from (equal to the `Year` column in all observed data, kept as a
convenience/provenance field and for sanity-checking during combination).

| Column | Description |
|---|---|
| `data_year` | Report year of the source workbook this row was read from (redundant with `Year`; used for provenance/QA). |
| `Utility ID` | EIA utility (company) identifier for the plant's owner/operator. |
| `State` | Two-letter postal abbreviation of the state where the plant is located. |
| `Plant Code` | EIA plant identifier. |
| `Plant Name` | Name of the power plant. |
| `Year` | Report year (should equal `data_year`). |
| `Month` | Report month (1-12). |
| `Generator ID` | Plant-specific generator identifier. |
| `Boiler ID` | Plant-specific boiler identifier. |
| `Cooling ID` | Plant-specific cooling system identifier. |
| `Generator Primary Technology` | EIA technology type of the associated generator (e.g. "Natural Gas Steam Turbine"). |
| `Summer Capacity of Steam Turbines (MW)` | Summer net capacity of steam turbine(s) associated with this boiler/cooling system. |
| `Gross Generation from Steam Turbines (MWh)` | Monthly gross generation attributable to steam turbines. |
| `Net Generation from Steam Turbines (MWh)` | Monthly net generation attributable to steam turbines. |
| `Summer Capacity Associated with Single Shaft Combined Cycle Units (MW)` | Summer capacity of single-shaft combined-cycle units sharing this cooling system. |
| `Gross Generation Associated with Single Shaft Combined Cycle Units (MWh)` | Monthly gross generation from single-shaft combined-cycle units. |
| `Net Generation Associated with Single Shaft Combined Cycle Units (MWh)` | Monthly net generation from single-shaft combined-cycle units. |
| `Summer Capacity Associated with Combined Cycle Gas Turbines (MW)` | Summer capacity of combined-cycle gas turbine units sharing this cooling system. |
| `Gross Generation Associated with Combined Cycle Gas Turbines (MWh)` | Monthly gross generation from combined-cycle gas turbines. |
| `Net Generation Associated with Combined Cycle Gas Turbines (MWh)` | Monthly net generation from combined-cycle gas turbines. |
| `Fuel Consumption from All Fuel Types (MMBTU)` | Total monthly fuel heat input across all fuel types for this boiler. |
| `Fuel Consumption from Steam Turbines (MMBTU)` | Fuel consumption attributable to steam turbine operation. |
| `Fuel Consumption from Single Shaft Combined Cycle Units (MMBTU)` | Fuel consumption attributable to single-shaft combined-cycle units. |
| `Fuel Consumption from Combined Cycle Gas Turbines (MMBTU)` | Fuel consumption attributable to combined-cycle gas turbines. |
| `Coal Consumption (MMBTU)` | Monthly heat input from coal. |
| `Natural Gas Consumption (MMBTU)` | Monthly heat input from natural gas. |
| `Petroleum Consumption (MMBTU)` | Monthly heat input from petroleum products. |
| `Biomass Consumption (MMBTU)` | Monthly heat input from biomass fuels. |
| `Other Gas Consumption (MMBTU)` | Monthly heat input from other gaseous fuels (e.g. blast furnace gas). |
| `Other Fuel Consumption (MMBTU)` | Monthly heat input from other/unclassified fuels. |
| `Water Withdrawal Volume (Million Gallons)` | Total monthly water withdrawn by the cooling system. |
| `Water Consumption Volume (Million Gallons)` | Total monthly water consumed (withdrawn but not returned to source) by the cooling system. |
| `Water Withdrawal Intensity Rate (Gallons / MWh)` | Water withdrawal per unit of net generation. |
| `Water Consumption Intensity Rate (Gallons / MWh)` | Water consumption per unit of net generation. |
| `Water Withdrawal Rate per Fuel Consumption (Gallons / MMBTU)` | Water withdrawal per unit of fuel heat input. |
| `Water Consumption Rate per Fuel Consumption (Gallons / MMBTU)` | Water consumption per unit of fuel heat input. |
| `Cooling Unit Hours in Service` | Hours the cooling system operated during the month. |
| `Average Distance of Water Intake Below Water Surface (Feet)` | Depth of the cooling water intake below the surface of the water source. |
| `860 Cooling Type 1` | Primary cooling system type code, as reported on EIA-860. |
| `860 Cooling Type 2` | Secondary cooling system type code, as reported on EIA-860 (if applicable). |
| `923 Cooling Type` | Cooling system type code as reported on this EIA-923 schedule. |
| `Cooling System Type` | Descriptive cooling system type (e.g. once-through, recirculating/tower, dry, hybrid). |
| `Water Type` | Type of water used (e.g. fresh, saline, reclaimed). |
| `Water Source` | Code identifying the water source category (e.g. surface water, groundwater, public supply). |
| `Water Source Name` | Name of the specific water body or source supplying the cooling system. |
| `Water Discharge Name` | Name of the water body or destination receiving discharged cooling water. |
| `Generator Status` | Operating status of the generator (e.g. operating, standby, retired). |
| `Generator Inservice Month` / `Generator Inservice Year` | Month/year the generator entered service. |
| `Generator Retirement Month` / `Generator Retirement Year` | Month/year the generator retired, if applicable. |
| `Boiler Status` | Operating status of the boiler. |
| `Boiler Inservice Month` / `Boiler Inservice Year` | Month/year the boiler entered service. |
| `Boiler Retirement Month` / `Boiler Retirement Year` | Month/year the boiler retired, if applicable. |
| `Cooling Status` | Operating status of the cooling system. |
| `Cooling Inservice Month` / `Cooling Inservice Year` | Month/year the cooling system entered service. |
| `Combined Heat and Power Generator?` | Y/N flag indicating the generator is a combined heat and power (cogeneration) unit. |
| `Generator Primary Energy Source Code` | EIA fuel code for the generator's primary energy source. |
| `Generator Prime Mover Code` | EIA prime mover code (e.g. ST, CT, CA) for the generator. |
| `Generator Duct Burners?` | Y/N flag indicating whether the generator's combined-cycle unit has duct burners. |
| `Sector` | EIA sector code for the plant/generator (e.g. electric utility, IPP). |
| `Steam Plant Type` | Classification of the steam plant (e.g. fossil, nuclear). |
| `Relationship Type` | Describes how the generator, boiler, and cooling system are associated (e.g. one-to-one, shared/topped). |
| `Number Operable Generators` | Count of operable generators associated with this cooling system. |
| `Number Operable Boilers` | Count of operable boilers associated with this cooling system. |
| `Number Operable Cooling Systems` | Count of operable cooling systems at the plant. |
