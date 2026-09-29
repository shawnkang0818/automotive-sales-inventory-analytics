import os

import matplotlib.pyplot as plt
import pandas as pd


# --------------------------------------------------
# File paths
# --------------------------------------------------

# Processed rolling-backtest output created by
# build_demand_forecast.py.
data_path = "data/processed/forecast_rolling_backtest.csv"

# Folder used to store forecasting charts.
output_dir = "dashboard/forecasting"


# --------------------------------------------------
# Load processed forecast data
# --------------------------------------------------

df = pd.read_csv(
    data_path,
    parse_dates=["month"]
)

print(
    "Forecast data shape:",
    df.shape
)

print(
    "\nForecast data columns:"
)

print(
    df.columns.tolist()
)


# --------------------------------------------------
# Prepare output directory
# --------------------------------------------------

# Create the output folder if it does not exist.
# exist_ok=True prevents an error if it already exists.
os.makedirs(
    output_dir,
    exist_ok=True
)


# --------------------------------------------------
# Sort data
# --------------------------------------------------

# Time-series charts must be plotted chronologically.
df = df.sort_values(
    ["vehicle_model", "month"]
)


# --------------------------------------------------
# Vehicle models
# --------------------------------------------------

vehicle_models = [
    "EV",
    "Pickup",
    "SUV",
    "Sedan",
]


# --------------------------------------------------
# Actual Demand vs Seasonal Naive Forecast
# --------------------------------------------------

for vehicle_model in vehicle_models:

    # Filter the rolling backtest down to one
    # vehicle model at a time.
    model_data = df[
        df["vehicle_model"] == vehicle_model
    ].copy()

    # Create a separate chart for this vehicle model.
    plt.figure(
        figsize=(10, 6)
    )

    # Actual monthly demand.
    plt.plot(
        model_data["month"],
        model_data["demand_units"],
        marker="o",
        label="Actual Demand"
    )

    # Forecast from the selected rolling-backtest model.
    plt.plot(
        model_data["month"],
        model_data["seasonal_naive_forecast"],
        marker="o",
        label="Seasonal Naive Forecast"
    )

    # --------------------------------------------------
    # Chart formatting
    # --------------------------------------------------

    plt.title(
        f"{vehicle_model}: Actual Demand vs Seasonal Naive Forecast"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Demand Units"
    )

    plt.legend()

    plt.grid(
        alpha=0.3
    )

    # Rotate month labels to improve readability.
    plt.xticks(
        rotation=45
    )

    # Prevent titles and labels from being cut off.
    plt.tight_layout()


    # --------------------------------------------------
    # Save chart
    # --------------------------------------------------

    output_path = (
        f"{output_dir}/"
        f"{vehicle_model.lower()}_actual_vs_forecast.png"
    )

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    # Close the current figure before the next loop.
    plt.close()

    print(
        "Saved:",
        output_path
    )

# --------------------------------------------------
# Load model comparison results
# --------------------------------------------------

comparison_path = (
    "data/processed/forecast_model_comparison.csv"
)

comparison_df = pd.read_csv(
    comparison_path
)

# --------------------------------------------------
# MAPE comparison by vehicle model
# --------------------------------------------------

# Create numeric x-axis positions:
# EV = 0, Pickup = 1, SUV = 2, Sedan = 3
x_positions = range(
    len(comparison_df)
)

# Width of each bar.
bar_width = 0.35

plt.figure(
    figsize=(10, 6)
)

plt.bar(
    [
        x - bar_width / 2
        for x in x_positions
    ],
    comparison_df["seasonal_naive_mape"],
    width=bar_width,
    label="Seasonal Naive"
)

plt.bar(
    [
        x + bar_width / 2
        for x in x_positions
    ],
    comparison_df["moving_average_mape"],
    width=bar_width,
    label="3-Month Moving Average"
)

plt.title(
    "Rolling Backtest MAPE by Vehicle Model"
)

plt.xlabel(
    "Vehicle Model"
)

plt.ylabel(
    "MAPE (%)"
)

plt.xticks(
    list(x_positions),
    comparison_df["vehicle_model"]
)

plt.legend()

plt.grid(
    axis="y",
    alpha=0.3
)

plt.tight_layout()

mape_output_path = (
    f"{output_dir}/"
    "model_mape_comparison.png"
)

plt.savefig(
    mape_output_path,
    dpi=150,
    bbox_inches="tight"
)

plt.close()

print(
    "Saved:",
    mape_output_path
)

# --------------------------------------------------
# Overall monthly Actual vs Seasonal Naive forecast
# --------------------------------------------------

# Aggregate all vehicle models into one monthly total.
# This provides a high-level view of company-wide demand
# and forecast performance.
overall_monthly = (
    df.groupby("month")
    .agg(
        actual_demand=(
            "demand_units",
            "sum"
        ),
        seasonal_naive_forecast=(
            "seasonal_naive_forecast",
            "sum"
        ),
    )
    .reset_index()
)

print(
    "\nOverall Monthly Forecast:"
)

print(
    overall_monthly
    .round(2)
    .to_string(index=False)
)

plt.figure(
    figsize=(10, 6)
)

# Plot total actual demand across all vehicle models.
plt.plot(
    overall_monthly["month"],
    overall_monthly["actual_demand"],
    marker="o",
    label="Actual Demand"
)

# Plot total Seasonal Naive forecast.
plt.plot(
    overall_monthly["month"],
    overall_monthly["seasonal_naive_forecast"],
    marker="o",
    label="Seasonal Naive Forecast"
)

plt.title(
    "Overall Monthly Demand vs Seasonal Naive Forecast"
)

plt.xlabel(
    "Month"
)

plt.ylabel(
    "Demand Units"
)

plt.legend()

plt.grid(
    alpha=0.3
)

plt.xticks(
    rotation=45
)

plt.tight_layout()


overall_output_path = (
    f"{output_dir}/"
    "overall_actual_vs_forecast.png"
)

plt.savefig(
    overall_output_path,
    dpi=150,
    bbox_inches="tight"
)

plt.close()


print(
    "\nForecast model comparison:"
)

print(
    comparison_df
    .round(2)
    .to_string(index=False)
)

print(
    "Saved:",
    overall_output_path
)

print(
    "\nForecast visualizations complete."
)