"""
Product & Category Intelligence Analytics Module
Performs Pareto 80/20 analysis, ABC classification, category performance ranking,
and revenue concentration evaluation.
"""

import pandas as pd
import numpy as np


def compute_category_pareto(df_category: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Pareto 80/20 analysis across product categories.
    Classifies categories into Class A (Top 80%), Class B (Next 15%), and Class C (Long Tail 5%).
    """
    df = df_category.copy().sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
    
    total_market_rev = df["total_revenue"].sum()
    df["revenue_share_pct"] = (df["total_revenue"] / total_market_rev * 100).round(2)
    df["cumulative_revenue"] = df["total_revenue"].cumsum()
    df["cumulative_revenue_pct"] = (df["cumulative_revenue"] / total_market_rev * 100).round(2)
    df["rank"] = df.index + 1

    def assign_abc(cum_pct):
        if cum_pct <= 80.0:
            return "Class A (Core 80%)"
        elif cum_pct <= 95.0:
            return "Class B (Secondary 15%)"
        else:
            return "Class C (Long Tail 5%)"

    df["abc_class"] = df["cumulative_revenue_pct"].apply(assign_abc)
    return df


def top_categories_metrics(df_category: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Returns top N revenue generating categories with key operational metrics.
    """
    pareto_df = compute_category_pareto(df_category)
    return pareto_df.head(top_n)
