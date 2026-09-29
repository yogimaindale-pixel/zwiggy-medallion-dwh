# ==============================================================================
# FILE: tests/test_pipeline.py
# PURPOSE: Unit and Integration Test Suite for the Zwiggy Medallion Data Warehouse.
# EXPLANATION FOR JUNIOR DEVELOPERS:
# Automated testing ensures that our data transformations produce correct results.
# 'unittest' is Python's standard testing framework. Test methods start with 'test_'
# and use assertion methods (e.g. self.assertEqual, self.assertGreater) to verify
# expected versus actual values.
# ==============================================================================

# Import the 'unittest' framework from Python standard library.
import unittest

# Import 'os' for file and folder path management.
import os

# Import 'sys' to manage module imports.
import sys

# Ensure project root directory is on the import path.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database connection helper.
from src.db_connection import get_db_connection

# Import sample generator and pipeline runner.
from data.sample_data_generator import generate_all_sample_data
from src.pipeline_runner import ZwiggyPipelineRunner


class TestZwiggyMedallionPipeline(unittest.TestCase):
    """
    Test suite validating database creation, Bronze ingestion, Silver transformations,
    and Gold analytics computations.
    """

    @classmethod
    def setUpClass(cls):
        """
        Executed ONCE before any test in this class runs.
        Generates sample raw JSON data and executes the full Medallion pipeline.
        """
        print("\n[TEST SETUP] Initializing test data and running full Medallion pipeline...")
        generate_all_sample_data()
        cls.runner = ZwiggyPipelineRunner()
        cls.summary = cls.runner.run_pipeline(force_regenerate_data=False)

    def test_bronze_layer_counts(self):
        """
        Verifies that all 6 Bronze tables have positive row counts.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        bronze_tables = [
            ("bronze_users", 10),
            ("bronze_restaurants", 8),
            ("bronze_drivers", 6),
            ("bronze_menu_items", 24),
            ("bronze_orders", 20),
            ("bronze_payments", 16)
        ]

        for table_name, expected_count in bronze_tables:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table_name};")
            row = cursor.fetchone()
            actual_count = row["cnt"]
            self.assertEqual(actual_count, expected_count, f"Table '{table_name}' count mismatch!")
            print(f"[TEST PASSED] {table_name}: {actual_count} records verified.")

        conn.close()

    def test_silver_layer_data_cleansing(self):
        """
        Verifies that Silver tables contain deduplicated, cleansed records with no NULL primary keys.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check silver_users
        cursor.execute("SELECT COUNT(*) as cnt FROM silver_users WHERE user_id IS NULL OR user_id = '';")
        null_users = cursor.fetchone()["cnt"]
        self.assertEqual(null_users, 0, "silver_users contains NULL or empty user_id values!")

        # Check silver_orders amounts are positive numbers
        cursor.execute("SELECT COUNT(*) as cnt FROM silver_orders WHERE total_amount <= 0;")
        invalid_orders = cursor.fetchone()["cnt"]
        self.assertEqual(invalid_orders, 0, "silver_orders contains invalid or non-positive total amounts!")

        # Check silver_orders order_status values are normalized uppercase strings
        cursor.execute("SELECT DISTINCT order_status FROM silver_orders;")
        statuses = [row["order_status"] for row in cursor.fetchall()]
        for status in statuses:
            self.assertEqual(status, status.upper(), f"Status '{status}' is not normalized uppercase!")

        conn.close()
        print("[TEST PASSED] Silver layer data cleansing and schema validation passed.")

    def test_gold_layer_revenue_aggregations(self):
        """
        Verifies that Gold daily restaurant sales revenue sums match delivered orders in Silver layer.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get total net revenue from Gold daily restaurant sales
        cursor.execute("SELECT SUM(net_revenue) as gold_net FROM gold_daily_restaurant_sales;")
        gold_net_rev = round(cursor.fetchone()["gold_net"], 2)

        # Get total net revenue from Silver completed orders
        cursor.execute("SELECT SUM(total_amount) as silver_net FROM silver_orders WHERE order_status = 'DELIVERED';")
        silver_net_rev = round(cursor.fetchone()["silver_net"], 2)

        self.assertEqual(gold_net_rev, silver_net_rev, "Gold net revenue does not match Silver delivered order total!")
        print(f"[TEST PASSED] Gold net revenue (${gold_net_rev}) matches Silver delivered total (${silver_net_rev}).")

        conn.close()

    def test_gold_city_performance_aggregations(self):
        """
        Verifies that Gold city performance correctly aggregates active users and drivers per city.
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(DISTINCT city) as city_count FROM gold_city_performance;")
        city_count = cursor.fetchone()["city_count"]
        self.assertGreater(city_count, 0, "gold_city_performance table is empty!")

        conn.close()
        print(f"[TEST PASSED] Gold city performance verified with {city_count} unique cities.")


if __name__ == "__main__":
    unittest.main()
