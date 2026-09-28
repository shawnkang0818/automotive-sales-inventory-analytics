import pandas as pd


# --------------------------------------------------
# Load synthetic operational data
# --------------------------------------------------

data_path = "data/synthetic/synthetic_operations.csv"

df = pd.read_csv(
    data_path,
    parse_dates=["month"]
)

print(df.shape)

# --------------------------------------------------
# Production planning KPIs
# --------------------------------------------------

df["production_vs_forecast_gap_units"] = (
    df["production_units"]
    - df["forecast_units"]
)

df["production_vs_demand_gap_units"] = (
    df["production_units"]
    - df["demand_units"]
)

df["production_vs_demand_gap_units"] = (
    df["production_units"]
    - df["demand_units"]
)

# --------------------------------------------------
# Vehicle-model production summary
# --------------------------------------------------

model_summary = (
    df.groupby("vehicle_model")
    .agg(
        total_forecast_units=(
            "forecast_units",
            "sum"
        ),
        total_demand_units=(
            "demand_units",
            "sum"
        ),
        total_production_units=(
            "production_units",
            "sum"
        ),
        total_sales_units=(
            "sales_units",
            "sum"
        ),
        total_lost_sales_units=(
            "lost_sales_units",
            "sum"
        ),
        average_ending_inventory=(
            "ending_inventory_units",
            "mean"
        ),
    )
    .reset_index()
)

# Positive = production above forecast
# Negative = production below forecast
model_summary["production_vs_forecast_gap_units"] = (
    model_summary["total_production_units"]
    - model_summary["total_forecast_units"]
)

# Positive = production above demand
# Negative = production below demand
model_summary["production_vs_demand_gap_units"] = (
    model_summary["total_production_units"]
    - model_summary["total_demand_units"]
)

# --------------------------------------------------
# Relative production gaps
# --------------------------------------------------

# Measures production deviation from forecast as a percentage
# of total forecast volume.
model_summary["production_vs_forecast_gap_pct"] = (
    model_summary["production_vs_forecast_gap_units"]
    / model_summary["total_forecast_units"]
    * 100
)

# Measures production deviation from actual demand as a percentage
# of total demand volume.
model_summary["production_vs_demand_gap_pct"] = (
    model_summary["production_vs_demand_gap_units"]
    / model_summary["total_demand_units"]
    * 100
)

# Percentage of customer demand that was actually fulfilled.
# Values below 100% indicate lost sales due to insufficient available inventory.
model_summary["demand_fulfillment_rate_pct"] = (
    model_summary["total_sales_units"]
    / model_summary["total_demand_units"]
    * 100
)

print(
    "\nVehicle Model Production Summary:"
)

print(
    model_summary
    .round(2)
    .to_string(index=False)
)

# --------------------------------------------------
# Region × vehicle-model production summary
# --------------------------------------------------

region_model_summary = (
    df.groupby(
        ["region", "vehicle_model"]
    )
    .agg(
        total_forecast_units=(
            "forecast_units",
            "sum"
        ),
        total_demand_units=(
            "demand_units",
            "sum"
        ),
        total_production_units=(
            "production_units",
            "sum"
        ),
        total_sales_units=(
            "sales_units",
            "sum"
        ),
        total_lost_sales_units=(
            "lost_sales_units",
            "sum"
        ),
        average_ending_inventory=(
            "ending_inventory_units",
            "mean"
        ),
    )
    .reset_index()
)

# --------------------------------------------------
# Absolute planning gaps
# --------------------------------------------------

# Production relative to forecast
region_model_summary["production_vs_forecast_gap_units"] = (
    region_model_summary["total_production_units"]
    - region_model_summary["total_forecast_units"]
)

# Production relative to actual demand
region_model_summary["production_vs_demand_gap_units"] = (
    region_model_summary["total_production_units"]
    - region_model_summary["total_demand_units"]
)

# Forecast compared with actual demand.
# Negative values mean demand was higher than forecast.
region_model_summary["forecast_vs_demand_gap_units"] = (
    region_model_summary["total_forecast_units"]
    - region_model_summary["total_demand_units"]
)

# --------------------------------------------------
# Relative planning KPIs
# --------------------------------------------------

# Relative production deviation from forecast
region_model_summary["production_vs_forecast_gap_pct"] = (
    region_model_summary["production_vs_forecast_gap_units"]
    / region_model_summary["total_forecast_units"]
    * 100
)

