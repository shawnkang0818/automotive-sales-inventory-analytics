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
# Build monthly demand time series by vehicle model
# --------------------------------------------------

monthly_demand = (
    df.groupby(
        ["month", "vehicle_model"]
    )["demand_units"]
    .sum()
    .reset_index()
)

# --------------------------------------------------
# Train/test split
# --------------------------------------------------

train_end_date = pd.Timestamp("2026-06-01")

train_data = monthly_demand[
    monthly_demand["month"] <= train_end_date
].copy()

test_data = monthly_demand[
    monthly_demand["month"] > train_end_date
].copy()

# --------------------------------------------------
# Seasonal naive forecast
# --------------------------------------------------

seasonal_naive = test_data.copy()

seasonal_naive["previous_year_month"] = (
    seasonal_naive["month"]
    - pd.DateOffset(years=1)
)

historical_demand = monthly_demand[
    [
        "month",
        "vehicle_model",
        "demand_units",
    ]
].copy()

historical_demand = historical_demand.rename(
    columns={
        "month": "previous_year_month",
        "demand_units": "seasonal_naive_forecast",
    }
)

seasonal_naive = seasonal_naive.merge(
    historical_demand,
    on=[
        "previous_year_month",
        "vehicle_model",
    ],
    how="left"
)

# --------------------------------------------------
# Seasonal naive forecast errors
# --------------------------------------------------

# Signed error:
# Positive = actual demand was higher than forecast.
# Negative = forecast was higher than actual demand.
seasonal_naive["forecast_error_units"] = (
    seasonal_naive["demand_units"]
    - seasonal_naive["seasonal_naive_forecast"]
)

# Absolute error removes the direction of the error.
seasonal_naive["absolute_error_units"] = (
    seasonal_naive["forecast_error_units"].abs()
)

# Absolute percentage error for each observation.
seasonal_naive["absolute_percentage_error"] = (
    seasonal_naive["absolute_error_units"]
    / seasonal_naive["demand_units"]
    * 100
)

# --------------------------------------------------
# Overall seasonal naive evaluation
# --------------------------------------------------

seasonal_naive_mae = (
    seasonal_naive["absolute_error_units"].mean()
)

seasonal_naive_mape = (
    seasonal_naive["absolute_percentage_error"].mean()
)

# --------------------------------------------------
# Seasonal naive evaluation by vehicle model
# --------------------------------------------------

seasonal_naive_by_model = (
    seasonal_naive.groupby("vehicle_model")
    .agg(
        mae=(
            "absolute_error_units",
            "mean"
        ),
        mape=(
            "absolute_percentage_error",
            "mean"
        ),
    )
    .reset_index()
)

# --------------------------------------------------
# 3-month moving average forecast
# --------------------------------------------------

moving_average = monthly_demand.copy()

# Sort each vehicle model chronologically before
# calculating rolling historical averages.
moving_average = moving_average.sort_values(
    ["vehicle_model", "month"]
)

moving_average["moving_average_3m_forecast"] = (
    moving_average
    .groupby("vehicle_model")["demand_units"]
    .transform(
        lambda series: (
            series
            .shift(1)
            .rolling(window=3)
            .mean()
        )
    )
)

moving_average_test = moving_average[
    moving_average["month"] > train_end_date
].copy()

# --------------------------------------------------
# 3-month moving average forecast errors
# --------------------------------------------------

# Signed error:
# Positive = actual demand was higher than forecast.
# Negative = forecast was higher than actual demand.
moving_average_test["forecast_error_units"] = (
    moving_average_test["demand_units"]
    - moving_average_test["moving_average_3m_forecast"]
)

# Absolute error measures error magnitude regardless of direction.
moving_average_test["absolute_error_units"] = (
    moving_average_test["forecast_error_units"].abs()
)

# Absolute percentage error makes errors comparable
# across vehicle models with different demand volumes.
moving_average_test["absolute_percentage_error"] = (
    moving_average_test["absolute_error_units"]
    / moving_average_test["demand_units"]
    * 100
)

# --------------------------------------------------
# Overall 3-month moving average evaluation
# --------------------------------------------------

moving_average_mae = (
    moving_average_test["absolute_error_units"].mean()
)

moving_average_mape = (
    moving_average_test["absolute_percentage_error"].mean()
)

# --------------------------------------------------
# 3-month moving average evaluation by vehicle model
# --------------------------------------------------

moving_average_by_model = (
    moving_average_test.groupby("vehicle_model")
    .agg(
        mae=(
            "absolute_error_units",
            "mean"
        ),
        mape=(
            "absolute_percentage_error",
            "mean"
        ),
    )
    .reset_index()
)

