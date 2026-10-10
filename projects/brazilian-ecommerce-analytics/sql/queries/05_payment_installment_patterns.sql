-- Business Query 5: Payment Types & Installment Financing Behavior
-- Explores Brazilian payment habits, credit card installment adoption by basket size, and cash flow timing.

-- Part A: Payment Channel Breakdown
SELECT 
    payment_type,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(COUNT(DISTINCT order_id) * 100.0 / (SELECT COUNT(DISTINCT order_id) FROM order_payments), 2) AS order_share_pct,
    ROUND(SUM(payment_value), 2) AS total_payment_value,
    ROUND(SUM(payment_value) * 100.0 / (SELECT SUM(payment_value) FROM order_payments), 2) AS revenue_share_pct,
    ROUND(AVG(payment_value), 2) AS avg_transaction_value,
    ROUND(AVG(payment_installments), 1) AS avg_installments
FROM order_payments
GROUP BY payment_type
ORDER BY total_payment_value DESC;

-- Part B: Installment Distribution for Credit Card Transactions
SELECT 
    payment_installments,
    COUNT(order_id) AS transaction_count,
    ROUND(COUNT(order_id) * 100.0 / (SELECT COUNT(*) FROM order_payments WHERE payment_type = 'credit_card'), 2) AS transaction_pct,
    ROUND(SUM(payment_value), 2) AS total_volume,
    ROUND(AVG(payment_value), 2) AS avg_order_ticket_value
FROM order_payments
WHERE payment_type = 'credit_card'
GROUP BY payment_installments
ORDER BY payment_installments ASC;
