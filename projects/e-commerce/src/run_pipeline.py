import os
import sqlite3
import pandas as pd
from generate_data import generate_ecommerce_dataset
from rfm_analyzer import run_rfm_analysis
from cohort_analyzer import run_cohort_analysis
from clv_churn_model import calculate_clv_and_churn

def execute_sql_scripts(db_path="projects/e-commerce/data/ecommerce.db", sql_dir="projects/e-commerce/sql", output_dir="projects/e-commerce/reports"):
    print("📜 Executing Analytical SQL Queries...")
    os.makedirs(output_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)
    
    sql_files = [
        ("01_kpi_metrics.sql", "sql_kpi_metrics_output.csv"),
        ("02_rfm_analysis.sql", "sql_rfm_segments_output.csv"),
        ("03_cohort_analysis.sql", "sql_cohort_retention_output.csv"),
        ("04_funnel_conversion.sql", "sql_funnel_conversion_output.csv")
    ]

    for sql_file, csv_out in sql_files:
        filepath = os.path.join(sql_dir, sql_file)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                sql_content = f.read()
            
            # Extract first query or split by semicolon
            queries = [q.strip() for q in sql_content.split(";") if q.strip()]
            if queries:
                try:
                    df = pd.read_sql_query(queries[-1], conn)
                    out_path = os.path.join(output_dir, csv_out)
                    df.to_csv(out_path, index=False)
                    print(f"  ✓ Executed `{sql_file}` -> saved output to `{csv_out}`")
                except Exception as e:
                    print(f"  ⚠️ Warning running `{sql_file}`: {e}")

    conn.close()

def main():
    print("=" * 60)
    print("🚀 E-COMMERCE DATA ANALYST PIPELINE EXECUTOR")
    print("=" * 60)

    # 1. Generate Dataset
    generate_ecommerce_dataset()

    # 2. Run SQL Scripts
    execute_sql_scripts()

    # 3. RFM Analysis
    run_rfm_analysis()

    # 4. Cohort Analysis
    run_cohort_analysis()

    # 5. CLV & Churn Model
    calculate_clv_and_churn()

    print("\n🎉 All pipeline stages completed successfully!")
    print("📊 Generated artifacts can be found in `projects/e-commerce/reports/` and `projects/e-commerce/data/`.")

if __name__ == "__main__":
    main()
