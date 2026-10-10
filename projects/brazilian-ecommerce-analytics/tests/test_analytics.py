"""
Automated Test Suite for Brazilian E-Commerce Analytics
Verifies database integrity, views, and core analytical logic.
"""

import sys
import sqlite3
from pathlib import Path
import pytest
import pandas as pd

# Add src to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.analytics.sales_kpi import compute_overview_kpis, compute_monthly_sales_trend, compute_state_distribution
from src.analytics.rfm_segmentation import calculate_rfm_metrics, segment_customers, get_segment_summary
from src.analytics.logistics_sla import compute_logistics_kpis, analyze_regional_logistics, delay_impact_on_reviews
from src.analytics.product_intelligence import compute_category_pareto


@pytest.fixture(scope="session")
def db_conn():
    db_path = BASE_DIR / "data" / "olist.db"
    assert db_path.exists(), f"Database not found at {db_path}"
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def sample_orders_df(db_conn):
    # Fetch sample of vw_orders_summary
    query = "SELECT * FROM vw_orders_summary LIMIT 2000"
    df = pd.read_sql_query(query, db_conn)
    return df


@pytest.fixture(scope="session")
def category_df(db_conn):
    query = "SELECT * FROM vw_category_sales"
    df = pd.read_sql_query(query, db_conn)
    return df


def test_database_tables_exist(db_conn):
    cursor = db_conn.cursor()
    tables = [
        "customers", "sellers", "products", "orders",
        "order_items", "order_payments", "order_reviews", "geolocation"
    ]
    for table in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count > 0, f"Table {table} is empty!"


def test_analytical_views_exist(db_conn):
    cursor = db_conn.cursor()
    views = [
        "vw_orders_summary", "vw_customer_rfm_raw", "vw_category_sales",
        "vw_state_logistics", "vw_seller_performance"
    ]
    for view in views:
        count = cursor.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        assert count > 0, f"View {view} returned 0 rows!"


def test_sales_kpi_computation(sample_orders_df):
    kpis = compute_overview_kpis(sample_orders_df)
    assert kpis["total_orders"] == len(sample_orders_df)
    assert kpis["gross_revenue"] > 0
    assert 0 <= kpis["late_delivery_rate_pct"] <= 100
    assert 0 <= kpis["ontime_delivery_rate_pct"] <= 100
    assert abs(kpis["late_delivery_rate_pct"] + kpis["ontime_delivery_rate_pct"] - 100.0) < 0.1


def test_rfm_segmentation_logic(sample_orders_df):
    rfm = calculate_rfm_metrics(sample_orders_df)
    assert len(rfm) > 0
    assert "recency" in rfm.columns
    assert "frequency" in rfm.columns
    assert "monetary" in rfm.columns
    
    segmented = segment_customers(rfm)
    assert "segment" in segmented.columns
    segments = set(segmented["segment"].unique())
    assert len(segments) >= 2


def test_logistics_sla_logic(sample_orders_df):
    kpis = compute_logistics_kpis(sample_orders_df)
    assert "average_delivery_days" in kpis
    assert kpis["average_delivery_days"] > 0
    
    impact = delay_impact_on_reviews(sample_orders_df)
    assert len(impact) > 0


def test_category_pareto(category_df):
    pareto = compute_category_pareto(category_df)
    assert "cumulative_revenue_pct" in pareto.columns
    assert pareto.iloc[-1]["cumulative_revenue_pct"] == pytest.approx(100.0, abs=0.5)
    assert "abc_class" in pareto.columns
    assert "Class A (Core 80%)" in pareto["abc_class"].values
