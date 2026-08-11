# PR Generation Fuel & Plant Frame data cleaning pipeline

This pipeline loads, cleans, and exports raw EIA-923 data about Puerto Rico, 
producing 3 data frames:

* pr_gen_fuel_monthly.parquet - Monthly plant-level generation and fuel consumption split out by fuel & prime mover:
  one row per *month* x plant x fuel x prime mover.
* pr_gen_fuel_annual.parquet - Annual plant-level generation and fuel consumption split out by fuel & prime mover:
  one row per *year* x plant x fuel x prime mover.
* pr_plant_frame.parquet - Annual/monthly plant characteristics like NAICS code, sector, etc.

Outputs have the EIA's n/a notation (".") converted to true nulls, 
nice data types (booleans instead of yes/no strings, proper categories), 
and a few known-bad rows dropped.

The input data comes from [the OED4A course repo](https://github.com/catalyst-cooperative/open-energy-data-for-all/tree/main/data). 
**Before you run this code, you should download the following two files and save them to this directory:**

* [raw_eia923__puerto_rico_generation_fuel.parquet](https://github.com/catalyst-cooperative/open-energy-data-for-all/raw/refs/heads/main/data/raw_eia923__puerto_rico_generation_fuel.parquet)
* [raw_eia923__puerto_rico_plant_frame.parquet](https://github.com/catalyst-cooperative/open-energy-data-for-all/raw/refs/heads/main/data/raw_eia923__puerto_rico_plant_frame.parquet)

I'm not sure if it works correctly!
This is abandoned code that Catalyst was playing with for a different OED4A lesson.

The documentation is really sparse 🫣 so you'll need to use your best judgement for what's supposed to happen in each function.
