import pandas as pd

sales = pd.read_csv("data/raw/TOTALSA.csv")
inventory = pd.read_csv("data/raw/AUINSA.csv")
dealer_sales = pd.read_csv("data/raw/MRTSSM441USS.csv")
dealer_inventory = pd.read_csv("data/raw/MRTSIM441USS.csv")

print(sales.head())
print(inventory.head())
print(dealer_sales.head())
print(dealer_inventory.head())

datasets = {
    "vehicle_sales": sales,
    "vehicle_inventory": inventory,
    "dealer_sales": dealer_sales,
    "dealer_inventory": dealer_inventory,
}

for name, df in datasets.items():
    print(f"\n--- {name} ---")
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("Data types:")
    print(df.dtypes)
    print("Missing values:")
    print(df.isna().sum())

for df in datasets.values():
    df["observation_date"] = pd.to_datetime(df["observation_date"])

for name, df in datasets.items():
    print(name, df["observation_date"].dtype)

start_date = max(df["observation_date"].min() for df in datasets.values())
end_date = min(df["observation_date"].max() for df in datasets.values())

print("Common start date:", start_date)
print("Common end date:", end_date)

for name, df in datasets.items():
    datasets[name] = df[
        (df["observation_date"] >= start_date) &
        (df["observation_date"] <= end_date)
    ].copy()

master = datasets["vehicle_sales"]

for name in ["vehicle_inventory", "dealer_sales", "dealer_inventory"]:
    master = master.merge(
        datasets[name],
        on="observation_date",
        how="inner"
    )

print(master.head())
print(master.tail())
print(master.shape)
print(master.isna().sum())


master = master.rename(columns={
    "TOTALSA": "vehicle_sales_saar_millions",
    "AUINSA": "domestic_auto_inventory_thousands",
    "MRTSSM441USS": "dealer_sales_millions_usd",
    "MRTSIM441USS": "dealer_inventory_millions_usd"
})

master["inventory_to_sales_ratio"] = (
    master["dealer_inventory_millions_usd"]
    / master["dealer_sales_millions_usd"]
)

print(
    master[
        [
            "observation_date",
            "dealer_sales_millions_usd",
            "dealer_inventory_millions_usd",
            "inventory_to_sales_ratio"
        ]
    ].tail(12)
)

master["sales_mom_pct"] = (
    master["dealer_sales_millions_usd"]
    .pct_change() * 100
)

master["inventory_mom_pct"] = (
    master["dealer_inventory_millions_usd"]
    .pct_change() * 100
)

master["sales_yoy_pct"] = (
    master["dealer_sales_millions_usd"]
    .pct_change(periods=12) * 100
)

master["inventory_yoy_pct"] = (
    master["dealer_inventory_millions_usd"]
    .pct_change(periods=12) * 100
)

columns_to_view = [
    "observation_date",
    "dealer_sales_millions_usd",
    "dealer_inventory_millions_usd",
    "inventory_to_sales_ratio",
    "sales_yoy_pct",
    "inventory_yoy_pct"
]
print(
    master[columns_to_view]
    .tail(12)
    .round(2)
    .to_string(index=False)
)

master["inventory_growth_gap"] = (
    master["inventory_yoy_pct"]
    - master["sales_yoy_pct"]
)

analysis_columns = [
    "observation_date",
    "sales_yoy_pct",
    "inventory_yoy_pct",
    "inventory_growth_gap",
    "inventory_to_sales_ratio"
]

print(
    master[analysis_columns]
    .tail(12)
    .round(2)
    .to_string(index=False)
)

ratio_stats = master["inventory_to_sales_ratio"].describe()

print("\nInventory-to-Sales Ratio Historical Summary:")
print(ratio_stats)

percentiles = master["inventory_to_sales_ratio"].quantile(
    [0.10, 0.25, 0.50, 0.75, 0.90]
)

print("\nInventory-to-Sales Ratio Percentiles:")
print(percentiles)

current_ratio = master["inventory_to_sales_ratio"].iloc[-1]

percentile_rank = (
    master["inventory_to_sales_ratio"] <= current_ratio
).mean() * 100

print("\nCurrent Ratio:", round(current_ratio, 2))
print("Historical Percentile Rank:", round(percentile_rank, 1))

p75 = master["inventory_to_sales_ratio"].quantile(0.75)
p90 = master["inventory_to_sales_ratio"].quantile(0.90)

def classify_inventory_pressure(ratio):
    if ratio >= p90:
        return "High"
    elif ratio >= p75:
        return "Elevated"
    else:
        return "Normal"

master["inventory_pressure_level"] = master[
    "inventory_to_sales_ratio"
].apply(classify_inventory_pressure)

master.to_csv(
    "data/processed/monthly_automotive_master.csv",
    index=False
)

print(
    master[
        [
            "observation_date",
            "inventory_to_sales_ratio",
            "inventory_growth_gap",
            "inventory_pressure_level"
        ]
    ]
    .tail(12)
    .to_string(index=False)
)