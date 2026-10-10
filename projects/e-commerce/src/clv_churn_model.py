import os
import sqlite3
import pandas as pd
import numpy as np

def calculate_clv_and_churn(db_path="projects/e-commerce/data/ecommerce.db", output_dir="projects/e-commerce/reports"):
    os.makedirs(output_dir, exist_ok=True)
    print("🔮 Modeling Customer Lifetime Value (CLV) & Churn Risk...")

    conn = sqlite3.connect(db_path)
    query = """
    SELECT 
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.email,
        c.city,
        c.acquisition_channel,
        c.signup_date,
        o.order_date,
        o.total_amount
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'Completed'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df['order_date'] = pd.to_datetime(df['order_date'])
    df['signup_date'] = pd.to_datetime(df['signup_date'])
    ref_date = df['order_date'].max() + pd.Timedelta(days=1)

    clv_df = df.groupby('customer_id').agg({
        'customer_name': 'first',
        'email': 'first',
        'city': 'first',
        'acquisition_channel': 'first',
        'signup_date': 'min',
        'order_date': ['min', 'max', 'count'],
        'total_amount': ['sum', 'mean']
    }).reset_index()

    clv_df.columns = [
        'customer_id', 'customer_name', 'email', 'city', 'acquisition_channel', 
        'signup_date', 'first_order', 'last_order', 'total_orders', 
        'historical_clv', 'avg_order_value'
    ]

    clv_df['days_since_last_order'] = (ref_date - clv_df['last_order']).dt.days
    clv_df['customer_lifespan_days'] = (clv_df['last_order'] - clv_df['first_order']).dt.days

    # Define Churn Risk logic
    def evaluate_churn_risk(recency_days):
        if recency_days > 180:
            return 'High Risk (Churned)'
        elif recency_days > 90:
            return 'Medium Risk'
        else:
            return 'Low Risk (Active)'

    clv_df['churn_risk_level'] = clv_df['days_since_last_order'].apply(evaluate_churn_risk)

    # Simplified Predictive 12-Month CLV Estimate
    # Formula: Historical Daily Spend Rate * 365 (adjusted by retention probability)
    def estimate_future_clv(row):
        lifespan = max(1, row['customer_lifespan_days'])
        daily_rate = row['historical_clv'] / lifespan
        retention_multiplier = 0.2 if row['churn_risk_level'] == 'High Risk (Churned)' else (0.6 if row['churn_risk_level'] == 'Medium Risk' else 0.95)
        return round(row['historical_clv'] + (daily_rate * 365 * retention_multiplier * 0.3), 2)

    clv_df['projected_12m_clv'] = clv_df.apply(estimate_future_clv, axis=1)

    csv_path = os.path.join(output_dir, "customer_churn_clv_summary.csv")
    numeric_cols = clv_df.select_dtypes(include=[np.number]).columns
    clv_df[numeric_cols] = clv_df[numeric_cols].round(2)
    clv_df.sort_values(by='projected_12m_clv', ascending=False).to_csv(csv_path, index=False)
    print(f"  ✓ Saved CLV & Churn predictions to `{csv_path}`")

    # Print summary statistics
    churn_summary = clv_df.groupby('churn_risk_level').agg({
        'customer_id': 'count',
        'historical_clv': 'sum',
        'projected_12m_clv': 'sum'
    }).round(2)
    print("  ✓ Churn Risk Breakdown:")
    print(churn_summary)

    return clv_df, churn_summary

if __name__ == "__main__":
    calculate_clv_and_churn()
