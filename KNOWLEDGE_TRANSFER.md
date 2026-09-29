# Zwiggy Medallion Data Warehouse — Knowledge Transfer (KT) Guide (`KNOWLEDGE_TRANSFER.md`)

Welcome to the **Zwiggy Medallion Data Warehouse** Knowledge Transfer (KT) Guide! This document is specifically written for junior developers, data engineering interns, and new team members joining the Zwiggy data engineering team.

---

## 💡 1. Core Concepts Explained Simply

### 1.1 What is a Data Warehouse?
A **Data Warehouse (DWH)** is a central database designed specifically for **reporting, business intelligence (BI), and analytics**, rather than real-time transactional app operations. 

- **OLTP (Online Transaction Processing)**: Operational databases (like PostgreSQL or MongoDB) used by the Zwiggy mobile app to quickly process single food orders.
- **OLAP (Online Analytical Processing)**: Analytical data warehouses (like our Medallion SQLite warehouse) used to calculate monthly sales trends, customer churn rates, and driver performance across millions of historical records.

---

### 1.2 What is a Medallion Architecture?
A **Medallion Architecture** organizes data into three quality tiers:

1. 🥉 **Bronze Layer (Raw Ingestion)**:
   - **Analogy**: The raw delivery inbox.
   - **What happens**: Stores incoming raw JSON payload files directly from source APIs without editing anything. Includes metadata like `ingested_at` timestamp.
   
2. 🥈 **Silver Layer (Cleaned & Curated)**:
   - **Analogy**: The organized pantry.
   - **What happens**: Parses JSON strings into clean columns, fixes missing values, removes duplicates (`ROW_NUMBER()`), normalizes uppercase status strings, and splits nested arrays (e.g. order items).

3. 🥇 **Gold Layer (Aggregated Business Marts)**:
   - **Analogy**: The prepared gourmet meal served to executives.
   - **What happens**: Runs SQL `GROUP BY` aggregations to build fast data marts (e.g., daily sales, customer lifetime value, driver metrics, city revenue).

---

### 1.3 What is Idempotency?
An operation is **idempotent** if running it multiple times produces the exact same result as running it once.
- In our pipeline, every processing function truncates (`DELETE FROM table`) old processed data before inserting fresh records. This means if a pipeline fails halfway through, you can safely re-run `python3 run_pipeline.py` without creating duplicate records or corrupted stats!

---

## 🗺️ 2. Codebase Sitemap & File Walkthrough

Here is a map of every single file in the project and what it does:

| Path | Purpose | Key Functions / Classes |
| :--- | :--- | :--- |
| `config/database_config.py` | Central configuration file for paths & DB name | `DB_PATH`, `RAW_DATA_DIR`, `ensure_directories_exist()` |
| `src/db_connection.py` | Manages SQLite connections and cursors | `get_db_connection()`, `get_db_cursor()`, `execute_sql_script()` |
| `data/sample_data_generator.py` | Generates synthetic Zwiggy raw JSON datasets | `generate_all_sample_data()` |
| `src/bronze_layer.py` | Raw data ingestion into Bronze tables | `BronzeLayerManager`, `ingest_json_file()` |
| `src/silver_layer.py` | Data cleansing, deduplication, & Silver tables | `SilverLayerManager`, `process_silver_orders_and_items()` |
| `src/gold_layer.py` | Business metrics aggregation into Gold data marts | `GoldLayerManager`, `process_gold_daily_restaurant_sales()` |
| `src/pipeline_runner.py` | Master orchestrator coordinating Bronze $\rightarrow$ Silver $\rightarrow$ Gold | `ZwiggyPipelineRunner`, `run_pipeline()` |
| `run_pipeline.py` | Command-line interface entry point script | `main()` |
| `tests/test_pipeline.py` | Automated unit and integration test suite | `TestZwiggyMedallionPipeline` |

---

## 🛠️ 3. Step-by-Step Hands-On Tutorials

### Tutorial 1: Executing the Data Pipeline Locally

To run the pipeline from scratch on your local machine:

1. Open your terminal in the project root folder (`zwiggy-medallion-dwh`).
2. Run the command:
   ```bash
   python3 run_pipeline.py --reset
   ```
3. You will see colored output logging each layer's execution:
   - `[DATA GEN]`: Creates sample JSON files in `data/sample_raw_data/`.
   - `[BRONZE]`: Ingests 6 raw tables.
   - `[SILVER]`: Cleans and populates 7 curated tables.
   - `[GOLD]`: Computes 4 analytical data marts.

---

### Tutorial 2: Inspecting Database Tables with SQLite CLI or Python

You can inspect the generated SQLite database directly in Python:

```python
import sqlite3

# Connect to local database file
conn = sqlite3.connect("data/zwiggy_dwh.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Query top daily restaurant sales from Gold layer
cursor.execute("SELECT restaurant_name, net_revenue, avg_order_value FROM gold_daily_restaurant_sales ORDER BY net_revenue DESC LIMIT 5;")
for row in cursor.fetchall():
    print(f"Restaurant: {row['restaurant_name']} | Revenue: ₹{row['net_revenue']} | AOV: ₹{row['avg_order_value']}")

conn.close()
```

---

### Tutorial 3: Adding a New Field to the Pipeline

Suppose Zwiggy adds a `loyalty_points` field to customer accounts. Here is how you would add it:

1. **Update Sample Generator** (`data/sample_data_generator.py`):
   Add `"loyalty_points": i * 50` inside `users_data`.
2. **Update Bronze Layer** (`src/bronze_layer.py`):
   Bronze stores `raw_json` as a complete blob, so Bronze automatically captures the new field!
3. **Update Silver Schema** (`src/silver_layer.py`):
   - Add `loyalty_points INTEGER DEFAULT 0` to `CREATE TABLE IF NOT EXISTS silver_users`.
   - Update `process_silver_users()` SQL query to extract `json_extract(raw_json, '$.loyalty_points')`.
4. **Update Gold Metrics** (`src/gold_layer.py`):
   - Use `silver_users.loyalty_points` in customer segmentation logic if desired.
5. **Run Tests**:
   Execute `python3 -m unittest tests/test_pipeline.py` to ensure all tests pass!

---

### Tutorial 4: Running Automated Tests

Run the test suite to verify pipeline health:

```bash
python3 -m unittest tests/test_pipeline.py
```

Expected Output:
```text
Ran 4 tests in 0.138s

OK
```

---

## ❓ 4. Frequently Asked Questions (FAQ)

### Q1: Why use SQLite instead of PostgreSQL or Snowflake?
**Answer**: For local development, prototyping, and testing, SQLite is fast, zero-configuration, and stores everything in a single portable file (`zwiggy_dwh.db`). The SQL code written here uses standard ANSI SQL (`ROW_NUMBER()`, CTEs `WITH ... AS`, aggregations) which ports directly to Databricks, BigQuery, or Snowflake in production.

### Q2: How does deduplication work if duplicate JSON records are ingested twice?
**Answer**: In `src/silver_layer.py`, we use the `ROW_NUMBER()` window function partitioned by entity ID and ordered by `record_id DESC`. This assigns `1` to the most recently ingested record and ignores older duplicate records.

### Q3: What happens if an order has status `CANCELLED`?
**Answer**:
- In `silver_orders`, the order is recorded with `order_status = 'CANCELLED'`.
- In `gold_daily_restaurant_sales`, `gross_revenue` includes all orders, but `net_revenue` only sums orders where `order_status = 'DELIVERED'`. `cancelled_orders` count is incremented, and `cancellation_rate` is computed automatically.
