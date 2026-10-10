-- Business Query 6: Marketplace Seller Ecosystem & SLA Performance
-- Analyzes seller geographic concentration, fulfillment speed, volume, and customer ratings.

-- Part A: Top 20 Marketplace Sellers by Sales Volume
SELECT 
    s.seller_id,
    s.seller_city,
    s.seller_state,
    p.total_orders,
    p.total_items_sold,
    p.total_sales,
    p.avg_item_price,
    p.avg_review_score,
    ROUND(p.total_sales * 100.0 / (SELECT SUM(total_sales) FROM vw_seller_performance), 2) AS marketplace_sales_share_pct
FROM vw_seller_performance p
JOIN sellers s ON p.seller_id = s.seller_id
ORDER BY p.total_sales DESC
LIMIT 20;

-- Part B: Seller Geographic Concentration by State
SELECT 
    seller_state,
    COUNT(seller_id) AS total_sellers,
    ROUND(COUNT(seller_id) * 100.0 / (SELECT COUNT(*) FROM sellers), 2) AS sellers_share_pct,
    ROUND(SUM(total_sales), 2) AS total_state_sales,
    ROUND(SUM(total_sales) * 100.0 / (SELECT SUM(total_sales) FROM vw_seller_performance), 2) AS sales_share_pct,
    ROUND(AVG(avg_review_score), 2) AS avg_seller_rating
FROM vw_seller_performance
GROUP BY seller_state
ORDER BY total_state_sales DESC;
