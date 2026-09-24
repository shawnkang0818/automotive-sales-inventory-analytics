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

master["growth_gap_3m_avg"] = (
    master["inventory_growth_gap"]
    .rolling(window=3)
    .mean()
)

gap_stats = master["growth_gap_3m_avg"].dropna().describe()

print("\n3-Month Growth Gap Historical Summary:")
print(gap_stats)

gap_percentiles = (
    master["growth_gap_3m_avg"]
    .dropna()
    .quantile([0.25, 0.50, 0.75, 0.90])
)

print("\n3-Month Growth Gap Percentiles:")
print(gap_percentiles)

gap_p75 = master["growth_gap_3m_avg"].quantile(0.75)
gap_p90 = master["growth_gap_3m_avg"].quantile(0.90)

def classify_trend_risk(gap):
    if pd.isna(gap):
        return "Insufficient Data"
    elif gap >= gap_p90:
        return "High"
    elif gap >= gap_p75:
        return "Rising"
    else:
        return "Normal"

master["inventory_trend_risk"] = (
    master["growth_gap_3m_avg"]
    .apply(classify_trend_risk)
)

risk_columns = [
    "observation_date",
    "inventory_to_sales_ratio",
    "inventory_growth_gap",
    "growth_gap_3m_avg",
    "inventory_pressure_level",
    "inventory_trend_risk"
]

print(
    master[risk_columns]
    .tail(18)
    .round(2)
    .to_string(index=False)
)

recent_benchmark = master[
    master["observation_date"] >= "2021-01-01"
].copy()

recent_ratio_percentiles = (
    recent_benchmark["inventory_to_sales_ratio"]
    .quantile([0.25, 0.50, 0.75, 0.90])
)

print("\nRecent Inventory-to-Sales Ratio Percentiles (2021+):")
print(recent_ratio_percentiles)

recent_gap_percentiles = (
    recent_benchmark["growth_gap_3m_avg"]
    .dropna()
    .quantile([0.25, 0.50, 0.75, 0.90])
)

print("\nRecent 3-Month Growth Gap Percentiles (2021+):")
print(recent_gap_percentiles)

current_ratio = master["inventory_to_sales_ratio"].iloc[-1]
current_gap = master["growth_gap_3m_avg"].iloc[-1]

recent_ratio_rank = (
    recent_benchmark["inventory_to_sales_ratio"] <= current_ratio
).mean() * 100

recent_gap_rank = (
    recent_benchmark["growth_gap_3m_avg"].dropna() <= current_gap
).mean() * 100

print("\nCurrent Ratio:", round(current_ratio, 2))
print("Recent Ratio Percentile Rank:", round(recent_ratio_rank, 1))

print("\nCurrent 3M Growth Gap:", round(current_gap, 2))
print("Recent Growth Gap Percentile Rank:", round(recent_gap_rank, 1))

recent_ratio_p75 = recent_benchmark[
    "inventory_to_sales_ratio"
].quantile(0.75)

recent_ratio_p90 = recent_benchmark[
    "inventory_to_sales_ratio"
].quantile(0.90)

def classify_recent_inventory_pressure(ratio):
    if ratio >= recent_ratio_p90:
        return "High"
    elif ratio >= recent_ratio_p75:
        return "Elevated"
    else:
        return "Normal"

master["recent_inventory_pressure"] = (
    master["inventory_to_sales_ratio"]
    .apply(classify_recent_inventory_pressure)
)

def recommend_planning_action(row):
    #long_term = row["inventory_pressure_level"]
    recent = row["recent_inventory_pressure"]
    trend = row["inventory_trend_risk"]

    if recent == "High" and trend == "High":
        return "Review Production and Promotion"

    elif recent in ["High", "Elevated"] and trend in ["High", "Rising"]:
        return "Investigate Inventory Pressure"

    elif recent in ["High", "Elevated"] and trend == "Normal":
        return "Monitor Elevated Inventory"

    elif recent == "Normal" and trend in ["High", "Rising"]:
        return "Monitor Emerging Trend"

    else:
        return "Maintain and Monitor"

master["planning_action"] = master.apply(
    recommend_planning_action,
    axis=1
)

action_columns = [
    "observation_date",
    "inventory_to_sales_ratio",
    "growth_gap_3m_avg",
    "inventory_pressure_level",
    "inventory_trend_risk",
    "planning_action"
]

print(
    master[action_columns]
    .tail(18)
    .round(2)
    .to_string(index=False)
)

comparison_columns = [
    "observation_date",
    "inventory_to_sales_ratio",
    "inventory_pressure_level",
    "recent_inventory_pressure",
    "growth_gap_3m_avg",
    "inventory_trend_risk",
    "planning_action"
]

print(
    master[comparison_columns]
    .tail(18)
    .round(2)
    .to_string(index=False)
)


master.to_csv(
    "data/processed/monthly_automotive_master.csv",
    index=False
)