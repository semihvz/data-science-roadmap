"""
Logistics & SLA Analytics Module
Analyzes delivery performance, SLA compliance, regional lead times,
freight cost economics, and customer dissatisfaction drivers.
"""

import pandas as pd
import numpy as np


def compute_logistics_kpis(df_orders: pd.DataFrame) -> dict:
    """
    Computes high-level logistics and fulfillment operational metrics.
    """
    deliv = df_orders[
        (df_orders["order_status"] == "delivered") &
        (df_orders["delivery_days"].notna())
    ].copy()

    total_deliv = len(deliv)
    if total_deliv == 0:
        return {}

    avg_lead_time = deliv["delivery_days"].mean()
    avg_estimated = deliv["estimated_days"].mean()
    
    delayed_orders = deliv[deliv["is_delayed"] == 1]
    late_count = len(delayed_orders)
    late_rate = (late_count / total_deliv * 100)
    ontime_rate = 100.0 - late_rate

    avg_delay_days = delayed_orders["delay_days"].mean() if late_count > 0 else 0.0
    
    early_orders = deliv[deliv["is_delayed"] == 0]
    avg_early_buffer = (early_orders["estimated_days"] - early_orders["delivery_days"]).mean() if len(early_orders) > 0 else 0.0

    avg_freight = deliv["total_freight"].mean()
    freight_ratio = (deliv["total_freight"] / deliv["total_order_value"].replace(0, np.nan) * 100).mean()

    return {
        "total_delivered_orders": int(total_deliv),
        "average_delivery_days": round(float(avg_lead_time), 1),
        "average_estimated_days": round(float(avg_estimated), 1),
        "late_delivery_rate_pct": round(float(late_rate), 2),
        "ontime_delivery_rate_pct": round(float(ontime_rate), 2),
        "avg_delay_when_late_days": round(float(avg_delay_days), 1),
        "avg_early_buffer_days": round(float(avg_early_buffer), 1),
        "average_freight_cost": round(float(avg_freight), 2),
        "average_freight_ratio_pct": round(float(freight_ratio), 2),
    }


def analyze_regional_logistics(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Computes state-by-state logistics efficiency, SLA adherence, and freight burden.
    """
    deliv = df_orders[
        (df_orders["order_status"] == "delivered") &
        (df_orders["delivery_days"].notna())
    ].copy()

    state_log = deliv.groupby("customer_state").agg(
        orders=("order_id", "count"),
        avg_delivery_days=("delivery_days", "mean"),
        avg_estimated_days=("estimated_days", "mean"),
        late_orders=("is_delayed", "sum"),
        avg_freight=("total_freight", "mean"),
        avg_order_value=("total_order_value", "mean"),
        avg_review=("review_score", "mean")
    ).reset_index()

    state_log["late_rate_pct"] = (state_log["late_orders"] / state_log["orders"] * 100).round(2)
    state_log["freight_ratio_pct"] = (state_log["avg_freight"] / state_log["avg_order_value"] * 100).round(2)
    
    # Sort by longest delivery time
    state_log = state_log.sort_values(by="avg_delivery_days", ascending=False).reset_index(drop=True)
    return state_log.round(2)


def delay_impact_on_reviews(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Correlates delivery delay severity with customer review ratings and dissatisfaction rates.
    """
    deliv = df_orders[
        (df_orders["order_status"] == "delivered") &
        (df_orders["review_score"].notna()) &
        (df_orders["delay_days"].notna())
    ].copy()

    def categorize_delay(delay):
        if delay <= -5:
            return "1. Fast (5+ days early)"
        elif delay <= 0:
            return "2. On Time (0-4 days early)"
        elif delay <= 3:
            return "3. Slightly Late (1-3 days late)"
        elif delay <= 7:
            return "4. Moderately Late (4-7 days late)"
        else:
            return "5. Severely Late (>7 days late)"

    deliv["delay_bucket"] = deliv["delay_days"].apply(categorize_delay)

    impact = deliv.groupby("delay_bucket").agg(
        order_count=("order_id", "count"),
        avg_review_score=("review_score", "mean"),
        five_star_pct=("review_score", lambda x: (x == 5).mean() * 100),
        one_star_pct=("review_score", lambda x: (x == 1).mean() * 100)
    ).reset_index()

    total_orders = impact["order_count"].sum()
    impact["share_pct"] = (impact["order_count"] / total_orders * 100).round(2)
    
    return impact.round(2)