# --------------------------------------------------
# Forecast model comparison
# --------------------------------------------------

model_comparison = pd.DataFrame({
    "model": [
        "Seasonal Naive",
        "3-Month Moving Average",
    ],
    "mae": [
        seasonal_naive_mae,
        moving_average_mae,
    ],
    "mape": [
        seasonal_naive_mape,
        moving_average_mape,
    ],
})

seasonal_naive_by_model_compare = (
    seasonal_naive_by_model.rename(
        columns={
            "mae": "seasonal_naive_mae",
            "mape": "seasonal_naive_mape",
        }
    )
)

moving_average_by_model_compare = (
    moving_average_by_model.rename(
        columns={
            "mae": "moving_average_mae",
            "mape": "moving_average_mape",
        }
    )
)

model_comparison_by_vehicle = (
    seasonal_naive_by_model_compare.merge(
        moving_average_by_model_compare,
        on="vehicle_model",
        how="inner"
    )
)

model_comparison_by_vehicle["better_model"] = (
    model_comparison_by_vehicle.apply(
        lambda row: (
            "Seasonal Naive"
            if row["seasonal_naive_mape"]
            < row["moving_average_mape"]
            else "3-Month Moving Average"
        ),
        axis=1
    )
)

# --------------------------------------------------
# Output
# --------------------------------------------------
print(
    "\nMonthly Demand Time Series:"
)

print(
    monthly_demand
    .head(12)
    .to_string(index=False)
)

print(monthly_demand.shape)

print(
    "\nTrain Period:",
    train_data["month"].min(),
    "to",
    train_data["month"].max()
)

print(
    "Test Period:",
    test_data["month"].min(),
    "to",
    test_data["month"].max()
)

print(
    "Train Shape:",
    train_data.shape
)

print(
    "Test Shape:",
    test_data.shape
)

print(
    "\nSeasonal Naive Forecast:"
)

print(
    seasonal_naive[
        [
            "month",
            "vehicle_model",
            "demand_units",
            "seasonal_naive_forecast",
        ]
    ]
    .head(12)
    .to_string(index=False)
)

print(
    "\nSeasonal Naive Evaluation:"
)

print(
    "MAE:",
    round(seasonal_naive_mae, 2)
)

print(
    "MAPE:",
    round(seasonal_naive_mape, 2),
    "%"
)

print(
    "\nSeasonal Naive Evaluation by Vehicle Model:"
)

print(
    seasonal_naive_by_model
    .round(2)
    .to_string(index=False)
)

print(
    "\n3-Month Moving Average Forecast:"
)

print(
    moving_average_test[
        [
            "month",
            "vehicle_model",
            "demand_units",
            "moving_average_3m_forecast",
        ]
    ]
    .head(12)
    .round(2)
    .to_string(index=False)
)

# --------------------------------------------------
# Verify the July 2026 EV moving-average forecast
# --------------------------------------------------

ev_history_check = monthly_demand[
    (monthly_demand["vehicle_model"] == "EV")
    & (
        monthly_demand["month"].between(
            "2026-04-01",
            "2026-07-01",
        )
    )
]

print(
    "\nEV History Check:"
)

print(
    ev_history_check.to_string(index=False)
)

print(
    "\n3-Month Moving Average Evaluation:"
)

print(
    "MAE:",
    round(moving_average_mae, 2)
)

print(
    "MAPE:",
    round(moving_average_mape, 2),
    "%"
)

print(
    "\n3-Month Moving Average Evaluation by Vehicle Model:"
)

print(
    moving_average_by_model
    .round(2)
    .to_string(index=False)
)

print(
    "\nForecast Model Comparison:"
)

print(
    model_comparison
    .round(2)
    .to_string(index=False)
)

print(
    "\nForecast Model Comparison by Vehicle Model:"
)

print(
    model_comparison_by_vehicle
    .round(2)
    .to_string(index=False)
)

# --------------------------------------------------
# Build selected forecast by vehicle model
# --------------------------------------------------

forecast_candidates = (
    seasonal_naive[
        [
            "month",
            "vehicle_model",
            "demand_units",
            "seasonal_naive_forecast",
        ]
    ]
    .merge(
        moving_average_test[
            [
                "month",
                "vehicle_model",
                "moving_average_3m_forecast",
            ]
        ],
        on=[
            "month",
            "vehicle_model",
        ],
        how="inner"
    )
)

forecast_candidates = forecast_candidates.merge(
    model_comparison_by_vehicle[
        [
            "vehicle_model",
            "better_model",
        ]
    ],
    on="vehicle_model",
    how="left"
)

