-- --------------------------------------------------
-- Production Planning Analysis
-- --------------------------------------------------
--
-- Business question:
-- Which region and vehicle-model combinations show
-- forecast error, production shortfall, or stockout risk?
--
-- Source grain:
-- one row = one month x one dealer x one vehicle model
--
-- Output grain:
-- one row = one region x one vehicle model
-- --------------------------------------------------


WITH planning_summary AS (

    SELECT
        region,
        vehicle_model,

        SUM(forecast_units) AS total_forecast_units,
        SUM(demand_units) AS total_demand_units,
        SUM(production_units) AS total_production_units,
        SUM(sales_units) AS total_sales_units,
        SUM(lost_sales_units) AS total_lost_sales_units,

        ROUND(
            AVG(ending_inventory_units),
            2
        ) AS avg_ending_inventory,

        -- Forecast minus demand.
        -- Negative means forecast underestimated demand.
        SUM(forecast_units)
        - SUM(demand_units)
        AS forecast_vs_demand_gap_units,

        ROUND(
            (
                SUM(forecast_units)
                - SUM(demand_units)
            ) * 100.0
            / NULLIF(SUM(demand_units), 0),
            2
        ) AS forecast_vs_demand_gap_pct,

        -- Production minus forecast.
        -- Negative means production came in below forecast.
        SUM(production_units)
        - SUM(forecast_units)
        AS production_vs_forecast_gap_units,

        ROUND(
            (
                SUM(production_units)
                - SUM(forecast_units)
            ) * 100.0
            / NULLIF(SUM(forecast_units), 0),
            2
        ) AS production_vs_forecast_gap_pct,

        -- Production minus demand.
        SUM(production_units)
        - SUM(demand_units)
        AS production_vs_demand_gap_units,

        ROUND(
            (
                SUM(production_units)
                - SUM(demand_units)
            ) * 100.0
            / NULLIF(SUM(demand_units), 0),
            2
        ) AS production_vs_demand_gap_pct,

        -- Demand fulfillment rate.
        ROUND(
            SUM(sales_units) * 100.0
            / NULLIF(SUM(demand_units), 0),
            2
        ) AS demand_fulfillment_rate_pct,

        -- Percent of dealer-month observations
        -- where lost sales occurred.
        ROUND(
            SUM(
                CASE
                    WHEN lost_sales_units > 0 THEN 1
                    ELSE 0
                END
            ) * 100.0
            / COUNT(*),
            2
        ) AS stockout_rate_pct

    FROM operations

    GROUP BY
        region,
        vehicle_model
)


SELECT
    region,
    vehicle_model,
    total_forecast_units,
    total_demand_units,
    total_production_units,
    total_sales_units,
    total_lost_sales_units,
    avg_ending_inventory,
    forecast_vs_demand_gap_units,
    forecast_vs_demand_gap_pct,
    production_vs_forecast_gap_units,
    production_vs_forecast_gap_pct,
    production_vs_demand_gap_units,
    production_vs_demand_gap_pct,
    demand_fulfillment_rate_pct,
    stockout_rate_pct,

    CASE
        WHEN forecast_vs_demand_gap_pct <= -1.0
         AND production_vs_forecast_gap_pct <= -2.0
         AND stockout_rate_pct >= 5.0
        THEN 'Mixed Issue'

        WHEN production_vs_forecast_gap_pct <= -2.0
         AND stockout_rate_pct >= 5.0
        THEN 'Production Issue'

        WHEN forecast_vs_demand_gap_pct <= -1.0
         AND stockout_rate_pct >= 5.0
        THEN 'Forecast Issue'

        WHEN stockout_rate_pct >= 5.0
        THEN 'Inventory / Timing Review'

        ELSE 'Balanced'
    END AS planning_diagnosis

FROM planning_summary

ORDER BY
    region,
    vehicle_model;