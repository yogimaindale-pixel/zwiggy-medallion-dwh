# 🗺️ 04. Master File, Function, and Line Range Mapping Matrix

| Concept | Target File | Class / Function | Start Line | End Line | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pipeline Runner** | `run_pipeline.py` | `main` | 23 | 38 | CLI entrypoint executing the 3-stage Medallion pipeline. |
| **DB Connection** | `src/db_connection.py` | `get_db_cursor` | 54 | 85 | Transaction wrapper providing sqlite3 dict cursors. |
| **Bronze Layer** | `src/bronze_layer.py` | `BronzeLayerManager` | 33 | 209 | Ingests raw JSON files into Bronze landing tables. |
| **Silver Layer** | `src/silver_layer.py` | `SilverLayerManager` | 30 | 542 | Cleanses raw JSON into structured Silver tables. |
| **Gold Layer** | `src/gold_layer.py` | `GoldLayerManager` | 28 | 375 | Builds analytical business data marts for BI dashboards. |
| **Pipeline Orchestrator**| `src/pipeline_runner.py`| `ZwiggyPipelineRunner`| 35 | 99 | Coordinates Bronze, Silver, and Gold execution sequence. |
| **Sample Data Seeder** | `data/sample_data_generator.py`| `generate_all_sample_data`| 32 | 229 | Generates synthetic JSON files for users, orders, and payments. |
