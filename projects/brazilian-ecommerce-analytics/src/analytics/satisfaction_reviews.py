"""
Customer Satisfaction & Reviews Analytics Module
Analyzes customer sentiment, review distributions, NPS proxy score,
and response timelines.
"""

import pandas as pd
import numpy as np


def compute_review_distribution(df_reviews: pd.DataFrame) -> dict:
    """
    Computes overall ratings distribution and text comment rates.
    """
    valid = df_reviews.dropna(subset=["review_score"]).copy()
    total = len(valid)
    if total == 0:
        return {}

    dist = valid["review_score"].value_counts().sort_index().to_dict()
    dist_pct = {k: round(v / total * 100, 2) for k, v in dist.items()}

    has_comment = valid["review_comment_message"].notna().sum()
    comment_rate = round(has_comment / total * 100, 2)

    avg_score = round(valid["review_score"].mean(), 2)

    return {
        "total_reviews": total,
        "average_score": avg_score,
        "score_counts": dist,
        "score_percentages": dist_pct,
        "reviews_with_comments_pct": comment_rate,
    }


def compute_nps_proxy(df_reviews: pd.DataFrame) -> dict:
    """
    Calculates Net Promoter Score (NPS) proxy:
    - Promoters: 5 Stars
    - Passives: 4 Stars
    - Detractors: 1, 2, 3 Stars
    Formula: NPS = % Promoters - % Detractors
    """
    valid = df_reviews.dropna(subset=["review_score"]).copy()
    total = len(valid)
    if total == 0:
        return {}

    promoters = (valid["review_score"] == 5).sum()
    passives = (valid["review_score"] == 4).sum()
    detractors = (valid["review_score"] <= 3).sum()

    p_pct = round(promoters / total * 100, 2)
    pas_pct = round(passives / total * 100, 2)
    d_pct = round(detractors / total * 100, 2)

    nps = round(p_pct - d_pct, 1)

    return {
        "nps_score": nps,
        "promoters_pct": p_pct,
        "passives_pct": pas_pct,
        "detractors_pct": d_pct,
        "promoters_count": int(promoters),
        "passives_count": int(passives),
        "detractors_count": int(detractors)
    }
