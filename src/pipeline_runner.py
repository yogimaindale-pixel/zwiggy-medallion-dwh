# ==============================================================================
# FILE: src/pipeline_runner.py
# PURPOSE: Master Orchestrator for the Zwiggy Medallion Data Warehouse Pipeline.
# EXPLANATION FOR JUNIOR DEVELOPERS:
# Pipeline orchestration means coordinating multiple data processing tasks in a
# strict sequence. If step 1 (Bronze Ingestion) fails, step 2 (Silver Cleansing)
# should not run. This module manages execution order, measures runtimes,
# and prints formatted execution summaries.
# ==============================================================================

# Import 'os' for file path checking.
import os

# Import 'sys' to manage module imports.
import sys

# Import 'time' to measure execution duration in seconds.
import time

# Ensure root directory is on module search path.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import central database configuration.
from config.database_config import RAW_DATA_DIR, DB_PATH

# Import sample raw data generator.
from data.sample_data_generator import generate_all_sample_data

# Import Medallion layer managers.
from src.bronze_layer import BronzeLayerManager
from src.silver_layer import SilverLayerManager
from src.gold_layer import GoldLayerManager


class ZwiggyPipelineRunner:
    """
    Orchestrates end-to-end execution of Bronze, Silver, and Gold layers.
    """

    def __init__(self, raw_data_dir=RAW_DATA_DIR, db_path=DB_PATH):
        """
        Initializes the pipeline runner.
        """
        self.raw_data_dir = raw_data_dir
        self.db_path = db_path
        self.bronze_mgr = BronzeLayerManager(raw_data_dir=self.raw_data_dir)
        self.silver_mgr = SilverLayerManager()
        self.gold_mgr = GoldLayerManager()

    def run_pipeline(self, force_regenerate_data=False):
        """
        Executes the complete Medallion pipeline end-to-end.
        
        Parameters:
            force_regenerate_data (bool): If True, regenerates raw sample JSON files before running.
            
        Returns:
            dict: Comprehensive execution metrics and layer statistics.
        """
        start_time = time.time()
        print("======================================================================")
        print("     STARTING ZWIGGY MEDALLION DATA WAREHOUSE PIPELINE RUNNER       ")
        print("======================================================================")

        # Step 0: Verify raw input JSON data files exist.
        if force_regenerate_data or not os.path.exists(self.raw_data_dir) or len(os.listdir(self.raw_data_dir)) == 0:
            print("[PIPELINE STEP 0] Generating raw sample dataset...")
            generate_all_sample_data()

        # Step 1: Run Bronze Layer (Raw Ingestion).
        print("\n--- [STEP 1/3] EXECUTING BRONZE LAYER INGESTION ---")
        bronze_stats = self.bronze_mgr.run_full_bronze_ingestion()

        # Step 2: Run Silver Layer (Cleansing & Transformation).
        print("\n--- [STEP 2/3] EXECUTING SILVER LAYER TRANSFORMATIONS ---")
        silver_stats = self.silver_mgr.run_full_silver_transformation()

        # Step 3: Run Gold Layer (Business Aggregations).
        print("\n--- [STEP 3/3] EXECUTING GOLD LAYER DATA MARTS ---")
        gold_stats = self.gold_mgr.run_full_gold_aggregation()

        elapsed_time = round(time.time() - start_time, 3)

        pipeline_summary = {
            "execution_time_seconds": elapsed_time,
            "bronze": bronze_stats,
            "silver": silver_stats,
            "gold": gold_stats
        }

        print("\n======================================================================")
        print(f"  PIPELINE COMPLETED SUCCESSFULLY IN {elapsed_time} SECONDS          ")
        print("======================================================================")
        print(f" Bronze Tables Populated: {len(bronze_stats)}")
        print(f" Silver Tables Populated: {len(silver_stats)}")
        print(f" Gold Tables Populated:   {len(gold_stats)}")
        print("======================================================================\n")

        return pipeline_summary


if __name__ == "__main__":
    runner = ZwiggyPipelineRunner()
    runner.run_pipeline(force_regenerate_data=True)
