# 💡 03. Core Engineering Concepts & Pattern Cards

### Concept 1: Medallion Architecture (Bronze -> Silver -> Gold)
- **What is it?**: A data design pattern that logically organizes data into three layers of increasing quality.
- **Why needed?**: Guarantees raw data auditability while delivering high-speed analytical data marts.
- **Repository Implementation**: `src/bronze_layer.py`, `src/silver_layer.py`, `src/gold_layer.py`.

### Concept 2: Context Manager Database Connection
- **What is it?**: Using Python context managers (`@contextmanager`) to manage SQLite connections and automatically commit or rollback transactions.
- **Repository Implementation**: `src/db_connection.py` (`get_db_connection`, `get_db_cursor`).

### Concept 3: Analytical Data Mart Pre-aggregation
- **What is it?**: Pre-computing complex aggregations (`SUM`, `AVG`, `COUNT`) into Gold tables so BI dashboards query ready results instantly.
- **Repository Implementation**: `src/gold_layer.py`.
