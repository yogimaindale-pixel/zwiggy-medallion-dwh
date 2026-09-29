# ❓ 07. Technical Interview Questions & Spoken Response Bank

### Q1: Why use a Medallion Data Architecture for food delivery analytics?
- **30-Second Pitch**: Medallion architecture decouples raw JSON ingestion in Bronze from cleansed tables in Silver and business metrics in Gold, preventing operational OLTP database locks.
- **Spoken Response**: "We implemented the Medallion Data Architecture to isolate heavy analytical queries from Zwiggy's transactional database. Bronze acts as an append-only raw JSON landing zone. Silver decodes JSON, standardizes data types, and enforces data quality constraints. Gold aggregates daily sales, driver performance, and customer retention metrics into Star Schema marts. This ensures raw data auditability while delivering sub-second query performance for BI dashboards."
