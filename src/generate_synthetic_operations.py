import pandas as pd
import numpy as np


# --------------------------------------------------
# Reproducibility
# --------------------------------------------------

rng_forecast = np.random.default_rng(42)
rng_demand = np.random.default_rng(43)
rng_production = np.random.default_rng(44)
rng_promotion = np.random.default_rng(45)

# --------------------------------------------------
# Simulation dimensions
# --------------------------------------------------

months = pd.date_range(
    start="2025-01-01",
    periods=24,
    freq="MS"
)

dealers = {
    "Northeast": ["NE_D01", "NE_D02"],
    "South": ["SO_D01", "SO_D02"],
    "Midwest": ["MW_D01", "MW_D02"],
    "West": ["WE_D01", "WE_D02"],
}

vehicle_models = [
    "SUV",
    "Sedan",
    "EV",
    "Pickup",
]


# --------------------------------------------------
# Base demand assumptions
# --------------------------------------------------

base_demand = {
    "SUV": 120,
    "Sedan": 75,
    "EV": 85,
    "Pickup": 100,
}

base_price = {
    "SUV": 42000,
    "Sedan": 32000,
    "EV": 48000,
    "Pickup": 46000,
}

promotion_response_factor = 0.8

# --------------------------------------------------
# Regional demand effects
# --------------------------------------------------

region_effect = {
    "Northeast": {
        "SUV": 1.00,
        "Sedan": 1.05,
        "EV": 1.10,
        "Pickup": 0.80,
    },
    "South": {
        "SUV": 1.05,
        "Sedan": 0.90,
        "EV": 0.85,
        "Pickup": 1.20,
    },
    "Midwest": {
        "SUV": 1.00,
        "Sedan": 0.90,
        "EV": 0.80,
        "Pickup": 1.25,
    },
    "West": {
        "SUV": 1.05,
        "Sedan": 0.95,
        "EV": 1.25,
        "Pickup": 0.90,
    },
}


# --------------------------------------------------
# Monthly seasonality assumptions
# --------------------------------------------------

seasonality = {
    1: 0.90,
    2: 0.92,
    3: 1.00,
    4: 1.03,
    5: 1.05,
    6: 1.08,
    7: 1.05,
    8: 1.03,
    9: 1.00,
    10: 0.98,
    11: 1.02,
    12: 1.10,
}

# --------------------------------------------------
# Initial inventory and promotion state
# --------------------------------------------------

inventory_state = {}
promotion_state = {}

for region, dealer_list in dealers.items():
    for dealer_id in dealer_list:
        for vehicle_model in vehicle_models:

            inventory_state[
                (dealer_id, vehicle_model)
            ] = round(
                base_demand[vehicle_model] * 0.75
            )

            promotion_state[
                (dealer_id, vehicle_model)
            ] = False
# --------------------------------------------------
# Generate monthly dealer/model operations
# --------------------------------------------------

rows = []

for month in months:

    month_number = month.month

    for region, dealer_list in dealers.items():

        for dealer_id in dealer_list:

            for vehicle_model in vehicle_models:

                # ----------------------------------
                # Promotion
                # ----------------------------------

                promotion_flag = promotion_state[
                    (dealer_id, vehicle_model)
                ]

                if promotion_flag:
                    promotion_discount_pct = rng_promotion.uniform(
                        5,
                        12
                    )
                else:
                    promotion_discount_pct = 0.0

                promotion_lift = (
                    1.0
                    + (
                        promotion_discount_pct
                        / 100
                        * promotion_response_factor
                    )
                )

                # ----------------------------------
                # Pricing
                # ----------------------------------

                list_price = base_price[
                    vehicle_model
                ]

                effective_price = (
                    list_price
                    * (1 - promotion_discount_pct / 100)
                )                

                # ----------------------------------
                # Expected demand
                # ----------------------------------
                
                baseline_expected_demand = (
                    base_demand[vehicle_model]
                    * region_effect[region][vehicle_model]
                    * seasonality[month_number]
                )

                expected_demand = (
                    baseline_expected_demand
                    * promotion_lift
                )

                # ----------------------------------
                # Forecast
                # ----------------------------------

                forecast_variation = rng_forecast.normal(
                    loc=1.0,
                    scale=0.06
                )

                forecast_units = round(
                    expected_demand * forecast_variation
                )

                forecast_units = max(
                    forecast_units,
                    0
                )

                # ----------------------------------
                # Customer demand
                # ----------------------------------

                demand_variation = rng_demand.normal(
                    loc=1.0,
                    scale=0.08
                )

                demand_units = round(
                    expected_demand * demand_variation
                )

                demand_units = max(
                    demand_units,
                    0
                )

                # ----------------------------------
                # Beginning inventory
                # ----------------------------------

                beginning_inventory = inventory_state[
                    (dealer_id, vehicle_model)
                ]

                # ----------------------------------
                # Production / allocation
                # ----------------------------------

                production_variation = rng_production.normal(
                    loc=0.98,
                    scale=0.10
                )

                production_units = round(
                    forecast_units * production_variation
                )

                production_units = max(
                    production_units,
                    0
                )

                # ----------------------------------
                # Available inventory
                # ----------------------------------

                available_units = (
                    beginning_inventory
                    + production_units
                )

                # ----------------------------------
                # Actual sales
                # ----------------------------------

                sales_units = min(
                    demand_units,
                    available_units
                )

                # ----------------------------------
                # Lost sales
                # ----------------------------------

                lost_sales_units = (
                    demand_units
                    - sales_units
                )

                # ----------------------------------
                # Ending inventory
                # ----------------------------------

                ending_inventory = (
                    available_units
                    - sales_units
                )

                inventory_risk_ratio = (
                    ending_inventory
                    / max(demand_units, 1)
                )

                next_month_promotion = (
                    inventory_risk_ratio > 1.0
                    and sales_units < forecast_units
                )

                # Carry inventory into next month
                inventory_state[
                    (dealer_id, vehicle_model)
                ] = ending_inventory

                promotion_state[
                    (dealer_id, vehicle_model)
                ] = next_month_promotion

                # ----------------------------------
                # Store row
                # ----------------------------------

                rows.append({
                    "month": month,
                    "region": region,
                    "dealer_id": dealer_id,
                    "vehicle_model": vehicle_model,
                    "promotion_flag": promotion_flag,
                    "promotion_discount_pct": round(
                        promotion_discount_pct,
                        2
                    ),
                    "promotion_lift": round(
                        promotion_lift,
                        4
                    ),
                    "list_price": list_price,
                    "effective_price": round(
                        effective_price,
                        2
                    ),
                    "baseline_expected_demand": round(
                        baseline_expected_demand,
                        2
                    ),
                    "forecast_units": forecast_units,
                    "demand_units": demand_units,
                    "production_units": production_units,
                    "beginning_inventory_units": beginning_inventory,
                    "sales_units": sales_units,
                    "lost_sales_units": lost_sales_units,
                    "ending_inventory_units": ending_inventory,
                    
                })


