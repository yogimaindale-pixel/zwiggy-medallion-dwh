# ==============================================================================
# FILE: run_pipeline.py
# PURPOSE: Root execution CLI script for the Zwiggy Medallion Data Warehouse.
# EXPLANATION FOR JUNIOR DEVELOPERS:
# This script serves as the primary entry point for command-line execution.
# Developers and automated schedulers (e.g. Cron or Airflow) can run this file
# directly using 'python3 run_pipeline.py'.
# ==============================================================================

# Import 'sys' to access command-line arguments and system path.
import sys

# Import 'os' to format file paths.
import os

# Add root directory path to Python module search paths.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main pipeline orchestrator from src/pipeline_runner.py.
from src.pipeline_runner import ZwiggyPipelineRunner


def main():
    """
    Main function executed when calling 'python3 run_pipeline.py'.
    Parses CLI flags (e.g. '--reset') and triggers full pipeline execution.
    """
    # Check if the user passed '--reset' flag to force regeneration of raw sample files.
    force_reset = "--reset" in sys.argv

    # Instantiate the pipeline runner.
    runner = ZwiggyPipelineRunner()

    # Execute the end-to-end Medallion data warehouse pipeline.
    summary = runner.run_pipeline(force_regenerate_data=force_reset)

    # Print clean exit message.
    print("[RUN COMPLETE] Summary stats:", summary)


if __name__ == "__main__":
    main()
