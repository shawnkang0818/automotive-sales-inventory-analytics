-- --------------------------------------------------
-- Inventory Risk Analysis
-- --------------------------------------------------
--
-- Business question:
-- Which dealer and vehicle combinations are carrying
-- relatively high inventory, and which combinations
-- may require inventory, allocation, or promotion review?
--
-- Source grain:
-- one row = one month x one dealer x one vehicle model
--
-- Output grain:
-- one row = one dealer x one vehicle model
-- --------------------------------------------------


WITH inventory_summary AS (

    SELECT
        dealer_id,
        region,
        vehicle_model,

        -- Total demand over the analysis period.
        SUM(demand_units) AS total_demand_units,

        -- Total actual sales.
        SUM(sales_units) AS total_sales_units,

        -- Average ending inventory.
        ROUND(
            AVG(ending_inventory_units),
            2
        ) AS avg_ending_inventory,

        -- Average inventory-to-sales ratio.
        ROUND(
            AVG(inventory_to_sales_ratio),
            2
        ) AS avg_inventory_to_sales_ratio,

        -- Total unmet demand.
        SUM(lost_sales_units) AS total_lost_sales_units,

        -- Demand fulfillment rate.
        ROUND(
            SUM(sales_units) * 100.0
            / NULLIF(SUM(demand_units), 0),
            2
        ) AS demand_fulfillment_rate_pct,

        -- Percent of monthly observations where
        -- demand could not be fully fulfilled.
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

        -- Percent of observations using promotion.
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

        -- Average promotion discount when promotion
        -- was actually active.
        ROUND(
            AVG(
                CASE
                    WHEN promotion_flag = 1
                    THEN promotion_discount_pct
                END
            ),
            2
        ) AS avg_promotion_discount_pct,

        -- Average expected revenue tradeoff for
        -- promoted observations only.
        ROUND(
            AVG(
                CASE
                    WHEN promotion_flag = 1
                    THEN expected_revenue_tradeoff
                END
            ),
            2
        ) AS avg_expected_revenue_tradeoff

    FROM operations

    GROUP BY
        dealer_id,
        region,
        vehicle_model
)


SELECT
    dealer_id,
    region,
    vehicle_model,
    total_demand_units,
    total_sales_units,
    avg_ending_inventory,
    avg_inventory_to_sales_ratio,
    total_lost_sales_units,
    demand_fulfillment_rate_pct,
    stockout_rate_pct,
    promotion_rate_pct,
    avg_promotion_discount_pct,
    avg_expected_revenue_tradeoff,

    -- Inventory review:
    -- high average inventory ratio without meaningful
    -- stockout pressure.
    CASE
        WHEN avg_inventory_to_sales_ratio >= 0.75
         AND stockout_rate_pct < 5
        THEN 'Yes'
        ELSE 'No'
    END AS inventory_review_flag,

    -- Supply review:
    -- meaningful stockout activity or weaker fulfillment.
    CASE
        WHEN stockout_rate_pct >= 5
          OR demand_fulfillment_rate_pct < 99.5
        THEN 'Yes'
        ELSE 'No'
    END AS supply_review_flag,

    -- Mixed condition:
    -- inventory appears elevated but stockouts also occur.
    -- This can suggest timing or allocation mismatch rather
    -- than a simple "too much inventory" problem.
    CASE
        WHEN avg_inventory_to_sales_ratio >= 0.75
         AND stockout_rate_pct >= 5
        THEN 'Yes'
        ELSE 'No'
    END AS timing_allocation_review_flag

FROM inventory_summary

ORDER BY
    avg_inventory_to_sales_ratio DESC,
    stockout_rate_pct DESC;