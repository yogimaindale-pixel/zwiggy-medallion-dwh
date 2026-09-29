# Line-by-Line Breakdown: src/pipeline_runner.py

- **L1-L34**: Import `time`, `logging`, and managers (`BronzeLayerManager`, `SilverLayerManager`, `GoldLayerManager`).
- **L35-L45**: Initialize `ZwiggyPipelineRunner` class. Create database connection instance and instantiate Bronze, Silver, and Gold managers.
- **L46-L70**: Define `run_full_pipeline()`. Start execution timer, invoke `bronze_manager.run_bronze_ingestion()`, and log bronze ingestion metrics.
- **L71-L85**: Invoke `silver_manager.run_silver_transformations()`, cleansing raw JSON payloads into relational Silver tables.
- **L86-L99**: Invoke `gold_manager.run_gold_transformations()`, constructing analytical business data marts. Return pipeline execution summary dictionary.
