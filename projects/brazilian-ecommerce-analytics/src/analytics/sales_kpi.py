"""
Sales & Executive KPI Analytics Module
Computes high-level marketplace metrics, monthly growth trajectories,
geographic penetration, and purchasing temporal patterns.
"""

import pandas as pd
import numpy as np


def compute_overview_kpis(df_orders: pd.DataFrame) -> dict:
    """
    Computes top-level executive KPIs across the marketplace dataset.
    """
    total_orders = len(df_orders)
    delivered_orders = df_orders[df_orders["order_status"] == "delivered"]
    num_delivered = len(delivered_orders)
    num_canceled = len(df_orders[df_orders["order_status"] == "canceled"])
    
    cancellation_rate = (num_canceled / total_orders * 100) if total_orders > 0 else 0.0
    unique_customers = df_orders["customer_unique_id"].nunique()
    
    gmv = delivered_orders["items_value"].sum()
    freight = delivered_orders["total_freight"].sum()
    gross_revenue = delivered_orders["total_order_value"].sum()
    
    aov = (gross_revenue / num_delivered) if num_delivered > 0 else 0.0
    avg_items = delivered_orders["total_items"].mean() if num_delivered > 0 else 0.0
    
    avg_review = delivered_orders["review_score"].dropna().mean()
    
    delayed_count = delivered_orders["is_delayed"].sum()
    late_rate = (delayed_count / num_delivered * 100) if num_delivered > 0 else 0.0
    ontime_rate = 100.0 - late_rate

    return {
        "total_orders": int(total_orders),
        "delivered_orders": int(num_delivered),
        "canceled_orders": int(num_canceled),
        "cancellation_rate_pct": round(cancellation_rate, 2),
        "unique_customers": int(unique_customers),
        "gross_merchandise_value": round(float(gmv), 2),
        "total_freight": round(float(freight), 2),
        "gross_revenue": round(float(gross_revenue), 2),
        "average_order_value": round(float(aov), 2),
        "average_items_per_order": round(float(avg_items), 2),
        "average_review_score": round(float(avg_review), 2),
        "late_delivery_rate_pct": round(float(late_rate), 2),
        "ontime_delivery_rate_pct": round(float(ontime_rate), 2),
    }


def compute_monthly_sales_trend(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates monthly sales performance, GMV, orders, and MoM growth rates.
    Filters standard full-operation period (2017-01 to 2018-08).
    """
    df_valid = df_orders[
        (df_orders["order_status"] == "delivered") &
        (df_orders["order_purchase_timestamp"] >= "2017-01-01") &
        (df_orders["order_purchase_timestamp"] < "2018-09-01")
    ].copy()

    df_valid["year_month"] = df_valid["order_purchase_timestamp"].str.slice(0, 7)
    
    monthly = df_valid.groupby("year_month").agg(
        orders=("order_id", "count"),
        active_customers=("customer_unique_id", "nunique"),
        gmv=("items_value", "sum"),
        freight=("total_freight", "sum"),
        total_revenue=("total_order_value", "sum"),
        aov=("total_order_value", "mean")
    ).reset_index()

    monthly["mom_gmv_growth_pct"] = monthly["gmv"].pct_change() * 100
    monthly["mom_orders_growth_pct"] = monthly["orders"].pct_change() * 100

    return monthly.round(2)


def compute_state_distribution(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Computes geographic breakdown of orders, revenue, and customer concentration across Brazilian states (UF).
    """
    df_deliv = df_orders[df_orders["order_status"] == "delivered"].copy()
    
    state_df = df_deliv.groupby("customer_state").agg(
        total_orders=("order_id", "count"),
        total_revenue=("total_order_value", "sum"),
        total_gmv=("items_value", "sum"),
        avg_aov=("total_order_value", "mean"),
        avg_review=("review_score", "mean")
    ).reset_index()

    total_market_rev = state_df["total_revenue"].sum()
    state_df["revenue_share_pct"] = (state_df["total_revenue"] / total_market_rev * 100).round(2)
    state_df = state_df.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
    state_df["cumulative_revenue_pct"] = state_df["revenue_share_pct"].cumsum().round(2)

    return state_df.round(2)


def compute_day_and_hour_patterns(df_orders: pd.DataFrame) -> pd.DataFrame:
    """
    Generates a pivot matrix of order counts by Day of Week vs Hour of Day.
    Useful for promotional scheduling and marketing push timing.
    """
    df = df_orders.copy()
    df["dt"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["day_name"] = df["dt"].dt.day_name()
    df["hour"] = df["dt"].dt.hour

    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = df.pivot_table(
        index="day_name",
        columns="hour",
        values="order_id",
        aggfunc="count",
        fill_value=0
    )
    pivot = pivot.reindex(days_order)
    return pivot
