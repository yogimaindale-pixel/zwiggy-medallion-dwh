# 🐣 09. Beginner Tutorial: Zwiggy Medallion Pipeline

Welcome to the beginner hands-on guide for **Zwiggy Medallion Data Warehouse**!

### Step 1: Run the Pipeline
```bash
python3 run_pipeline.py
```

### Step 2: Inspect Database Output
```python
import sqlite3

conn = sqlite3.connect('data/zwiggy_dwh.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM gold_daily_restaurant_sales LIMIT 5")
print(cursor.fetchall())
```
