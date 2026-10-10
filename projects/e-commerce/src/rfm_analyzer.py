import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def run_rfm_analysis(db_path="projects/e-commerce/data/ecommerce.db", output_dir="projects/e-commerce/reports"):
    os.makedirs(output_dir, exist_ok=True)
    print("🔍 Executing RFM Customer Segmentation Analysis...")

    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.email,
        c.city,
        c.acquisition_channel,
        o.order_date,
        o.total_amount
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.order_status = 'Completed'
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    df['order_date'] = pd.to_datetime(df['order_date'])
    reference_date = df['order_date'].max() + pd.Timedelta(days=1)

    # Calculate RFM values
    rfm = df.groupby('customer_id').agg({
        'order_date': lambda x: (reference_date - x.max()).days,
        'email': 'count',
        'total_amount': 'sum'
    }).reset_index()

    rfm.rename(columns={
        'order_date': 'recency',
        'email': 'frequency',
        'total_amount': 'monetary'
    }, inplace=True)

    # Compute RFM Scores (1 to 5)
    rfm['r_score'] = pd.qcut(rfm['recency'], q=5, labels=[5, 4, 3, 2, 1])
    
    # Frequency can have ties, so use rank(method='first') for robust qcut
    rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])
    rfm['m_score'] = pd.qcut(rfm['monetary'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])

    rfm['r_score'] = rfm['r_score'].astype(int)
    rfm['f_score'] = rfm['f_score'].astype(int)
    rfm['m_score'] = rfm['m_score'].astype(int)

    def segment_customer(row):
        r, f, m = row['r_score'], row['f_score'], row['m_score']
        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions'
        elif r >= 3 and f >= 3 and m >= 3:
            return 'Loyal Customers'
        elif r >= 4 and f <= 2:
            return 'Promising / New'
        elif r <= 2 and f >= 3 and m >= 3:
            return 'At Risk'
        elif r <= 2 and f <= 2 and m <= 2:
            return 'Lost Customers'
        elif r == 3 and f <= 2:
            return 'About to Sleep'
        else:
            return 'Need Attention'

    rfm['rfm_segment'] = rfm.apply(segment_customer, axis=1)

    # Segment Summary Statistics
    summary = rfm.groupby('rfm_segment').agg({
        'customer_id': 'count',
        'recency': 'mean',
        'frequency': 'mean',
        'monetary': ['mean', 'sum']
    }).round(2)

    summary.columns = ['customer_count', 'avg_recency_days', 'avg_frequency', 'avg_monetary', 'total_segment_revenue']
    summary['customer_share_pct'] = (summary['customer_count'] / len(rfm) * 100).round(2)
    summary = summary.sort_values(by='total_segment_revenue', ascending=False)

    csv_path = os.path.join(output_dir, "rfm_segment_summary.csv")
    summary.to_csv(csv_path)
    print(f"  ✓ Saved RFM summary to `{csv_path}`")

    # Plot RFM Segment Distribution Chart
    plt.figure(figsize=(10, 6))
    palette = sns.color_palette("viridis", len(summary))
    ax = sns.barplot(x=summary.index, y=summary['total_segment_revenue'], hue=summary.index, legend=False, palette=palette)
    plt.title("Total Revenue by RFM Customer Segment", fontsize=14, fontweight='bold')
    plt.xlabel("RFM Segment", fontsize=12)
    plt.ylabel("Total Revenue ($)", fontsize=12)
    plt.xticks(rotation=30)
    plt.tight_layout()

    chart_path = os.path.join(output_dir, "rfm_distribution.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"  ✓ Saved RFM distribution chart to `{chart_path}`")

    return rfm, summary

if __name__ == "__main__":
    run_rfm_analysis()
