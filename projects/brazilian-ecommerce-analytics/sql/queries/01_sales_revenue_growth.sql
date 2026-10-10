-- Business Query 1: Monthly Sales Revenue & Order Growth Analysis
-- Analyzes Gross Merchandise Value (GMV), order volume, AOV, and Month-over-Month (MoM) growth.

WITH monthly_sales AS (
    SELECT 
        SUBSTR(order_purchase_timestamp, 1, 7) AS order_year_month,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT customer_unique_id) AS active_customers,
        ROUND(SUM(items_value), 2) AS gross_merchandise_value,
        ROUND(SUM(total_freight), 2) AS total_freight_collected,
        ROUND(SUM(total_order_value), 2) AS total_gross_revenue,
        ROUND(AVG(total_order_value), 2) AS average_order_value
    FROM vw_orders_summary
    WHERE order_status = 'delivered'
      AND order_purchase_timestamp >= '2017-01-01' -- Exclude 2016 pilot launch noise
      AND order_purchase_timestamp < '2018-09-01'  -- Exclude incomplete final month
    GROUP BY SUBSTR(order_purchase_timestamp, 1, 7)
)
SELECT 
    order_year_month,
    total_orders,
    active_customers,
    gross_merchandise_value,
    total_freight_collected,
    total_gross_revenue,
    average_order_value,
    ROUND(
        (gross_merchandise_value - LAG(gross_merchandise_value, 1) OVER (ORDER BY order_year_month)) 
        * 100.0 / LAG(gross_merchandise_value, 1) OVER (ORDER BY order_year_month), 
        2
    ) AS gmv_mom_growth_pct,
    ROUND(
        (total_orders - LAG(total_orders, 1) OVER (ORDER BY order_year_month)) 
        * 100.0 / LAG(total_orders, 1) OVER (ORDER BY order_year_month), 
        2
    ) AS order_mom_growth_pct
FROM monthly_sales
ORDER BY order_year_month ASC;