# --------------------------------------------------
# Create DataFrame
# --------------------------------------------------

synthetic = pd.DataFrame(rows)


# --------------------------------------------------
# Forecast KPIs
# --------------------------------------------------

synthetic["forecast_error_units"] = (
    synthetic["demand_units"]
    - synthetic["forecast_units"]
)

synthetic["forecast_error_pct"] = (
    synthetic["forecast_error_units"]
    / synthetic["forecast_units"].replace(0, np.nan)
    * 100
)

synthetic["absolute_forecast_error_pct"] = (
    synthetic["forecast_error_pct"].abs()
)


# --------------------------------------------------
# Inventory KPI
# --------------------------------------------------

synthetic["inventory_to_sales_ratio"] = (
    synthetic["ending_inventory_units"]
    / synthetic["sales_units"].replace(0, np.nan)
)

# --------------------------------------------------
# Promotion KPI
# --------------------------------------------------

synthetic["promotion_expected_lift_units"] = (
    synthetic["baseline_expected_demand"]
    * (
        synthetic["promotion_lift"]
        - 1
    )
)

# --------------------------------------------------
# Revenue KPI
# --------------------------------------------------

synthetic["revenue"] = (
    synthetic["sales_units"]
    * synthetic["effective_price"]
)

synthetic["list_price_revenue_on_actual_sales"] = (
    synthetic["sales_units"]
    * synthetic["list_price"]
)

synthetic["discount_revenue_concession"] = (
    synthetic["list_price_revenue_on_actual_sales"]
    - synthetic["revenue"]
)

synthetic["discount_revenue_concession"] = (
    synthetic["list_price_revenue_on_actual_sales"]
    - synthetic["revenue"]
)

# --------------------------------------------------
# Promotion revenue trade-off KPI
# --------------------------------------------------

synthetic["baseline_expected_revenue"] = (
    synthetic["baseline_expected_demand"]
    * synthetic["list_price"]
)

synthetic["promoted_expected_demand"] = (
    synthetic["baseline_expected_demand"]
    * synthetic["promotion_lift"]
)

synthetic["promoted_expected_revenue"] = (
    synthetic["promoted_expected_demand"]
    * synthetic["effective_price"]
)

synthetic["expected_revenue_tradeoff"] = (
    synthetic["promoted_expected_revenue"]
    - synthetic["baseline_expected_revenue"]
)

synthetic["break_even_demand_lift_pct"] = (
    (
        synthetic["list_price"]
        / synthetic["effective_price"]
        - 1
    )
    * 100
)

synthetic["assumed_demand_lift_pct"] = (
    (
        synthetic["promotion_lift"]
        - 1
    )
    * 100
)

# --------------------------------------------------
# Summary statistics
# --------------------------------------------------

mape = synthetic[
    "absolute_forecast_error_pct"
].mean()

print(
    "\nMean Absolute Percentage Error:",
    round(mape, 2),
    "%"
)

print(
    "\nShape:",
    synthetic.shape
)

