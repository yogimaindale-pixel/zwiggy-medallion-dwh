# 📌 01. Zwiggy Medallion DWH - Repository Overview

## 🎯 Problem Statement & Business Context
For hyper-local food delivery platforms like Zwiggy, operational databases experience thousands of concurrent writes per minute across users, restaurants, drivers, menu items, orders, and payments. Querying operational OLTP databases directly for daily restaurant sales, user cohort retention, or city performance causes database locks and severe checkout latency.

This repository implements a production-grade **Medallion Data Warehouse Architecture** in SQLite/Python that decouples operational data from analytics through Bronze raw ingestion, Silver data cleansing, and Gold business marts.

---

## 🏗️ Architecture Overview

- **Bronze Layer (`src/bronze_layer.py`)**: Appends raw JSON records into `bronze_users`, `bronze_restaurants`, `bronze_drivers`, `bronze_menu_items`, `bronze_orders`, and `bronze_payments` with extraction metadata (`ingestion_timestamp`, `raw_payload`).
- **Silver Layer (`src/silver_layer.py`)**: Cleanses raw JSON strings into structured, type-cast relational tables, enforcing email validation, phone standardization, currency formatting, and default null handling.
- **Gold Layer (`src/gold_layer.py`)**: Constructs analytical aggregation data marts (`gold_daily_restaurant_sales`, `gold_user_analytics`, `gold_driver_metrics`, `gold_city_performance`).

---

## 🛠️ Technology Stack
- **Language**: Python 3.10+
- **Database Engine**: SQLite 3 (via `sqlite3` standard library with `ROW_FACTORY = sqlite3.Row`)
- **Pipeline Runner**: `ZwiggyPipelineRunner` (`src/pipeline_runner.py`)
- **Testing**: `pytest` (`tests/test_pipeline.py`)
