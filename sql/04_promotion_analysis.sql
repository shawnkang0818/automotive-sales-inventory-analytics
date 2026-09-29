-- --------------------------------------------------
-- Promotion Analysis
-- --------------------------------------------------
--
-- Business question:
-- Which vehicle models use promotions most often,
-- how large are the discounts, and what is the
-- expected revenue tradeoff under the synthetic
-- promotion assumptions?
--
-- Important:
-- expected_revenue_tradeoff is NOT profit or ROI.
-- This dataset does not include COGS, margin,
-- advertising cost, or campaign operating cost.
--
-- Source grain:
-- one row = one month x one dealer x one vehicle model
--
-- Output grain:
-- one row = one vehicle model
-- --------------------------------------------------


WITH promotion_summary AS (

    SELECT
        vehicle_model,

        COUNT(*) AS total_observations,

        SUM(
            CASE
                WHEN promotion_flag = 1 THEN 1
                ELSE 0
            END
        ) AS promotion_observations,

        ROUND(
            AVG(
                CASE
                    WHEN promotion_flag = 1 THEN 100.0
                    ELSE 0.0
                END
            ),
            2
        ) AS promotion_rate_pct,

        ROUND(
            AVG(
                CASE
                    WHEN promotion_flag = 1
                    THEN promotion_discount_pct
                END
            ),
            2
        ) AS avg_promotion_discount_pct,

        ROUND(
            AVG(
                CASE
                    WHEN promotion_flag = 1
                    THEN assumed_demand_lift_pct
                END
            ),
            2
        ) AS avg_assumed_demand_lift_pct,

        ROUND(
            AVG(
                CASE
                    WHEN promotion_flag = 1
                    THEN break_even_demand_lift_pct
                END
            ),
            2
        ) AS avg_break_even_demand_lift_pct,

        ROUND(
            AVG(
                CASE
                    WHEN promotion_flag = 1
                    THEN expected_revenue_tradeoff
                END
            ),
            2
        ) AS avg_expected_revenue_tradeoff,

        SUM(
            CASE
                WHEN promotion_flag = 1
                 AND expected_revenue_tradeoff > 0
                THEN 1
                ELSE 0
            END
        ) AS revenue_positive_promotions,

        ROUND(
            AVG(
                CASE
                    WHEN promotion_flag = 1 THEN
                        CASE
                            WHEN expected_revenue_tradeoff > 0
                            THEN 100.0
                            ELSE 0.0
                        END
                END
            ),
            2
        ) AS revenue_positive_promotion_rate_pct

    FROM operations

    GROUP BY
        vehicle_model
)


SELECT
    vehicle_model,
    total_observations,
    promotion_observations,
    promotion_rate_pct,
    avg_promotion_discount_pct,
    avg_assumed_demand_lift_pct,
    avg_break_even_demand_lift_pct,
    avg_expected_revenue_tradeoff,
    revenue_positive_promotions,
    revenue_positive_promotion_rate_pct,

    CASE
        WHEN avg_expected_revenue_tradeoff > 0
        THEN 'Expected Revenue Positive'
        ELSE 'Expected Revenue Negative'
    END AS promotion_revenue_assessment

FROM promotion_summary

ORDER BY
    promotion_rate_pct DESC;