def select_forecast(row):
    """
    Select the forecast produced by the better-performing
    baseline model for each vehicle model.
    """

    if row["better_model"] == "Seasonal Naive":
        return row["seasonal_naive_forecast"]

    return row["moving_average_3m_forecast"]

forecast_candidates["selected_forecast"] = (
    forecast_candidates.apply(
        select_forecast,
        axis=1
    )
)

# --------------------------------------------------
# Selected forecast backtest errors
# --------------------------------------------------

forecast_candidates["selected_forecast_error_units"] = (
    forecast_candidates["demand_units"]
    - forecast_candidates["selected_forecast"]
)

forecast_candidates["selected_absolute_error_units"] = (
    forecast_candidates[
        "selected_forecast_error_units"
    ].abs()
)

forecast_candidates["selected_absolute_percentage_error"] = (
    forecast_candidates["selected_absolute_error_units"]
    / forecast_candidates["demand_units"]
    * 100
)

selected_forecast_mae = (
    forecast_candidates[
        "selected_absolute_error_units"
    ].mean()
)

selected_forecast_mape = (
    forecast_candidates[
        "selected_absolute_percentage_error"
    ].mean()
)

print(
    "\nSelected Forecast Backtest:"
)

print(
    forecast_candidates[
        [
            "month",
            "vehicle_model",
            "demand_units",
            "better_model",
            "selected_forecast",
        ]
    ]
    .round(2)
    .to_string(index=False)
)

print(
    "\nSelected Forecast Backtest Evaluation:"
)

print(
    "MAE:",
    round(selected_forecast_mae, 2)
)

print(
    "MAPE:",
    round(selected_forecast_mape, 2),
    "%"
)

# --------------------------------------------------
# Rolling backtest setup
# --------------------------------------------------

# Start from the complete monthly demand history.
# A rolling backtest simulates forecasting each month
# using only information that would have been available
# before that month.
rolling_backtest = monthly_demand.copy()

# Rolling and shifting operations depend on row order,
# so each vehicle model must be sorted chronologically.
rolling_backtest = rolling_backtest.sort_values(
    ["vehicle_model", "month"]
)


# --------------------------------------------------
# Rolling Seasonal Naive forecast
# --------------------------------------------------

# Forecast each month using demand from the same month
# one year earlier.
#
# Example:
# 2026-07 forecast <- 2025-07 actual demand
rolling_backtest["seasonal_naive_forecast"] = (
    rolling_backtest
    .groupby("vehicle_model")["demand_units"]
    .shift(12)
)


# --------------------------------------------------
# Rolling 3-month moving average forecast
# --------------------------------------------------

# Forecast each month using the average demand from
# the previous three months.
#
# shift(1) is critical because it prevents the current
# month's actual demand from leaking into its own forecast.
rolling_backtest["moving_average_3m_forecast"] = (
    rolling_backtest
    .groupby("vehicle_model")["demand_units"]
    .transform(
        lambda series: (
            series
            .shift(1)
            .rolling(window=3)
            .mean()
        )
    )
)


# --------------------------------------------------
# Define rolling backtest period
# --------------------------------------------------

# Start in January 2026 because Seasonal Naive requires
# 12 months of historical demand.
rolling_backtest_test = rolling_backtest[
    rolling_backtest["month"] >= pd.Timestamp("2026-01-01")
].copy()

# Keep only observations where both forecasting methods
# have enough historical data to generate a forecast.
rolling_backtest_test = rolling_backtest_test.dropna(
    subset=[
        "seasonal_naive_forecast",
        "moving_average_3m_forecast",
    ]
)


# --------------------------------------------------
# Rolling backtest errors: Seasonal Naive
# --------------------------------------------------

# Signed error:
# Positive = actual demand exceeded the forecast.
# Negative = forecast exceeded actual demand.
rolling_backtest_test["seasonal_naive_error_units"] = (
    rolling_backtest_test["demand_units"]
    - rolling_backtest_test["seasonal_naive_forecast"]
)

# Absolute error is used to calculate MAE.
rolling_backtest_test["seasonal_naive_absolute_error"] = (
    rolling_backtest_test[
        "seasonal_naive_error_units"
    ].abs()
)

# Absolute Percentage Error (APE) is used to calculate MAPE.
rolling_backtest_test["seasonal_naive_ape"] = (
    rolling_backtest_test[
        "seasonal_naive_absolute_error"
    ]
    / rolling_backtest_test["demand_units"]
    * 100
)


