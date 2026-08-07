import pandas as pd
import numpy as np

# Silence some warnings about deprecated Pandas behavior
pd.set_option("future.no_silent_downcasting", True)

def full_pipeline():
    pr_gen_fuel, pr_plant_frame = read_data()
    pr_gen_fuel = cleaned(pr_gen_fuel, [
        "energy_source_code",
        "fuel_type_code_agg",
        "prime_mover_code",
        "reporting_frequency_code",
        "data_maturity",
        "plant_state",
    ])
    pr_plant_frame = cleaned(pr_plant_frame, [
        "reporting_frequency_code",
        "data_maturity",
        "plant_state",
    ])
    index_cols = ["plant_id_eia", "plant_name_eia", "report_year", "prime_mover_code", "energy_source_code", "fuel_unit"]

    pr_gen_fuel_monthly = pivoted_all_monthly_cols(
        pr_gen_fuel,
        [
            "fuel_consumed_for_electricity_mmbtu",
            "fuel_consumed_for_electricity_units",
            "fuel_consumed_mmbtu",
            "fuel_consumed_units",
            "net_generation_mwh",
        ],
        index_cols
    )

    # Plant 62410 has two 2020 data entries but one is null
    # Drop the bad row
    pr_gen_fuel_monthly = pr_gen_fuel_monthly.loc[
        ~((pr_gen_fuel_monthly.plant_id_eia == 62410) 
          & (pr_gen_fuel_monthly.date.dt.year == 2020)
          & (pr_gen_fuel_monthly.fuel_consumed_for_electricity_mmbtu.isnull()))
    ]
    # drop after 2025-03-01 (for now) as these values should not exist
    pr_gen_fuel_monthly = pr_gen_fuel_monthly.loc[pr_gen_fuel_monthly.date < pd.Timestamp("2025-03-01")]

    pr_gen_fuel_annual = pr_gen_fuel.loc[
        :,
        index_cols + ["total_fuel_consumption_mmbtu", "total_fuel_consumption_quantity", "total_net_generation_mwh"]
    ]
    # this plot takes a while
    #check_nulls_plot(pr_gen_fuel_monthly)
    ### output
    pr_gen_fuel_monthly.to_parquet("pr_gen_fuel_monthly.parquet")
    pr_gen_fuel_annual.to_parquet("pr_gen_fuel_annual.parquet")
    pr_plant_frame.to_parquet("pr_plant_frame.parquet")

def check_nulls_plot(pr_gen_fuel):
    ## some investigation into NA values
    clean_index_cols = ["date", "energy_source_code", "prime_mover_code", "plant_id_eia", "plant_name_eia", "fuel_unit"]
    pp = pr_gen_fuel.set_index(clean_index_cols).isna().all(axis=1).reset_index().rename(columns={0: "isna"}).loc[:, ["date", "plant_name_eia", "isna"]]

    pp.plot.scatter(x="date", y="plant_name_eia", c=pp["isna"].astype(int), colormap="viridis", s=10, alpha=0.2, figsize=(10, 20))

    # it turns out that after 2025-03-01 there's a pile of NAs, and many plants have multiple generators, some of which report as all-NA while their sibling generators are reporting non-NA values
    # though Aguirre Plant and Hewlett Packard Puerto Rico seem to have actual stretches of all-NA time that might be wroth dropping.

def cleaned(df, categories):
    df = fix_eia_nulls(df)
    df = convert_data_types(df)
    convert_yn_boolean(df, "associated_combined_heat_power")
    return df.astype({
        c: "category"
        for c in categories
    })

def read_data():
    pr_gen_fuel = pd.read_parquet("raw_eia923__puerto_rico_generation_fuel.parquet")
    pr_plant_frame = pd.read_parquet("raw_eia923__puerto_rico_plant_frame.parquet")
    return pr_gen_fuel, pr_plant_frame

def fix_eia_nulls(df):
    # Handle EIA null values
    return df.replace(to_replace = ".", value = pd.NA)

def convert_data_types(df):
    # Convert data types (mmbtu/units to numeric, booleans, categories)
    df = df.convert_dtypes()
    for colname in df.columns:
        if (
                "fuel_consumption" in colname
                or "fuel_consumed" in colname
                or "net_generation" in colname
                or "fuel_mmbtu_per_unit" in colname
        ):
            df[colname] = df[colname].astype("float64")
    return df

def convert_yn_boolean(df, column):
    # Some booleans were coded as "Y" "N" but we want True False
    df[column] = (
        df[column]
        .astype("object") # necessary for the types to work for the .replace() call
        .replace({"Y": True, "N": False})
        .astype("boolean")
    )

def pivoted_monthly_cols(df, prefix, index_cols):
    cols = index_cols + [col for col in df.columns if col.startswith(prefix)]
    subset = df.loc[:, cols]
    
    ## Melt the fuel_consumed columns
    subset = subset.melt(
        id_vars=index_cols,
        var_name="month",
        value_name=prefix
    )
    subset["month"] = subset["month"].str.replace(f"{prefix}_", "")
    return subset.set_index(index_cols + ["month"])
    
def pivoted_all_monthly_cols(df, variables, index_cols):
    df = pd.concat(
        [
            pivoted_monthly_cols(df, v, index_cols)
            for v in variables
        ], 
        axis="columns",
    ).reset_index()
    ## Create date from month and year
    df["date"] = pd.to_datetime(
        df["month"] + df["report_year"].astype(str),
        format="%B%Y",
    )
    ## Drop old date columns
    return df.drop(columns = ["report_year", "month"])

if __name__ == "__main__":
    full_pipeline()
