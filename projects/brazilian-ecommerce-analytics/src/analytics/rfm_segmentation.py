"""
Customer Analytics: RFM Segmentation & Cohort Retention Module
Performs Recency, Frequency, Monetary (RFM) scoring, behavioral tiering,
cohort acquisition retention analysis, and strategic customer playbooks.
"""

import pandas as pd
import numpy as np


def calculate_rfm_metrics(df_orders: pd.DataFrame, ref_date: str = None) -> pd.DataFrame:
    """
    Calculates Recency, Frequency, and Monetary metrics for unique customers.
    """
    df_deliv = df_orders[df_orders["order_status"] == "delivered"].copy()
    df_deliv["dt"] = pd.to_datetime(df_deliv["order_purchase_timestamp"])
    
    if ref_date is None:
        anchor = df_deliv["dt"].max() + pd.Timedelta(days=1)
    else:
        anchor = pd.to_datetime(ref_date)

    rfm = df_deliv.groupby("customer_unique_id").agg(
        last_purchase=("dt", "max"),
        first_purchase=("dt", "min"),
        frequency=("order_id", "nunique"),
        monetary=("items_value", "sum"),
        customer_state=("customer_state", "first"),
        customer_city=("customer_city", "first")
    ).reset_index()

    rfm["recency"] = (anchor - rfm["last_purchase"]).dt.days
    rfm["customer_tenure_days"] = (rfm["last_purchase"] - rfm["first_purchase"]).dt.days
    
    return rfm


def segment_customers(df_rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Assigns RFM scores (1-5) and categorizes customers into strategic marketing segments.
    """
    df = df_rfm.copy()
    
    # 1. Recency Score (Higher score = More recent = Better)
    df["r_score"] = pd.qcut(df["recency"], q=5, labels=[5, 4, 3, 2, 1]).astype(int)

    # 2. Frequency Score (Handled discrete due to 1-purchase dominance in Olist)
    def assign_f_score(f):
        if f == 1:
            return 1
        elif f == 2:
            return 3
        elif f == 3:
            return 4
        else:
            return 5
    df["f_score"] = df["frequency"].apply(assign_f_score)

    # 3. Monetary Score (Higher score = Higher spend)
    df["m_score"] = pd.qcut(df["monetary"], q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    
    df["rfm_combined"] = df["r_score"].astype(str) + df["f_score"].astype(str) + df["m_score"].astype(str)

    # Segment classification rules
    def assign_segment(row):
        r, f = row["r_score"], row["f_score"]
        if r >= 4 and f >= 4:
            return "Champions"
        elif r >= 3 and f >= 3:
            return "Loyal Customers"
        elif r >= 4 and f == 3:
            return "Potential Loyalists"
        elif r >= 4 and f == 1:
            return "Recent Customers"
        elif r == 3 and f <= 2:
            return "Promising"
        elif r == 2 and f >= 3:
            return "Customers Needing Attention"
        elif r == 2 and f <= 2:
            return "About to Sleep"
        elif r == 1 and f >= 3:
            return "At Risk (High Value)"
        elif r == 1 and f == 2:
            return "Hibernating"
        else:
            return "Lost Customers"

    df["segment"] = df.apply(assign_segment, axis=1)
    return df


def get_segment_summary(df_segmented: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates metrics per segment including customer share and revenue contribution.
    """
    total_cust = len(df_segmented)
    total_rev = df_segmented["monetary"].sum()

    summary = df_segmented.groupby("segment").agg(
        customer_count=("customer_unique_id", "count"),
        total_revenue=("monetary", "sum"),
        avg_recency_days=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean")
    ).reset_index()

    summary["customer_pct"] = (summary["customer_count"] / total_cust * 100).round(2)
    summary["revenue_pct"] = (summary["total_revenue"] / total_rev * 100).round(2)
    
    return summary.sort_values(by="total_revenue", ascending=False).reset_index(drop=True).round(2)


def compute_cohort_retention(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates monthly customer acquisition cohorts and repeat purchase retention matrix.
    """
    df = df_orders[df_orders["order_status"] == "delivered"].copy()
    df["dt"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["order_month"] = df["dt"].dt.to_period("M")
    
    # Customer cohort is the month of first purchase
    df["cohort_month"] = df.groupby("customer_unique_id")["order_month"].transform("min")
    
    # Calculate period offset
    cohort_group = df.groupby(["cohort_month", "order_month"]).agg(
        n_customers=("customer_unique_id", "nunique")
    ).reset_index()
    
    cohort_group["period_number"] = (
        (cohort_group["order_month"].dt.year - cohort_group["cohort_month"].dt.year) * 12 +
        (cohort_group["order_month"].dt.month - cohort_group["cohort_month"].dt.month)
    )

    cohort_pivot = cohort_group.pivot_table(
        index="cohort_month",
        columns="period_number",
        values="n_customers"
    )

    cohort_size = cohort_pivot.iloc[:, 0]
    retention_matrix = cohort_pivot.divide(cohort_size, axis=0) * 100
    return retention_matrix.round(2)


def get_segment_playbook() -> dict:
    """
    Provides marketing strategies and retention playbooks for each RFM segment.
    """
    return {
        "Champions": {
            "description": "Bought recently, buy often, and spend the most.",
            "strategy": "Reward loyalty with VIP perks, early product drops, advocate program, no heavy discounts needed.",
            "priority": "Critical Retention"
        },
        "Loyal Customers": {
            "description": "Consistent repeat buyers with solid lifetime value.",
            "strategy": "Upsell higher margin categories, offer subscription or loyalty points program, request product reviews.",
            "priority": "High Value Nurturing"
        },
        "Potential Loyalists": {
            "description": "Recent buyers with multi-order behavior.",
            "strategy": "Cross-sell complementary categories, recommend best-sellers, engage via personalized recommendations.",
            "priority": "Growth Acceleration"
        },
        "Recent Customers": {
            "description": "Bought recently for the first time.",
            "strategy": "Onboarding welcome series, immediate second-purchase coupon (within 14 days), introduce customer service.",
            "priority": "Onboarding & Conversion"
        },
        "Promising": {
            "description": "Moderate recency and spend, bought once or twice.",
            "strategy": "Seasonal campaigns, limited-time offers, category discovery emails.",
            "priority": "Engagement"
        },
        "Customers Needing Attention": {
            "description": "Above average spend and frequency, but haven't purchased in a while.",
            "strategy": "Reactivate with targeted time-sensitive discounts, showcase new catalog arrivals, ask for feedback.",
            "priority": "Reactivation"
        },
        "About to Sleep": {
            "description": "Below average recency and frequency. Will lose them if not reactivated.",
            "strategy": "Aggressive win-back discounts, highlight trending products, cart abandonment triggers.",
            "priority": "Risk Mitigation"
        },
        "At Risk (High Value)": {
            "description": "Spent big money and purchased multiple times in past, but gone cold.",
            "strategy": "High-priority direct outreach, significant win-back coupon (e.g. 20% off), surveys on customer service issues.",
            "priority": "High Urgency Win-Back"
        },
        "Hibernating": {
            "description": "Last purchase was long ago, low spend.",
            "strategy": "Standard clearance newsletter, low-cost marketing, do not overspend on paid ads.",
            "priority": "Low Cost Recovery"
        },
        "Lost Customers": {
            "description": "Lowest recency, frequency, and monetary scores.",
            "strategy": "Deprioritize ad spend. Periodically trigger annual major sale email (e.g. Black Friday).",
            "priority": "Deprioritized"
        }
    }
