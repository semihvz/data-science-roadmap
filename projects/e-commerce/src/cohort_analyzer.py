import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def run_cohort_analysis(db_path="projects/e-commerce/data/ecommerce.db", output_dir="projects/e-commerce/reports"):
    os.makedirs(output_dir, exist_ok=True)
    print("📈 Executing Monthly Customer Cohort Retention Analysis...")

    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        customer_id,
        order_date,
        total_amount
    FROM orders
    WHERE order_status = 'Completed'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df['order_date'] = pd.to_datetime(df['order_date'])
    df['order_month'] = df['order_date'].dt.to_period('M')

    # Find cohort month (first order month for each customer)
    df['cohort_month'] = df.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')

    # Group by Cohort Month and Order Month
    cohort_data = df.groupby(['cohort_month', 'order_month']).agg({
        'customer_id': 'nunique'
    }).reset_index()

    # Calculate Month Index (Period 0, Period 1, ...)
    cohort_data['period_number'] = (cohort_data['order_month'].dt.year - cohort_data['cohort_month'].dt.year) * 12 + \
                                   (cohort_data['order_month'].dt.month - cohort_data['cohort_month'].dt.month)

    # Pivot to create Retention Matrix
    cohort_pivot = cohort_data.pivot(index='cohort_month', columns='period_number', values='customer_id')

    # Initial Cohort Size (Period 0)
    cohort_sizes = cohort_pivot.iloc[:, 0]

    # Calculate Percentage Retention
    retention_matrix = cohort_pivot.divide(cohort_sizes, axis=0) * 100.0

    csv_path = os.path.join(output_dir, "cohort_retention_matrix.csv")
    retention_matrix.round(2).to_csv(csv_path)
    print(f"  ✓ Saved Cohort Retention Matrix to `{csv_path}`")

    # Plot Seaborn Retention Heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        retention_matrix, 
        annot=True, 
        fmt=".1f", 
        cmap="Blues", 
        cbar_kws={'label': 'Retention Rate (%)'},
        linewidths=0.5
    )
    plt.title("Monthly Customer Cohort Retention Heatmap (%)", fontsize=14, fontweight='bold')
    plt.xlabel("Months Since First Purchase (Period Number)", fontsize=12)
    plt.ylabel("Cohort Month", fontsize=12)
    plt.tight_layout()

    chart_path = os.path.join(output_dir, "cohort_retention_heatmap.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"  ✓ Saved Cohort Retention Heatmap to `{chart_path}`")

    return retention_matrix, cohort_sizes

if __name__ == "__main__":
    run_cohort_analysis()