# Relative production deviation from actual demand
region_model_summary["production_vs_demand_gap_pct"] = (
    region_model_summary["production_vs_demand_gap_units"]
    / region_model_summary["total_demand_units"]
    * 100
)

# Forecast error relative to total demand.
# Negative = demand exceeded forecast.
# Positive = forecast exceeded demand.
region_model_summary["forecast_vs_demand_gap_pct"] = (
    region_model_summary["forecast_vs_demand_gap_units"]
    / region_model_summary["total_demand_units"]
    * 100
)

# Percentage of demand that was fulfilled
region_model_summary["demand_fulfillment_rate_pct"] = (
    region_model_summary["total_sales_units"]
    / region_model_summary["total_demand_units"]
    * 100
)

# --------------------------------------------------
# Region-model stockout frequency
# --------------------------------------------------

region_model_stockout = (
    df.assign(
        stockout_flag=(
            df["lost_sales_units"] > 0
        )
    )
    .groupby(
        ["region", "vehicle_model"]
    )["stockout_flag"]
    .mean()
    .mul(100)
    .reset_index(
        name="stockout_rate_pct"
    )
)

region_model_summary = region_model_summary.merge(
    region_model_stockout,
    on=["region", "vehicle_model"],
    how="left"
)

# --------------------------------------------------
# Planning issue classification
# --------------------------------------------------

def classify_planning_issue(row):
    """
    Classify each region-model combination based on
    forecast accuracy, production execution, and stockout impact.
    """

    forecast_underestimated = (
        row["forecast_vs_demand_gap_pct"] <= -1.0
    )

    production_shortfall = (
        row["production_vs_forecast_gap_pct"] <= -2.0
    )

    meaningful_stockout = (
        row["stockout_rate_pct"] >= 5.0
    )

    # Both demand forecasting and production execution
    # contributed to the observed shortage.
    if (
        forecast_underestimated
        and production_shortfall
        and meaningful_stockout
    ):
        return "Mixed Issue"

    # Forecast was reasonably close to demand,
    # but production did not keep up with the forecast.
    if (
        production_shortfall
        and meaningful_stockout
    ):
        return "Production Issue"

    # Demand exceeded forecast enough to contribute
    # to stockout risk, while production broadly followed plan.
    if (
        forecast_underestimated
        and meaningful_stockout
    ):
        return "Forecast Issue"

    # Stockouts occurred even though aggregate forecast
    # and production gaps do not fully explain them.
    # This suggests timing or allocation mismatch.
    if meaningful_stockout:
        return "Inventory / Timing Review"

    return "Balanced"

region_model_summary["planning_issue_type"] = (
    region_model_summary.apply(
        classify_planning_issue,
        axis=1
    )
)

# --------------------------------------------------
# Planning recommendations
# --------------------------------------------------

def recommend_planning_action(row):
    """
    Convert the planning diagnosis into a practical business action.
    """

    if row["planning_issue_type"] == "Mixed Issue":
        return (
            "Review both forecast assumptions and production allocation"
        )

    if row["planning_issue_type"] == "Production Issue":
        return (
            "Review production execution and regional allocation"
        )

    if row["planning_issue_type"] == "Forecast Issue":
        return (
            "Review demand forecast assumptions and recent demand signals"
        )

    if row["planning_issue_type"] == "Inventory / Timing Review":
        return (
            "Review inventory timing and dealer-level allocation"
        )

    return "Maintain current plan and continue monitoring"

region_model_summary["recommended_planning_action"] = (
    region_model_summary.apply(
        recommend_planning_action,
        axis=1
    )
)

# --------------------------------------------------
# Output
# --------------------------------------------------

print(
    "\nRegion × Vehicle Model Production Summary:"
)

print(
    region_model_summary
    .round(2)
    .to_string(index=False)
)

print(
    "\nProduction Planning Diagnosis:"
)

print(
    region_model_summary[
        [
            "region",
            "vehicle_model",
            "forecast_vs_demand_gap_pct",
            "production_vs_forecast_gap_pct",
            "stockout_rate_pct",
            "demand_fulfillment_rate_pct",
            "planning_issue_type",
        ]
    ]
    .round(2)
    .to_string(index=False)
)

print(
    "\nProduction Planning Recommendations:"
)

print(
    region_model_summary[
        [
            "region",
            "vehicle_model",
            "planning_issue_type",
            "recommended_planning_action",
        ]
    ]
    .to_string(index=False)
)