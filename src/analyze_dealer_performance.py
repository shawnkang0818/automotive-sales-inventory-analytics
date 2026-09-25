import pandas as pd

data_path = "data/synthetic/synthetic_operations.csv"

df = pd.read_csv(
    data_path,
    parse_dates=["month"]
)

print(df.shape)
print(df.columns.tolist())


dealer_performance = (
    df.groupby(
        ["region", "dealer_id"]
    )
    .agg(
        total_sales_units=(
            "sales_units",
            "sum"
        ),
        total_demand_units=(
            "demand_units",
            "sum"
        ),
        total_revenue=(
            "revenue",
            "sum"
        ),
        forecast_mape=(
            "absolute_forecast_error_pct",
            "mean"
        ),
        average_ending_inventory=(
            "ending_inventory_units",
            "mean"
        ),
        total_lost_sales=(
            "lost_sales_units",
            "sum"
        ),
    )
    .reset_index()
)

stockout_rate = (
    df.assign(
        stockout_flag=(
            df["lost_sales_units"] > 0
        )
    )
    .groupby(
        ["region", "dealer_id"]
    )["stockout_flag"]
    .mean()
    .mul(100)
    .reset_index(
        name="stockout_rate_pct"
    )
)

dealer_performance = dealer_performance.merge(
    stockout_rate,
    on=["region", "dealer_id"],
    how="left"
)

promotion_rate = (
    df.groupby(
        ["region", "dealer_id"]
    )["promotion_flag"]
    .mean()
    .mul(100)
    .reset_index(
        name="promotion_rate_pct"
    )
)

inventory_ratio = (
    df.groupby(
        ["region", "dealer_id"]
    )["inventory_to_sales_ratio"]
    .mean()
    .reset_index(
        name="avg_inventory_to_sales_ratio"
    )
)

production_demand = (
    df.groupby(
        ["region", "dealer_id"]
    )
    .agg(
        total_production_units=(
            "production_units",
            "sum"
        ),
        total_demand_units_check=(
            "demand_units",
            "sum"
        ),
    )
    .reset_index()
)

production_demand["production_demand_gap_units"] = (
    production_demand["total_production_units"]
    - production_demand["total_demand_units_check"]
)

dealer_performance["demand_fulfillment_rate_pct"] = (
    dealer_performance["total_sales_units"]
    / dealer_performance["total_demand_units"]
    * 100
)

dealer_performance = (
    dealer_performance
    .merge(
        promotion_rate,
        on=["region", "dealer_id"],
        how="left"
    )
    .merge(
        inventory_ratio,
        on=["region", "dealer_id"],
        how="left"
    )
    .merge(
        production_demand[
            [
                "region",
                "dealer_id",
                "total_production_units",
                "production_demand_gap_units",
            ]
        ],
        on=["region", "dealer_id"],
        how="left"
    )
)

dealer_performance["supply_pressure_flag"] = (
    (dealer_performance["stockout_rate_pct"] >= 5)
    | (dealer_performance["demand_fulfillment_rate_pct"] < 99.5)
)

dealer_performance["inventory_pressure_flag"] = (
    (dealer_performance["avg_inventory_to_sales_ratio"] >= 0.75)
    & (dealer_performance["stockout_rate_pct"] < 5)
)

dealer_performance["forecast_review_flag"] = (
    dealer_performance["forecast_mape"] >= 9
)

def recommend_dealer_action(row):
    if row["supply_pressure_flag"] and row["forecast_review_flag"]:
        return "Review forecast accuracy and increase allocation support"

    elif row["supply_pressure_flag"]:
        return "Review allocation and monitor stockout risk"

    elif row["inventory_pressure_flag"]:
        return "Review inventory levels and promotion effectiveness"

    else:
        return "Maintain current plan and continue monitoring"


dealer_performance["recommended_action"] = (
    dealer_performance.apply(
        recommend_dealer_action,
        axis=1
    )
)

print(
    "\nDealer Performance Scorecard:"
)

print(
    dealer_performance
    .round(2)
    .to_string(index=False)
)

print(
    "\nDealer Diagnostic Flags:"
)

print(
    dealer_performance[
        [
            "region",
            "dealer_id",
            "supply_pressure_flag",
            "inventory_pressure_flag",
            "forecast_review_flag",
        ]
    ]
    .to_string(index=False)
)

print(
    "\nDealer Recommendations:"
)

print(
    dealer_performance[
        [
            "region",
            "dealer_id",
            "recommended_action",
        ]
    ]
    .to_string(index=False)
)