-- --------------------------------------------------
-- Dealer Performance Analysis
-- --------------------------------------------------
--
-- Business question:
-- Which dealers are generating the most demand and sales,
-- and which dealers show signs of supply or inventory pressure?
--
-- Source grain:
-- one row = one month x one dealer x one vehicle model
-- --------------------------------------------------


WITH dealer_summary AS (

    SELECT
        dealer_id,
        region,

        -- Total attempted demand.
        SUM(demand_units) AS total_demand_units,

        -- Total actual sales.
        SUM(sales_units) AS total_sales_units,

        -- Total units of unmet demand.
        SUM(lost_sales_units) AS total_lost_sales_units,

        -- Total dealer revenue.
        ROUND(
            SUM(revenue),
            2
        ) AS total_revenue,

        -- Average ending inventory across all
        -- dealer-model-month observations.
        ROUND(
            AVG(ending_inventory_units),
            2
        ) AS avg_ending_inventory,

        -- Average inventory-to-sales ratio.
        ROUND(
            AVG(inventory_to_sales_ratio),
            2
        ) AS avg_inventory_to_sales_ratio,

        -- Average absolute forecast error percentage.
        ROUND(
            AVG(absolute_forecast_error_pct),
            2
        ) AS forecast_mape,

        -- Demand fulfillment rate.
        ROUND(
            SUM(sales_units) * 100.0
            / NULLIF(SUM(demand_units), 0),
            2
        ) AS demand_fulfillment_rate_pct,

        -- Stockout rate:
        -- percent of observations with lost sales.
        ROUND(
            SUM(
                CASE
                    WHEN lost_sales_units > 0 THEN 1
                    ELSE 0
                END
            ) * 100.0
            / COUNT(*),
            2
        ) AS stockout_rate_pct,

        -- Promotion rate:
        -- percent of observations using promotion.
        ROUND(
            SUM(
                CASE
                    WHEN promotion_flag = 1 THEN 1
                    ELSE 0
                END
            ) * 100.0
            / COUNT(*),
            2
        ) AS promotion_rate_pct,

        -- Total production volume.
        SUM(production_units) AS total_production_units,

        -- Production minus demand.
        SUM(production_units)
        - SUM(demand_units)
        AS production_demand_gap_units

    FROM operations

    GROUP BY
        dealer_id,
        region
)


SELECT
    dealer_id,
    region,
    total_demand_units,
    total_sales_units,
    total_lost_sales_units,
    total_revenue,
    avg_ending_inventory,
    avg_inventory_to_sales_ratio,
    forecast_mape,
    demand_fulfillment_rate_pct,
    stockout_rate_pct,
    promotion_rate_pct,
    total_production_units,
    production_demand_gap_units,

    -- Supply pressure:
    -- higher stockout activity or weaker fulfillment.
    CASE
        WHEN stockout_rate_pct >= 5
          OR demand_fulfillment_rate_pct < 99.5
        THEN 'Yes'
        ELSE 'No'
    END AS supply_pressure_flag,

    -- Inventory pressure:
    -- elevated average inventory-to-sales ratio
    -- without simultaneous supply pressure.
    CASE
        WHEN avg_inventory_to_sales_ratio >= 0.75
         AND stockout_rate_pct < 5
        THEN 'Yes'
        ELSE 'No'
    END AS inventory_pressure_flag,

    -- Forecast review:
    -- synthetic diagnostic threshold.
    CASE
        WHEN forecast_mape >= 9
        THEN 'Yes'
        ELSE 'No'
    END AS forecast_review_flag

FROM dealer_summary

ORDER BY
    total_demand_units DESC;