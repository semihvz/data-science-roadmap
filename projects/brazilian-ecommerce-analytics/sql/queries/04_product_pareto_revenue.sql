-- Business Query 4: Product Category Pareto Analysis (80/20 Rule)
-- Evaluates cumulative revenue contribution across categories to identify key revenue drivers.

WITH category_totals AS (
    SELECT 
        category_name,
        items_sold,
        distinct_orders,
        total_revenue,
        avg_item_price,
        avg_freight,
        avg_review_score,
        SUM(total_revenue) OVER () AS overall_marketplace_revenue
    FROM vw_category_sales
),
pareto_calc AS (
    SELECT 
        category_name,
        items_sold,
        distinct_orders,
        total_revenue,
        avg_item_price,
        avg_freight,
        avg_review_score,
        ROUND(total_revenue * 100.0 / overall_marketplace_revenue, 2) AS category_share_pct,
        SUM(total_revenue) OVER (ORDER BY total_revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue,
        ROUND(
            SUM(total_revenue) OVER (ORDER BY total_revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 100.0 
            / overall_marketplace_revenue, 
            2
        ) AS cumulative_revenue_pct,
        ROW_NUMBER() OVER (ORDER BY total_revenue DESC) AS category_rank
    FROM category_totals
)
SELECT 
    category_rank,
    category_name,
    items_sold,
    total_revenue,
    category_share_pct,
    cumulative_revenue_pct,
    avg_item_price,
    avg_review_score,
    CASE 
        WHEN cumulative_revenue_pct <= 80.0 THEN 'Core 80% Revenue (Class A)'
        WHEN cumulative_revenue_pct <= 95.0 THEN 'Secondary 15% (Class B)'
        ELSE 'Long Tail 5% (Class C)'
    END AS abc_pareto_tier
FROM pareto_calc
ORDER BY total_revenue DESC;
