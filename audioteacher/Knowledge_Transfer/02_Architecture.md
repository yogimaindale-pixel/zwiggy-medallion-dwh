# 🏛️ 02. Zwiggy Medallion DWH - Architecture Deep Dive

## Medallion Architecture Specification

### Bronze Raw Landing
- Stores unmodified JSON strings in a single `raw_payload TEXT` column.
- Appends `ingestion_timestamp` and `source_filename`.
- Prevents data loss if source API or database schema changes unexpectedly.

### Silver Cleansed Layer
- Decodes JSON payloads using `json.loads()`.
- Validates mandatory primary keys and handles corrupt/missing fields.
- Casts strings to native SQLite data types (`INTEGER`, `REAL`, `TIMESTAMP`).

### Gold Business Marts
- Aggregates metrics across dimensions (Restaurant, User, Driver, City).
- Pre-calculates Key Performance Indicators (KPIs) like Gross Merchandise Value (GMV), average delivery time, and customer lifetime order count.
