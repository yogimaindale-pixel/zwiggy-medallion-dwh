# ==============================================================================
# FILE: src/bronze_layer.py
# PURPOSE: Implements the Bronze Layer (Raw Data Ingestion) of the Data Warehouse.
# EXPLANATION FOR JUNIOR DEVELOPERS:
# The Bronze layer is the first tier in a Medallion Architecture. Its main purpose
# is to store raw, unmodified data exactly as received from external source systems.
# We include metadata columns like 'ingested_at' and 'source_file' so we have a full
# audit log showing when and where each piece of data originated.
# ==============================================================================

# Import 'json' to parse raw JSON files into Python lists and dictionaries.
import json

# Import 'os' for file and directory path manipulations.
import os

# Import 'sys' to manage module search paths.
import sys

# Import 'datetime' and 'timezone' to record UTC timestamps during data ingestion.
from datetime import datetime, timezone

# Ensure the root project path is accessible for configuration imports.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database connection helper functions from src/db_connection.py.
from src.db_connection import get_db_connection, execute_sql_script

# Import RAW_DATA_DIR path from config/database_config.py.
from config.database_config import RAW_DATA_DIR


class BronzeLayerManager:
    """
    Manages the creation of Bronze tables and the ingestion of raw JSON files
    into the SQLite database.
    """

    def __init__(self, raw_data_dir=RAW_DATA_DIR):
        """
        Initializes the BronzeLayerManager instance with the path to raw input data.
        
        Parameters:
            raw_data_dir (str): Directory path containing source JSON files.
        """
        # Store the directory path as an instance attribute.
        self.raw_data_dir = raw_data_dir

    def create_bronze_tables(self):
        """
        Executes DDL (Data Definition Language) SQL commands to build all Bronze tables.
        If tables already exist, they are preserved or recreated cleanly.
        """
        # Define SQL statements to create Bronze schema tables.
        # Storing 'raw_json' as TEXT allows storing complete nested JSON payloads verbatim.
        sql_ddl = """
        -- Table for raw user profile records
        CREATE TABLE IF NOT EXISTS bronze_users (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_user_id TEXT,
            raw_json TEXT NOT NULL,
            source_file TEXT NOT NULL,
            ingested_at TEXT NOT NULL
        );

        -- Table for raw restaurant records
        CREATE TABLE IF NOT EXISTS bronze_restaurants (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_restaurant_id TEXT,
            raw_json TEXT NOT NULL,
            source_file TEXT NOT NULL,
            ingested_at TEXT NOT NULL
        );

        -- Table for raw delivery partner records
        CREATE TABLE IF NOT EXISTS bronze_drivers (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_driver_id TEXT,
            raw_json TEXT NOT NULL,
            source_file TEXT NOT NULL,
            ingested_at TEXT NOT NULL
        );

        -- Table for raw menu item records
        CREATE TABLE IF NOT EXISTS bronze_menu_items (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_item_id TEXT,
            raw_json TEXT NOT NULL,
            source_file TEXT NOT NULL,
            ingested_at TEXT NOT NULL
        );

        -- Table for raw customer order records
        CREATE TABLE IF NOT EXISTS bronze_orders (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_order_id TEXT,
            raw_json TEXT NOT NULL,
            source_file TEXT NOT NULL,
            ingested_at TEXT NOT NULL
        );

        -- Table for raw payment transaction records
        CREATE TABLE IF NOT EXISTS bronze_payments (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_payment_id TEXT,
            raw_json TEXT NOT NULL,
            source_file TEXT NOT NULL,
            ingested_at TEXT NOT NULL
        );
        """
        # Call execute_sql_script to run the multiline DDL string on our database.
        execute_sql_script(sql_ddl)
        print("[BRONZE] Created all Bronze layer raw ingestion tables.")

    def ingest_json_file(self, filename, table_name, id_key_name):
        """
        Reads a raw JSON file from disk and inserts each record into a Bronze table.
        
        Parameters:
            filename (str): Name of the JSON file inside raw_data_dir (e.g. 'users.json').
            table_name (str): Name of the target Bronze table (e.g. 'bronze_users').
            id_key_name (str): Key name used to extract the record ID (e.g. 'user_id').
            
        Returns:
            int: Total number of records successfully ingested into the table.
        """
        # Construct the full filesystem path to the target JSON file.
        file_path = os.path.join(self.raw_data_dir, filename)

        # Check if the file exists before attempting to read it.
        if not os.path.exists(file_path):
            print(f"[BRONZE WARNING] File '{filename}' not found at path '{file_path}'. Skipping.")
            return 0

        # Open the JSON file in read mode ('r') with UTF-8 character encoding.
        with open(file_path, "r", encoding="utf-8") as f:
            # 'json.load' converts the JSON string from the file into a Python list of dicts.
            records = json.load(f)

        # Obtain the current UTC timestamp formatted as ISO-8601 string (e.g. 2026-09-29T10:00:00Z).
        current_utc_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Open a database connection to perform data insertion.
        conn = get_db_connection()
        cursor = conn.cursor()

        # Truncate existing data in the Bronze table to ensure clean ingestion idempotency.
        cursor.execute(f"DELETE FROM {table_name};")

        # Track the total inserted record count.
        inserted_count = 0

        # Prepare parameterized INSERT statement SQL query.
        # Parameterized queries ('?') prevent SQL injection vulnerabilities and handle quotes safely.
        insert_sql = f"""
            INSERT INTO {table_name} (raw_{id_key_name}, raw_json, source_file, ingested_at)
            VALUES (?, ?, ?, ?);
        """

        # Iterate through each dictionary record in the loaded JSON array.
        for item in records:
            # Extract the raw entity ID (e.g. 'USR_001') if present in the record.
            raw_id = item.get(id_key_name, None)

            # Convert the entire dictionary back into a compact JSON string format.
            raw_json_str = json.dumps(item)

            # Execute the INSERT query with tuple parameters.
            cursor.execute(insert_sql, (raw_id, raw_json_str, filename, current_utc_timestamp))
            inserted_count += 1

        # Commit all inserted rows to save changes permanently.
        conn.commit()

        # Close the connection.
        conn.close()

        print(f"[BRONZE] Ingested {inserted_count} records from '{filename}' into table '{table_name}'.")
        return inserted_count

    def run_full_bronze_ingestion(self):
        """
        Orchestrates the creation of Bronze tables and ingests all 6 raw JSON datasets.
        
        Returns:
            dict: Summary mapping of table names to their respective ingested row counts.
        """
        # Ensure Bronze database schema tables exist.
        self.create_bronze_tables()

        # Map each JSON file to its corresponding Bronze table name and primary key attribute.
        ingestion_targets = [
            ("users.json", "bronze_users", "user_id"),
            ("restaurants.json", "bronze_restaurants", "restaurant_id"),
            ("drivers.json", "bronze_drivers", "driver_id"),
            ("menu_items.json", "bronze_menu_items", "item_id"),
            ("orders.json", "bronze_orders", "order_id"),
            ("payments.json", "bronze_payments", "payment_id"),
        ]

        # Dictionary to record ingestion summary statistics.
        ingestion_summary = {}

        # Loop through each target file configuration and execute ingestion.
        for file_name, table, id_key in ingestion_targets:
            count = self.ingest_json_file(file_name, table, id_key)
            ingestion_summary[table] = count

        return ingestion_summary


if __name__ == "__main__":
    # Test Bronze layer ingestion when running this file directly.
    manager = BronzeLayerManager()
    summary = manager.run_full_bronze_ingestion()
    print("[BRONZE TEST SUMMARY]:", summary)
