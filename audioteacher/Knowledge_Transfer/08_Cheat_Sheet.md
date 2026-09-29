# ⚡ 08. Zwiggy Medallion DWH Cheat Sheet

| Operation | Command | Purpose |
| :--- | :--- | :--- |
| **Run Pipeline** | `python3 run_pipeline.py` | Executes Bronze, Silver, and Gold layers end-to-end. |
| **Seed Sample Data** | `python3 data/sample_data_generator.py` | Generates sample raw JSON files in `data/sample_raw_data/`. |
| **Run Tests** | `PYTHONPATH=. pytest tests/` | Runs automated test suite verifying layer row counts. |