# --------------------------------------------------
# Rolling backtest errors: 3-Month Moving Average
# --------------------------------------------------

rolling_backtest_test["moving_average_error_units"] = (
    rolling_backtest_test["demand_units"]
    - rolling_backtest_test["moving_average_3m_forecast"]
)

rolling_backtest_test["moving_average_absolute_error"] = (
    rolling_backtest_test[
        "moving_average_error_units"
    ].abs()
)

rolling_backtest_test["moving_average_ape"] = (
    rolling_backtest_test[
        "moving_average_absolute_error"
    ]
    / rolling_backtest_test["demand_units"]
    * 100
)


# --------------------------------------------------
# Overall rolling backtest evaluation
# --------------------------------------------------

rolling_seasonal_naive_mae = (
    rolling_backtest_test[
        "seasonal_naive_absolute_error"
    ].mean()
)

rolling_seasonal_naive_mape = (
    rolling_backtest_test[
        "seasonal_naive_ape"
    ].mean()
)

rolling_moving_average_mae = (
    rolling_backtest_test[
        "moving_average_absolute_error"
    ].mean()
)

rolling_moving_average_mape = (
    rolling_backtest_test[
        "moving_average_ape"
    ].mean()
)


# --------------------------------------------------
# Overall rolling model comparison
# --------------------------------------------------

rolling_model_comparison = pd.DataFrame({
    "model": [
        "Seasonal Naive",
        "3-Month Moving Average",
    ],
    "mae": [
        rolling_seasonal_naive_mae,
        rolling_moving_average_mae,
    ],
    "mape": [
        rolling_seasonal_naive_mape,
        rolling_moving_average_mape,
    ],
})


# --------------------------------------------------
# Rolling backtest evaluation by vehicle model
# --------------------------------------------------

# Aggregate forecast accuracy separately for each
# vehicle model across the full rolling test period.
rolling_comparison_by_vehicle = (
    rolling_backtest_test.groupby("vehicle_model")
    .agg(
        seasonal_naive_mae=(
            "seasonal_naive_absolute_error",
            "mean"
        ),
        seasonal_naive_mape=(
            "seasonal_naive_ape",
            "mean"
        ),
        moving_average_mae=(
            "moving_average_absolute_error",
            "mean"
        ),
        moving_average_mape=(
            "moving_average_ape",
            "mean"
        ),
    )
    .reset_index()
)


# --------------------------------------------------
# Select better model by vehicle
# --------------------------------------------------

# Choose the model with the lower rolling-backtest MAPE
# for each vehicle model.
rolling_comparison_by_vehicle["better_model"] = (
    rolling_comparison_by_vehicle.apply(
        lambda row: (
            "Seasonal Naive"
            if row["seasonal_naive_mape"]
            < row["moving_average_mape"]
            else "3-Month Moving Average"
        ),
        axis=1
    )
)


# --------------------------------------------------
# Select overall rolling winner
# --------------------------------------------------

# Sort models by MAPE from lowest to highest.
# iloc[0] selects the first row, which is the
# best-performing model under this evaluation.
rolling_best_model = (
    rolling_model_comparison
    .sort_values("mape")
    .iloc[0]["model"]
)


# --------------------------------------------------
# Rolling backtest output
# --------------------------------------------------

print(
    "\nRolling Backtest Forecasts:"
)

print(
    rolling_backtest_test[
        [
            "month",
            "vehicle_model",
            "demand_units",
            "seasonal_naive_forecast",
            "moving_average_3m_forecast",
        ]
    ]
    .head(16)
    .round(2)
    .to_string(index=False)
)

print(
    "\nRolling Backtest Shape:",
    rolling_backtest_test.shape
)


print(
    "\nRolling Backtest Model Comparison:"
)

print(
    rolling_model_comparison
    .round(2)
    .to_string(index=False)
)


print(
    "\nRolling Backtest Comparison by Vehicle Model:"
)

print(
    rolling_comparison_by_vehicle
    .round(2)
    .to_string(index=False)
)


print(
    "\nSelected Rolling Backtest Model:",
    rolling_best_model
)


# --------------------------------------------------
# Save forecasting outputs
# --------------------------------------------------

# Save detailed month-level rolling forecasts and
# forecast errors for later visualization/dashboard use.
rolling_backtest_test.to_csv(
    "data/processed/forecast_rolling_backtest.csv",
    index=False
)

# Save vehicle-level model comparison and winner.
rolling_comparison_by_vehicle.to_csv(
    "data/processed/forecast_model_comparison.csv",
    index=False
)

print(
    "\nSaved forecasting outputs to data/processed/"
)