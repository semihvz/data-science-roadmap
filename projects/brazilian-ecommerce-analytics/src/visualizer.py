"""
Visualizer Module: Generates Publication-Quality High-Resolution Charts
Outputs styled analytical figures to reports/figures/
"""

import sys
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "olist.db"
FIGURES_DIR = BASE_DIR / "reports" / "figures"

# Set styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.sans-serif": "DejaVu Sans",
    "axes.edgecolor": "#cccccc",
    "axes.linewidth": 0.8,
    "grid.color": "#ebebeb",
    "grid.linestyle": "--",
    "grid.alpha": 0.7,
})

PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]


def generate_all_figures():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)

    # 1. Monthly Revenue & Order Growth
    print("Generating Figure 1: Monthly Revenue & Growth...")
    query_monthly = """
    SELECT 
        SUBSTR(order_purchase_timestamp, 1, 7) AS year_month,
        COUNT(DISTINCT order_id) AS orders,
        ROUND(SUM(items_value), 2) AS gmv
    FROM vw_orders_summary
    WHERE order_status = 'delivered'
      AND order_purchase_timestamp >= '2017-01-01'
      AND order_purchase_timestamp < '2018-09-01'
    GROUP BY SUBSTR(order_purchase_timestamp, 1, 7)
    ORDER BY year_month ASC
    """
    df_m = pd.read_sql_query(query_monthly, conn)

    fig, ax1 = plt.subplots(figsize=(12, 6), dpi=300)
    ax2 = ax1.twinx()

    x = range(len(df_m))
    bars = ax1.bar(x, df_m["gmv"] / 1000, color="#2b5c8f", alpha=0.85, width=0.55, label="GMV (k R$)")
    lines = ax2.plot(x, df_m["orders"], color="#e76f51", marker="o", linewidth=2.5, label="Order Count")

    ax1.set_xticks(x)
    ax1.set_xticklabels(df_m["year_month"], rotation=45, ha="right", fontsize=9)
    ax1.set_ylabel("Gross Merchandise Value (Thousand R$)", fontsize=11, fontweight="bold", color="#2b5c8f")
    ax2.set_ylabel("Delivered Orders", fontsize=11, fontweight="bold", color="#e76f51")
    ax1.set_title("Olist Monthly Revenue (GMV) & Order Trajectory (2017 - 2018)", fontsize=14, fontweight="bold", pad=15)

    # Highlight Black Friday 2017
    bf_idx = df_m[df_m["year_month"] == "2017-11"].index
    if len(bf_idx) > 0:
        idx = bf_idx[0]
        ax1.annotate(
            "Black Friday Peak\n(Nov 2017)",
            xy=(idx, df_m.loc[idx, "gmv"] / 1000),
            xytext=(idx - 2, (df_m.loc[idx, "gmv"] / 1000) * 0.95),
            arrowprops=dict(facecolor="#d62728", shrink=0.08, width=1.5, headwidth=7),
            fontsize=9, fontweight="bold", color="#d62728"
        )

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "01_monthly_revenue_growth.png")
    plt.close()

    # 2. RFM Customer Segments Distribution
    print("Generating Figure 2: RFM Customer Segments...")
    query_rfm = """
    WITH ref AS (SELECT DATE(MAX(order_purchase_timestamp), '+1 day') AS ref_date FROM orders),
    cust AS (
        SELECT 
            c.customer_unique_id,
            CAST((JULIANDAY((SELECT ref_date FROM ref)) - JULIANDAY(MAX(o.order_purchase_timestamp))) AS INT) AS recency,
            COUNT(DISTINCT o.order_id) AS frequency,
            SUM(i.price) AS monetary
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items i ON o.order_id = i.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_unique_id
    ),
    scored AS (
        SELECT 
            customer_unique_id, recency, frequency, monetary,
            NTILE(5) OVER (ORDER BY recency DESC) AS r,
            CASE WHEN frequency = 1 THEN 1 WHEN frequency = 2 THEN 3 WHEN frequency = 3 THEN 4 ELSE 5 END AS f,
            NTILE(5) OVER (ORDER BY monetary ASC) AS m
        FROM cust
    ),
    seg AS (
        SELECT 
            CASE
                WHEN r >= 4 AND f >= 4 THEN 'Champions'
                WHEN r >= 3 AND f >= 3 THEN 'Loyal Customers'
                WHEN r >= 4 AND f < 3 THEN 'Recent Customers'
                WHEN r = 3 AND f = 1 THEN 'Promising'
                WHEN r = 2 AND f >= 2 THEN 'Need Attention'
                WHEN r = 2 AND f = 1 THEN 'About to Sleep'
                WHEN r = 1 AND f >= 3 THEN 'At Risk (High Value)'
                WHEN r = 1 AND f = 2 THEN 'Hibernating'
                ELSE 'Lost Customers'
            END AS segment,
            monetary
        FROM scored
    )
    SELECT segment, COUNT(*) AS count, SUM(monetary) AS total_spend
    FROM seg
    GROUP BY segment
    ORDER BY total_spend DESC;
    """
    df_rfm = pd.read_sql_query(query_rfm, conn)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    colors = sns.color_palette("viridis", len(df_rfm))
    y_pos = range(len(df_rfm))
    bars = ax.barh(y_pos, df_rfm["total_spend"] / 1000, color=colors, alpha=0.85)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df_rfm["segment"], fontsize=10, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel("Total Segment Revenue (Thousand R$)", fontsize=11, fontweight="bold")
    ax.set_title("Customer Value by Strategic RFM Segment", fontsize=14, fontweight="bold", pad=15)

    for i, bar in enumerate(bars):
        spend = df_rfm.loc[i, "total_spend"] / 1000
        count = df_rfm.loc[i, "count"]
        ax.text(spend + 15, bar.get_y() + bar.get_height() / 2, f"{spend:,.0f}k R$ ({count:,} cust)", 
                va="center", fontsize=8.5, color="#333333")

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "02_rfm_customer_segments.png")
    plt.close()

    # 3. Delivery Lead Times by State
    print("Generating Figure 3: Regional Delivery Lead Times...")
    query_logistics = """
    SELECT 
        customer_state,
        COUNT(order_id) AS orders,
        ROUND(AVG(delivery_days), 1) AS avg_delivery_days,
        ROUND(AVG(estimated_days), 1) AS avg_estimated_days
    FROM vw_orders_summary
    WHERE order_status = 'delivered' AND delivery_days IS NOT NULL
    GROUP BY customer_state
    ORDER BY avg_delivery_days DESC
    """
    df_log = pd.read_sql_query(query_logistics, conn)

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    x = range(len(df_log))
    ax.bar(x, df_log["avg_delivery_days"], color="#2a9d8f", alpha=0.85, label="Actual Delivery Days")
    ax.plot(x, df_log["avg_estimated_days"], color="#e76f51", marker="s", linestyle="--", linewidth=1.8, label="Estimated SLA")

    ax.set_xticks(x)
    ax.set_xticklabels(df_log["customer_state"], fontsize=9, fontweight="bold")
    ax.set_ylabel("Days to Delivery", fontsize=11, fontweight="bold")
    ax.set_title("Delivery Lead Time by Brazilian State (North vs Southeast Disparity)", fontsize=14, fontweight="bold", pad=15)
    ax.legend(frameon=True)

    # Highlight SP vs RR
    ax.axhline(df_log["avg_delivery_days"].mean(), color="gray", linestyle=":", alpha=0.8, label="National Mean")

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "03_logistics_delivery_by_state.png")
    plt.close()

    # 4. Delivery Delay vs Review Score Drop
    print("Generating Figure 4: Delay vs Customer Satisfaction...")
    query_delay_rev = """
    WITH delay_buckets AS (
        SELECT 
            order_id,
            review_score,
            CASE 
                WHEN delay_days <= -5 THEN '1. Early (>5d)'
                WHEN delay_days <= 0 THEN '2. On-Time (0-4d)'
                WHEN delay_days <= 3 THEN '3. Late (1-3d)'
                WHEN delay_days <= 7 THEN '4. Late (4-7d)'
                ELSE '5. Critical Late (>7d)'
            END AS bucket
        FROM vw_orders_summary
        WHERE order_status = 'delivered' AND review_score IS NOT NULL AND delay_days IS NOT NULL
    )
    SELECT 
        bucket,
        ROUND(AVG(review_score), 2) AS avg_score,
        ROUND(SUM(CASE WHEN review_score = 5 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS five_star_pct,
        ROUND(SUM(CASE WHEN review_score = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS one_star_pct
    FROM delay_buckets
    GROUP BY bucket
    ORDER BY bucket ASC
    """
    df_dr = pd.read_sql_query(query_delay_rev, conn)

    fig, ax1 = plt.subplots(figsize=(9, 5), dpi=300)
    x = range(len(df_dr))
    bars = ax1.bar(x, df_dr["avg_score"], color=["#2ca02c", "#8fbb43", "#e6a817", "#e76f51", "#d62728"], alpha=0.85)

    ax1.set_xticks(x)
    ax1.set_xticklabels(df_dr["bucket"], fontsize=10, fontweight="bold")
    ax1.set_ylabel("Average Review Score (1 - 5 Stars)", fontsize=11, fontweight="bold")
    ax1.set_ylim(0, 5)
    ax1.set_title("Impact of Delivery Delays on Customer Review Ratings", fontsize=14, fontweight="bold", pad=15)

    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, height + 0.1, f"{height:.2f} ★", 
                 ha="center", fontsize=10, fontweight="bold")

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "04_delay_impact_on_csat.png")
    plt.close()

    # 5. Product Category Pareto Analysis
    print("Generating Figure 5: Category Pareto 80/20...")
    query_pareto = """
    SELECT 
        category_name,
        total_revenue,
        ROUND(SUM(total_revenue) OVER (ORDER BY total_revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 100.0 
              / SUM(total_revenue) OVER (), 1) AS cum_pct
    FROM vw_category_sales
    ORDER BY total_revenue DESC
    LIMIT 20
    """
    df_p = pd.read_sql_query(query_pareto, conn)

    fig, ax1 = plt.subplots(figsize=(12, 6), dpi=300)
    ax2 = ax1.twinx()

    x = range(len(df_p))
    ax1.bar(x, df_p["total_revenue"] / 1000, color="#1f77b4", alpha=0.8, width=0.6)
    ax2.plot(x, df_p["cum_pct"], color="#d62728", marker="o", linewidth=2)

    ax1.set_xticks(x)
    ax1.set_xticklabels(df_p["category_name"], rotation=45, ha="right", fontsize=9)
    ax1.set_ylabel("Revenue (Thousand R$)", fontsize=11, fontweight="bold", color="#1f77b4")
    ax2.set_ylabel("Cumulative Revenue %", fontsize=11, fontweight="bold", color="#d62728")
    ax2.axhline(80, color="gray", linestyle="--", alpha=0.7)
    ax2.text(len(df_p) - 3, 82, "80% Revenue Threshold", color="#d62728", fontsize=9, fontweight="bold")
    ax1.set_title("Product Category Pareto Curve (Top 20 Categories)", fontsize=14, fontweight="bold", pad=15)

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "05_pareto_category_revenue.png")
    plt.close()

    # 6. Payment Methods Share Donut Chart
    print("Generating Figure 6: Payment Methods Share...")
    query_payments = """
    SELECT payment_type, SUM(payment_value) AS vol
    FROM order_payments
    WHERE payment_type != 'not_defined'
    GROUP BY payment_type
    ORDER BY vol DESC
    """
    df_pay = pd.read_sql_query(query_payments, conn)

    fig, ax = plt.subplots(figsize=(7, 7), dpi=300)
    labels = [p.replace("_", " ").title() for p in df_pay["payment_type"]]
    colors = ["#2b5c8f", "#e76f51", "#2ca02c", "#f4a261"]
    wedges, texts, autotexts = ax.pie(
        df_pay["vol"], labels=labels, autopct="%1.1f%%",
        startangle=140, colors=colors, pctdistance=0.75,
        textprops=dict(fontsize=10, fontweight="bold"),
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2)
    )
    for at in autotexts:
        at.set_color("white")
    ax.set_title("Marketplace Payment Volume by Channel", fontsize=14, fontweight="bold", pad=15)

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "06_payment_methods_share.png")
    plt.close()

    # 7. Purchasing Day & Hour Heatmap
    print("Generating Figure 7: Purchasing Intensity Heatmap...")
    query_heatmap = """
    SELECT order_purchase_timestamp FROM orders WHERE order_status = 'delivered'
    """
    df_ord = pd.read_sql_query(query_heatmap, conn)
    df_ord["dt"] = pd.to_datetime(df_ord["order_purchase_timestamp"])
    df_ord["day"] = df_ord["dt"].dt.day_name()
    df_ord["hour"] = df_ord["dt"].dt.hour

    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = df_ord.pivot_table(index="day", columns="hour", values="order_purchase_timestamp", aggfunc="count", fill_value=0)
    pivot = pivot.reindex(days_order)

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    sns.heatmap(pivot, cmap="YlGnBu", ax=ax, cbar_kws={"label": "Delivered Orders"}, linewidths=0.5)
    ax.set_title("Customer Purchasing Heatmap: Day of Week vs Hour of Day (BRT)", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Hour of Day (00:00 - 23:00)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Day of Week", fontsize=11, fontweight="bold")

    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "07_purchasing_heatmap.png")
    plt.close()

    conn.close()
    print("All 7 figures generated and saved in reports/figures/!")


if __name__ == "__main__":
    generate_all_figures()
