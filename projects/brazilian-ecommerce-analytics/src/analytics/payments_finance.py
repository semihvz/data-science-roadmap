"""
Payments & Financial Behavior Analytics Module
Analyzes Brazilian payment ecosystem, method breakdown, installment financing habits,
and basket size correlation.
"""

import pandas as pd
import numpy as np


def compute_payment_method_breakdown(df_payments: pd.DataFrame) -> pd.DataFrame:
    """
    Computes volume and transaction distribution across payment methods.
    """
    df = df_payments[df_payments["payment_type"] != "not_defined"].copy()
    
    total_trans = len(df)
    total_vol = df["payment_value"].sum()

    breakdown = df.groupby("payment_type").agg(
        transactions=("order_id", "count"),
        total_volume=("payment_value", "sum"),
        avg_ticket=("payment_value", "mean"),
        avg_installments=("payment_installments", "mean")
    ).reset_index()

    breakdown["transaction_share_pct"] = (breakdown["transactions"] / total_trans * 100).round(2)
    breakdown["volume_share_pct"] = (breakdown["total_volume"] / total_vol * 100).round(2)
    
    return breakdown.sort_values(by="total_volume", ascending=False).reset_index(drop=True).round(2)


def analyze_installments(df_payments: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates credit card installment usage and relation with order ticket size.
    """
    cc = df_payments[df_payments["payment_type"] == "credit_card"].copy()
    total_cc = len(cc)

    inst_summary = cc.groupby("payment_installments").agg(
        transactions=("order_id", "count"),
        total_volume=("payment_value", "sum"),
        avg_order_value=("payment_value", "mean")
    ).reset_index()

    inst_summary["transaction_share_pct"] = (inst_summary["transactions"] / total_cc * 100).round(2)
    
    def bin_installments(x):
        if x == 1:
            return "1 Installment (Full)"
        elif 2 <= x <= 3:
            return "2 - 3 Installments"
        elif 4 <= x <= 6:
            return "4 - 6 Installments"
        elif 7 <= x <= 10:
            return "7 - 10 Installments"
        else:
            return "> 10 Installments"

    cc["installment_tier"] = cc["payment_installments"].apply(bin_installments)
    tier_summary = cc.groupby("installment_tier").agg(
        transactions=("order_id", "count"),
        total_volume=("payment_value", "sum"),
        avg_order_value=("payment_value", "mean")
    ).reset_index()

    tier_summary["share_pct"] = (tier_summary["transactions"] / total_cc * 100).round(2)
    return tier_summary.round(2)
