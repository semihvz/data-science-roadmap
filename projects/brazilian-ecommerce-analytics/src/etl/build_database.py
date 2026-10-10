"""
ETL Pipeline: Olist Brazilian E-Commerce
Extracts raw CSV files, performs data cleaning, normalizes schemas,
creates optimized SQLite relational database (olist.db), builds indexes and analytical views.
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("OlistETL")

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_PATH = BASE_DIR / "data" / "olist.db"
SQL_DIR = BASE_DIR / "sql"


def check_or_download_data():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    required = RAW_DIR / "olist_orders_dataset.csv"
    if not required.exists():
        logger.info("Raw CSV files not found. Downloading via Kaggle API...")
        os.system(f"kaggle datasets download -d olistbr/brazilian-ecommerce -p '{RAW_DIR}' --unzip")


def run_etl():
    logger.info(f"Starting ETL Pipeline. Base dir: {BASE_DIR}")
    check_or_download_data()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    if DB_PATH.exists():
        logger.info(f"Removing existing database at {DB_PATH}")
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Execute DDL Schema
    schema_file = SQL_DIR / "schema.sql"
    logger.info(f"Executing schema definition from {schema_file}")
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    conn.commit()

    # 2. Ingest Customers
    logger.info("Ingesting Customers...")
    df_customers = pd.read_csv(RAW_DIR / "olist_customers_dataset.csv")
    df_customers.drop_duplicates(subset=["customer_id"], inplace=True)
    df_customers.to_sql("customers", conn, if_exists="append", index=False)
    logger.info(f"Customers ingested: {len(df_customers):,} rows")

    # 3. Ingest Sellers
    logger.info("Ingesting Sellers...")
    df_sellers = pd.read_csv(RAW_DIR / "olist_sellers_dataset.csv")
    df_sellers.drop_duplicates(subset=["seller_id"], inplace=True)
    df_sellers.to_sql("sellers", conn, if_exists="append", index=False)
    logger.info(f"Sellers ingested: {len(df_sellers):,} rows")

    # 4. Ingest Products with English Category Names
    logger.info("Ingesting Products and Category Translations...")
    df_products = pd.read_csv(RAW_DIR / "olist_products_dataset.csv")
    df_trans = pd.read_csv(RAW_DIR / "product_category_name_translation.csv")
    df_products = df_products.merge(df_trans, on="product_category_name", how="left")
    
    # Fill missing translation with original or 'unknown'
    df_products["product_category_name_english"] = df_products["product_category_name_english"].fillna(
        df_products["product_category_name"].fillna("unknown")
    )
    df_products.drop_duplicates(subset=["product_id"], inplace=True)
    df_products.to_sql("products", conn, if_exists="append", index=False)
    logger.info(f"Products ingested: {len(df_products):,} rows")

    # 5. Ingest Orders
    logger.info("Ingesting Orders...")
    df_orders = pd.read_csv(RAW_DIR / "olist_orders_dataset.csv")
    df_orders.drop_duplicates(subset=["order_id"], inplace=True)
    df_orders.to_sql("orders", conn, if_exists="append", index=False)
    logger.info(f"Orders ingested: {len(df_orders):,} rows")

    # 6. Ingest Order Items
    logger.info("Ingesting Order Items...")
    df_order_items = pd.read_csv(RAW_DIR / "olist_order_items_dataset.csv")
    df_order_items.drop_duplicates(subset=["order_id", "order_item_id"], inplace=True)
    df_order_items.to_sql("order_items", conn, if_exists="append", index=False)
    logger.info(f"Order Items ingested: {len(df_order_items):,} rows")

    # 7. Ingest Order Payments
    logger.info("Ingesting Order Payments...")
    df_payments = pd.read_csv(RAW_DIR / "olist_order_payments_dataset.csv")
    df_payments.drop_duplicates(subset=["order_id", "payment_sequential"], inplace=True)
    df_payments.to_sql("order_payments", conn, if_exists="append", index=False)
    logger.info(f"Order Payments ingested: {len(df_payments):,} rows")

    # 8. Ingest Order Reviews
    logger.info("Ingesting Order Reviews...")
    df_reviews = pd.read_csv(RAW_DIR / "olist_order_reviews_dataset.csv")
    # Clean possible duplicate review_id + order_id pairs
    df_reviews.drop_duplicates(subset=["review_id", "order_id"], inplace=True)
    df_reviews.to_sql("order_reviews", conn, if_exists="append", index=False)
    logger.info(f"Order Reviews ingested: {len(df_reviews):,} rows")

    # 9. Ingest Deduplicated Geolocation
    logger.info("Processing & Ingesting Geolocation (deduplicating 1M+ rows to zip centroid)...")
    df_geo = pd.read_csv(RAW_DIR / "olist_geolocation_dataset.csv")
    df_geo_agg = df_geo.groupby("geolocation_zip_code_prefix").agg({
        "geolocation_lat": "mean",
        "geolocation_lng": "mean",
        "geolocation_city": "first",
        "geolocation_state": "first"
    }).reset_index()
    df_geo_agg.to_sql("geolocation", conn, if_exists="append", index=False)
    logger.info(f"Geolocation ingested: {len(df_geo_agg):,} unique zip codes")

    # 10. Execute Analytical Views
    views_file = SQL_DIR / "analytical_views.sql"
    logger.info(f"Creating Analytical Views from {views_file}")
    with open(views_file, "r", encoding="utf-8") as f:
        views_sql = f.read()
    cursor.executescript(views_sql)
    conn.commit()

    # 11. Verification and Sanity Check
    logger.info("Verifying tables and view row counts:")
    tables = [
        "customers", "sellers", "products", "orders", "order_items",
        "order_payments", "order_reviews", "geolocation"
    ]
    for table in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        logger.info(f"  ✓ {table}: {count:,} rows")

    views = ["vw_orders_summary", "vw_customer_rfm_raw", "vw_category_sales", "vw_state_logistics", "vw_seller_performance"]
    for view in views:
        count = cursor.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        logger.info(f"  ✓ {view}: {count:,} rows")

    # 12. Create fast parquet snapshots for Python analytical modules
    logger.info("Generating fast Parquet caches in data/processed/...")
    df_orders_summary = pd.read_sql_query("SELECT * FROM vw_orders_summary", conn)
    df_orders_summary.to_parquet(PROCESSED_DIR / "orders_summary.parquet", index=False)

    df_rfm_raw = pd.read_sql_query("SELECT * FROM vw_customer_rfm_raw", conn)
    df_rfm_raw.to_parquet(PROCESSED_DIR / "customer_rfm_raw.parquet", index=False)

    df_category = pd.read_sql_query("SELECT * FROM vw_category_sales", conn)
    df_category.to_parquet(PROCESSED_DIR / "category_sales.parquet", index=False)

    conn.close()
    logger.info("ETL Pipeline completed successfully! Database ready at data/olist.db")


if __name__ == "__main__":
    run_etl()
