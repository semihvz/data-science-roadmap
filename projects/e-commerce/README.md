# 🛍️ E-Commerce Data Analyst Portfolio Project

An end-to-end, production-grade **E-Commerce Analytics & Business Intelligence Engine** designed to solve key business challenges: Customer RFM Segmentation, Cohort Retention Heatmaps, Predictive Churn & Customer Lifetime Value (CLV), Product Category Performance, and Executive Reporting.

---

## 📌 Business Scenario & Objectives

Modern e-commerce platforms struggle with high customer acquisition costs (CAC) and post-purchase customer churn. This project provides a full-stack analytical solution for an e-commerce platform ("TrendyStyle"):

1. **Revenue Growth & Sales KPIs**: Track Monthly Recurring Revenue (MRR), Average Order Value (AOV), and Month-over-Month (MoM) growth rates.
2. **Customer Segmentation (RFM)**: Segment 1,200+ customers using Recency, Frequency, and Monetary scoring to identify Champions, At-Risk, and Lost customers.
3. **Cohort Retention Analysis**: Track customer retention curves across 24+ monthly cohorts to measure customer lifetime engagement.
4. **Predictive CLV & Churn Scoring**: Identify high-value customers likely to churn and estimate 12-month projected spend.
5. **Executive BI Dashboard**: Provide an interactive web dashboard (built with Streamlit & Plotly) for decision-makers.

---

## 🏗️ Project Architecture & Directory Structure

```text
projects/e-commerce/
├── README.md                          # Project Documentation
├── requirements.txt                   # Python Dependencies
├── sql/                               # Analytical SQL Modules
│   ├── schema.sql                     # SQLite Relational Database DDL Schema
│   ├── 01_kpi_metrics.sql             # Executive KPI & Sales Metrics
│   ├── 02_rfm_analysis.sql            # RFM Scoring using SQL NTILE() & Window Functions
│   ├── 03_cohort_analysis.sql         # Monthly Cohort Retention Aggregation Queries
│   └── 04_funnel_conversion.sql       # Acquisition Channel & Payment Conversion
├── src/                               # Python Analytical Engine
│   ├── generate_data.py               # Realistic E-Commerce Synthetic Data Generator
│   ├── rfm_analyzer.py                # RFM Segmentation Engine & Visualization Generator
│   ├── cohort_analyzer.py             # Cohort Matrix Builder & Heatmap Generator
│   ├── clv_churn_model.py             # Customer Lifetime Value & Churn Risk Assessor
│   └── run_pipeline.py                # Master Pipeline Execution Orchestrator
├── dashboard/                         # Web BI Dashboard
│   └── app.py                         # Streamlit Interactive Web Application
├── data/                              # Database & Raw Exports (Generated)
│   └── ecommerce.db                   # Relational SQLite Database
└── reports/                           # Output Reports & Visualizations
    ├── executive_summary.md           # Strategic Business Insights & Recommendations
    ├── rfm_distribution.png           # RFM Revenue Bar Chart
    ├── cohort_retention_heatmap.png   # Cohort Heatmap Visualization
    ├── rfm_segment_summary.csv        # Segment Stats Export
    └── customer_churn_clv_summary.csv # Individual Customer Risk Export
```

---

## 💾 Relational Database Schema (`sql/schema.sql`)

The database consists of 6 indexed relational tables:

- `customers`: Customer demography, acquisition channels, signup date, segment.
- `products`: Product catalog, categories, unit prices, cost prices, stock.
- `orders`: Order dates, status (Completed, Cancelled, Returned), total amounts, payment methods.
- `order_items`: Line item quantities, unit prices, total line item prices.
- `marketing_campaigns`: Campaign channels, budgets, date ranges.
- `customer_reviews`: Star ratings (1-5) and review text.

---

## 🚀 Quick Start Guide

### 1. Requirements Installation
Ensure Python 3.9+ is installed, then run:

```bash
pip install -r projects/e-commerce/requirements.txt
```

### 2. Run the Full Analytical Pipeline
To generate synthetic data, create the SQLite database, execute SQL analytics, run RFM & Cohort models, and save reports:

```bash
python3 projects/e-commerce/src/run_pipeline.py
```

### 3. Launch the Interactive Dashboard
To launch the Streamlit BI Dashboard in your web browser:

```bash
streamlit run projects/e-commerce/dashboard/app.py
```

---

## 📊 Key Analytical Methods & Insights

### 1. SQL Window Functions & CTEs
The SQL analytical scripts utilize advanced features:
- `NTILE(5) OVER (ORDER BY monetary ASC)` for quantile scoring.
- `JULIANDAY()` date math for recency tracking.
- `LAG()` and `OVER()` for Month-over-Month (MoM) revenue growth calculation.

### 2. RFM Segmentation Logic
- **Champions**: `R >= 4, F >= 4, M >= 4` -> Priority VIP engagement.
- **At Risk**: `R <= 2, F >= 3, M >= 3` -> High spenders who haven't ordered recently. Immediate win-back target.
- **Lost Customers**: `R <= 2, F <= 2, M <= 2` -> Low engagement, automated win-back sequence.

---

## 📄 Executive Report

Read the complete business analysis and leadership recommendations in [`reports/executive_summary.md`](./reports/executive_summary.md).