print(
    "\nTotal Lost Sales:",
    synthetic["lost_sales_units"].sum()
)

print(
    "\nEnding Inventory Summary:"
)

print(
    synthetic["ending_inventory_units"]
    .describe()
)

print(
    "\nAverage Ending Inventory by Vehicle Model:"
)

print(
    synthetic
    .groupby("vehicle_model")[
        "ending_inventory_units"
    ]
    .mean()
    .round(1)
)

print(
    "\nAverage Inventory-to-Sales Ratio by Vehicle Model:"
)

print(
    synthetic
    .groupby("vehicle_model")[
        "inventory_to_sales_ratio"
    ]
    .mean()
    .round(2)
)

print(
    "\nMAPE by Vehicle Model:"
)

print(
    synthetic
    .groupby("vehicle_model")[
        "absolute_forecast_error_pct"
    ]
    .mean()
    .round(2)
)

print(
    "\nMAPE by Region:"
)

print(
    synthetic
    .groupby("region")[
        "absolute_forecast_error_pct"
    ]
    .mean()
    .round(2)
)

stockout_rows = (
    synthetic["lost_sales_units"] > 0
).sum()

stockout_rate = (
    (synthetic["lost_sales_units"] > 0).mean()
    * 100
)

print(
    "\nRows with Lost Sales:",
    stockout_rows
)

print(
    "Stockout Rate:",
    round(stockout_rate, 2),
    "%"
)

promotion_summary = (
    synthetic
    .groupby("promotion_flag")["sales_units"]
    .mean()
)

print("\nAverage Sales by Promotion Status:")
print(promotion_summary)

print(
    "\nPromotion Rows:",
    synthetic["promotion_flag"].sum()
)

promotion_rate = (
    synthetic["promotion_flag"].mean() * 100
)

print(
    "Promotion Rate:",
    round(promotion_rate, 2),
    "%"
)


# --------------------------------------------------
# 13. Preview
# --------------------------------------------------

preview_columns = [
    "month",
    "region",
    "dealer_id",
    "vehicle_model",
    "forecast_units",
    "demand_units",
    "production_units",
    "beginning_inventory_units",
    "sales_units",
    "lost_sales_units",
    "ending_inventory_units",
]

print(
    "\nSample Operational Data:"
)

print(
    synthetic[preview_columns]
    .head(20)
    .to_string(index=False)
)

print(
    "\nPromotion Sample:"
)

print(
    synthetic[
        [
            "month",
            "region",
            "dealer_id",
            "vehicle_model",
            "promotion_flag",
            "promotion_discount_pct",
            "baseline_expected_demand",
            "demand_units",
            "promotion_expected_lift_units",
        ]
    ]
    .loc[synthetic["promotion_flag"]]
    .head(15)
    .round(2)
    .to_string(index=False)
)

print(
    "\nAverage Promotion Discount:",
    round(
        synthetic.loc[
            synthetic["promotion_flag"],
            "promotion_discount_pct"
        ].mean(),
        2
    ),
    "%"
)

print(
    "\nAverage Revenue by Promotion Status:"
)

print(
    synthetic
    .groupby("promotion_flag")["revenue"]
    .mean()
    .round(2)
)

print(
    "\nTotal Discount Revenue Concession:",
    round(
        synthetic["discount_revenue_concession"].sum(),
        2
    )
)

print(
    "\nRevenue by Vehicle Model:"
)

print(
    synthetic
    .groupby("vehicle_model")["revenue"]
    .sum()
    .round(2)
)

print(
    "\nPromotion Discount and Expected Lift Sample:"
)

print(
    synthetic.loc[
        synthetic["promotion_flag"],
        [
            "promotion_discount_pct",
            "promotion_lift",
            "baseline_expected_demand",
            "promotion_expected_lift_units",
        ]
    ]
    .head(15)
    .round(2)
    .to_string(index=False)
)

promotion_tradeoff = synthetic.loc[
    synthetic["promotion_flag"]
].copy()

print(
    "\nPromotion Revenue Trade-off Summary:"
)

print(
    promotion_tradeoff[
        [
            "promotion_discount_pct",
            "assumed_demand_lift_pct",
            "break_even_demand_lift_pct",
            "baseline_expected_revenue",
            "promoted_expected_revenue",
            "expected_revenue_tradeoff",
        ]
    ]
    .head(15)
    .round(2)
    .to_string(index=False)
)

print(
    "\nAverage Expected Revenue Trade-off per Promotion:"
)

print(
    round(
        promotion_tradeoff[
            "expected_revenue_tradeoff"
        ].mean(),
        2
    )
)

positive_tradeoff_rate = (
    (
        promotion_tradeoff[
            "expected_revenue_tradeoff"
        ] > 0
    ).mean()
    * 100
)

print(
    "\nRevenue-Positive Promotion Rate:",
    round(positive_tradeoff_rate, 2),
    "%"
)


# --------------------------------------------------
# Save dataset
# --------------------------------------------------

synthetic.to_csv(
    "data/synthetic/synthetic_operations.csv",
    index=False
)