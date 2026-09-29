# Zwiggy Medallion Data Warehouse (`zwiggy-medallion-dwh`)

Production-ready 3-tier **Medallion Architecture Data Warehouse** built for **Zwiggy** (a food delivery & food-tech platform). Designed with exhaustive line-by-line commenting and beginner-friendly documentation to serve as a comprehensive reference for data engineers and junior developers.

---

## 🌟 Architecture Overview

The Zwiggy Medallion Data Warehouse organizes data into three distinct analytical layers:

```
                                  MEDALLION PIPELINE ARCHITECTURE
                                  
   +-------------------+       +-----------------------+       +-------------------------+
   |   BRONZE LAYER    |  -->  |     SILVER LAYER      |  -->  |       GOLD LAYER        |
   |   (Raw Ingestion) |       |  (Cleaned & Curated)  |       | (Analytics & Data Marts)|
   +-------------------+       +-----------------------+       +-------------------------+
   | • bronze_users    |       | • silver_users        |       | • gold_daily_restaurant_sales
   | • bronze_rest.    |       | • silver_restaurants  |       | • gold_user_analytics   |
   | • bronze_drivers  |       | • silver_drivers      |       | • gold_driver_metrics   |
   | • bronze_menu     |       | • silver_menu_items   |       | • gold_city_performance |
   | • bronze_orders   |       | • silver_orders       |       +-------------------------+
   | • bronze_payments |       | • silver_order_items  |
   +-------------------+       | • silver_payments     |
                               +-----------------------+
```

### Layer Breakdown:
1. **Bronze Layer (Raw Ingestion)**: Ingests raw JSON data files directly into database tables, preserving original JSON payloads verbatim along with audit metadata (`ingested_at`, `source_file`).
2. **Silver Layer (Cleaned & Curated)**: Parses JSON blobs, cleans text fields, casts numeric types, eliminates duplicate records using SQL window functions (`ROW_NUMBER()`), unnests order line items, and enforces relational integrity.
3. **Gold Layer (Business Aggregations & Marts)**: Computes pre-aggregated business KPIs and analytical metrics for business intelligence tools (e.g. Daily Restaurant Sales, Customer Lifetime Value & RFM Segmentation, Driver Ratings, and City Performance).

---

## 🚀 Quick-Start Guide

### Prerequisites
- **Python**: Version 3.8 or higher.
- **Dependencies**: Uses Python built-in standard libraries (`sqlite3`, `json`, `unittest`, `os`, `sys`, `datetime`). No external heavy dependencies required!

### Running the Pipeline
Execute the master pipeline runner from the root directory:

```bash
# Run the end-to-end Medallion pipeline (Bronze -> Silver -> Gold)
python3 run_pipeline.py

# Force-regenerate synthetic raw sample JSON data and execute pipeline
python3 run_pipeline.py --reset
```

### Running Automated Tests
Execute the unit and integration test suite:

```bash
python3 -m unittest tests/test_pipeline.py
```

---

## 📁 Repository Sitemap & Structure

```
zwiggy-medallion-dwh/
├── config/
│   ├── __init__.py
│   └── database_config.py      # Database settings, paths, and directory managers
├── data/
│   ├── sample_data_generator.py # Synthetic JSON data generator for Zwiggy platform
│   └── sample_raw_data/        # Generated raw JSON data (users, restaurants, orders, etc.)
├── src/
│   ├── __init__.py
│   ├── db_connection.py        # SQLite connection manager and SQL script runner
│   ├── bronze_layer.py         # Raw ingestion manager (Bronze schema and JSON loader)
│   ├── silver_layer.py         # Data cleansing and transformation manager
│   ├── gold_layer.py           # Business metrics aggregation and data mart manager
│   └── pipeline_runner.py      # Master pipeline orchestrator
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py        # Automated unit and integration test suite
├── DOCUMENTATION.md            # Technical specifications, table schemas, and business rules
├── KNOWLEDGE_TRANSFER.md       # Junior developer KT guide, core concepts, hands-on tutorials
├── README.md                   # Quick-start guide and architecture overview
└── run_pipeline.py             # Root CLI entrypoint script
```

---

## 📊 Summary Execution Metrics

| Pipeline Stage | Table Count | Total Records | Key Operations |
| :--- | :---: | :---: | :--- |
| **Bronze Layer** | 6 Tables | 84 Records | Raw JSON ingestion, UTC timestamp logging |
| **Silver Layer** | 7 Tables | 104 Records | Deduplication, type casting, array unnesting |
| **Gold Layer** | 4 Tables | 41 Summary Rows | Sales aggregations, RFM segmentation, City KPIs |
| **Test Suite** | 4 Tests | 100% Pass | Verified schema integrity, calculations, and row counts |

---

## 📚 Detailed Documentation & KT Guides

- 📖 **[DOCUMENTATION.md](file:///config/Desktop/Session1/zwiggy-medallion-dwh/DOCUMENTATION.md)**: Full technical specifications, database schema diagrams, data types, constraints, and business rules.
- 🎓 **[KNOWLEDGE_TRANSFER.md](file:///config/Desktop/Session1/zwiggy-medallion-dwh/KNOWLEDGE_TRANSFER.md)**: Beginner-friendly guide for junior developers explaining Medallion architecture, ETL concepts, code walkthroughs, and step-by-step hands-on tutorials.
