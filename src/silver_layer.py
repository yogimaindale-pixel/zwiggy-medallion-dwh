# ==============================================================================
# FILE: src/silver_layer.py
# PURPOSE: Implements the Silver Layer (Cleansed & Curated Data) of the Data Warehouse.
# EXPLANATION FOR JUNIOR DEVELOPERS:
# The Silver layer cleanses, validates, deduplicates, and structures raw data
# from the Bronze layer. While Bronze contains raw JSON text blobs, Silver contains
# structured tables with typed columns (e.g. INTEGER, REAL, TEXT, DATETIME),
# normalized strings, default values for missing data, and unnested child tables.
# ==============================================================================

# Import 'json' to parse nested array structures like order items.
import json

# Import 'os' for file and directory operations.
import os

# Import 'sys' to manage module search paths.
import sys

# Import 'datetime' and 'timezone' for transformation audit timestamps.
from datetime import datetime, timezone

# Ensure the root project path is accessible for imports.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database connection helper functions from src/db_connection.py.
from src.db_connection import get_db_connection, execute_sql_script


class SilverLayerManager:
    """
    Manages the creation of Silver tables and the transformation of raw Bronze JSON records
    into clean, normalized relational tables.
    """

    def create_silver_tables(self):
        """
        Executes SQL DDL queries to create structured Silver layer tables.
        Includes constraints, data types, and primary key definitions.
        """
        sql_ddl = """
        -- Cleansed Users Dimension Table
        CREATE TABLE IF NOT EXISTS silver_users (
            user_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone_number TEXT,
            city TEXT NOT NULL,
            registered_at TEXT NOT NULL,
            processed_at TEXT NOT NULL
        );

        -- Cleansed Restaurants Dimension Table
        CREATE TABLE IF NOT EXISTS silver_restaurants (
            restaurant_id TEXT PRIMARY KEY,
            restaurant_name TEXT NOT NULL,
            cuisine_type TEXT NOT NULL,
            city TEXT NOT NULL,
            rating REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 1,
            processed_at TEXT NOT NULL
        );

        -- Cleansed Drivers Dimension Table
        CREATE TABLE IF NOT EXISTS silver_drivers (
            driver_id TEXT PRIMARY KEY,
            driver_name TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            city TEXT NOT NULL,
            rating REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 1,
            processed_at TEXT NOT NULL
        );

        -- Cleansed Menu Items Dimension Table
        CREATE TABLE IF NOT EXISTS silver_menu_items (
            item_id TEXT PRIMARY KEY,
            restaurant_id TEXT NOT NULL,
            item_name TEXT NOT NULL,
            price REAL NOT NULL,
            is_available INTEGER DEFAULT 1,
            processed_at TEXT NOT NULL,
            FOREIGN KEY (restaurant_id) REFERENCES silver_restaurants(restaurant_id)
        );

        -- Cleansed Customer Orders Fact Table
        CREATE TABLE IF NOT EXISTS silver_orders (
            order_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            restaurant_id TEXT NOT NULL,
            driver_id TEXT,
            order_status TEXT NOT NULL,
            order_timestamp TEXT NOT NULL,
            subtotal REAL NOT NULL,
            tax REAL NOT NULL,
            delivery_fee REAL NOT NULL,
            discount REAL NOT NULL,
            total_amount REAL NOT NULL,
            processed_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES silver_users(user_id),
            FOREIGN KEY (restaurant_id) REFERENCES silver_restaurants(restaurant_id),
            FOREIGN KEY (driver_id) REFERENCES silver_drivers(driver_id)
        );

        -- Cleansed Order Line Items Fact Detail Table (Unnested items)
        CREATE TABLE IF NOT EXISTS silver_order_items (
            order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            processed_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES silver_orders(order_id)
        );

        -- Cleansed Payment Transactions Fact Table
        CREATE TABLE IF NOT EXISTS silver_payments (
            payment_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            transaction_amount REAL NOT NULL,
            payment_timestamp TEXT NOT NULL,
            processed_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES silver_orders(order_id)
        );
        """
        # Execute the multi-statement schema script.
        execute_sql_script(sql_ddl)
        print("[SILVER] Created all Silver layer schema tables.")

    def process_silver_users(self):
        """
        Extracts, cleans, deduplicates, and loads User records from bronze_users into silver_users.
        
        Returns:
            int: Total number of rows populated in silver_users.
        """
        # Current audit timestamp for processing tracking.
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # SQL query using SQLite 'json_extract' function to extract specific fields
        # from the raw JSON payload in bronze_users.
        # Uses ROW_NUMBER() window function to perform deduplication, retaining the newest record per user_id.
        sql_query = """
        WITH ExtractUsers AS (
            SELECT 
                json_extract(raw_json, '$.user_id') AS user_id,
                TRIM(json_extract(raw_json, '$.full_name')) AS full_name,
                LOWER(TRIM(json_extract(raw_json, '$.email'))) AS email,
                json_extract(raw_json, '$.phone_number') AS phone_number,
                TRIM(json_extract(raw_json, '$.city')) AS city,
                json_extract(raw_json, '$.registered_at') AS registered_at,
                ROW_NUMBER() OVER (
                    PARTITION BY json_extract(raw_json, '$.user_id') 
                    ORDER BY record_id DESC
                ) AS row_num
            FROM bronze_users
            WHERE json_extract(raw_json, '$.user_id') IS NOT NULL
        )
        SELECT user_id, full_name, email, phone_number, city, registered_at
        FROM ExtractUsers
        WHERE row_num = 1;
        """

        conn = get_db_connection()
        cursor = conn.cursor()

        # Clear existing Silver records for clean idempotency.
        cursor.execute("DELETE FROM silver_users;")

        # Fetch all cleansed and deduplicated user records.
        cursor.execute(sql_query)
        rows = cursor.fetchall()

        insert_sql = """
            INSERT INTO silver_users (user_id, full_name, email, phone_number, city, registered_at, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """

        count = 0
        for r in rows:
            # Fallback handling for missing values.
            phone = r["phone_number"] if r["phone_number"] else "N/A"
            city = r["city"] if r["city"] else "Unknown"

            cursor.execute(insert_sql, (
                r["user_id"],
                r["full_name"],
                r["email"],
                phone,
                city,
                r["registered_at"],
                current_time
            ))
            count += 1

        conn.commit()
        conn.close()
        print(f"[SILVER] Populated {count} records into 'silver_users'.")
        return count

    def process_silver_restaurants(self):
        """
        Transforms raw restaurant records from bronze_restaurants into silver_restaurants.
        """
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        sql_query = """
        WITH ExtractRestaurants AS (
            SELECT 
                json_extract(raw_json, '$.restaurant_id') AS restaurant_id,
                TRIM(json_extract(raw_json, '$.restaurant_name')) AS restaurant_name,
                TRIM(json_extract(raw_json, '$.cuisine_type')) AS cuisine_type,
                TRIM(json_extract(raw_json, '$.city')) AS city,
                CAST(json_extract(raw_json, '$.rating') AS REAL) AS rating,
                CASE WHEN json_extract(raw_json, '$.is_active') = 1 OR json_extract(raw_json, '$.is_active') = true THEN 1 ELSE 0 END AS is_active,
                ROW_NUMBER() OVER (
                    PARTITION BY json_extract(raw_json, '$.restaurant_id') 
                    ORDER BY record_id DESC
                ) AS row_num
            FROM bronze_restaurants
            WHERE json_extract(raw_json, '$.restaurant_id') IS NOT NULL
        )
        SELECT restaurant_id, restaurant_name, cuisine_type, city, rating, is_active
        FROM ExtractRestaurants
        WHERE row_num = 1;
        """

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM silver_restaurants;")

        cursor.execute(sql_query)
        rows = cursor.fetchall()

        insert_sql = """
            INSERT INTO silver_restaurants (restaurant_id, restaurant_name, cuisine_type, city, rating, is_active, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """

        count = 0
        for r in rows:
            cursor.execute(insert_sql, (
                r["restaurant_id"],
                r["restaurant_name"],
                r["cuisine_type"],
                r["city"],
                r["rating"] if r["rating"] is not None else 0.0,
                r["is_active"],
                current_time
            ))
            count += 1

        conn.commit()
        conn.close()
        print(f"[SILVER] Populated {count} records into 'silver_restaurants'.")
        return count

    def process_silver_drivers(self):
        """
        Transforms raw delivery partner records from bronze_drivers into silver_drivers.
        """
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        sql_query = """
        WITH ExtractDrivers AS (
            SELECT 
                json_extract(raw_json, '$.driver_id') AS driver_id,
                TRIM(json_extract(raw_json, '$.driver_name')) AS driver_name,
                TRIM(json_extract(raw_json, '$.vehicle_type')) AS vehicle_type,
                TRIM(json_extract(raw_json, '$.city')) AS city,
                CAST(json_extract(raw_json, '$.rating') AS REAL) AS rating,
                CASE WHEN json_extract(raw_json, '$.is_active') = 1 OR json_extract(raw_json, '$.is_active') = true THEN 1 ELSE 0 END AS is_active,
                ROW_NUMBER() OVER (
                    PARTITION BY json_extract(raw_json, '$.driver_id') 
                    ORDER BY record_id DESC
                ) AS row_num
            FROM bronze_drivers
            WHERE json_extract(raw_json, '$.driver_id') IS NOT NULL
        )
        SELECT driver_id, driver_name, vehicle_type, city, rating, is_active
        FROM ExtractDrivers
        WHERE row_num = 1;
        """

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM silver_drivers;")

        cursor.execute(sql_query)
        rows = cursor.fetchall()

        insert_sql = """
            INSERT INTO silver_drivers (driver_id, driver_name, vehicle_type, city, rating, is_active, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """

        count = 0
        for r in rows:
            cursor.execute(insert_sql, (
                r["driver_id"],
                r["driver_name"],
                r["vehicle_type"],
                r["city"],
                r["rating"] if r["rating"] is not None else 0.0,
                r["is_active"],
                current_time
            ))
            count += 1

        conn.commit()
        conn.close()
        print(f"[SILVER] Populated {count} records into 'silver_drivers'.")
        return count

    def process_silver_menu_items(self):
        """
        Transforms raw menu item records from bronze_menu_items into silver_menu_items.
        """
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        sql_query = """
        WITH ExtractMenu AS (
            SELECT 
                json_extract(raw_json, '$.item_id') AS item_id,
                json_extract(raw_json, '$.restaurant_id') AS restaurant_id,
                TRIM(json_extract(raw_json, '$.item_name')) AS item_name,
                CAST(json_extract(raw_json, '$.price') AS REAL) AS price,
                CASE WHEN json_extract(raw_json, '$.is_available') = 1 OR json_extract(raw_json, '$.is_available') = true THEN 1 ELSE 0 END AS is_available,
                ROW_NUMBER() OVER (
                    PARTITION BY json_extract(raw_json, '$.item_id') 
                    ORDER BY record_id DESC
                ) AS row_num
            FROM bronze_menu_items
            WHERE json_extract(raw_json, '$.item_id') IS NOT NULL
        )
        SELECT item_id, restaurant_id, item_name, price, is_available
        FROM ExtractMenu
        WHERE row_num = 1;
        """

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM silver_menu_items;")

        cursor.execute(sql_query)
        rows = cursor.fetchall()

        insert_sql = """
            INSERT INTO silver_menu_items (item_id, restaurant_id, item_name, price, is_available, processed_at)
            VALUES (?, ?, ?, ?, ?, ?);
        """

        count = 0
        for r in rows:
            cursor.execute(insert_sql, (
                r["item_id"],
                r["restaurant_id"],
                r["item_name"],
                r["price"],
                r["is_available"],
                current_time
            ))
            count += 1

        conn.commit()
        conn.close()
        print(f"[SILVER] Populated {count} records into 'silver_menu_items'.")
        return count

    def process_silver_orders_and_items(self):
        """
        Transforms order records from bronze_orders into silver_orders and unnests child items into silver_order_items.
        """
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Retrieve raw JSON blobs from bronze_orders to unnest nested 'items' arrays safely in Python.
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM silver_orders;")
        cursor.execute("DELETE FROM silver_order_items;")

        cursor.execute("SELECT raw_json FROM bronze_orders;")
        rows = cursor.fetchall()

        order_count = 0
        item_count = 0

        insert_order_sql = """
            INSERT INTO silver_orders (
                order_id, user_id, restaurant_id, driver_id, order_status, 
                order_timestamp, subtotal, tax, delivery_fee, discount, total_amount, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        insert_item_sql = """
            INSERT INTO silver_order_items (
                order_id, item_id, item_name, quantity, unit_price, total_price, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """

        seen_orders = set()

        for r in rows:
            # Parse the JSON string into a Python dictionary.
            data = json.loads(r["raw_json"])
            order_id = data.get("order_id")

            # Deduplicate by skipping already processed order IDs.
            if not order_id or order_id in seen_orders:
                continue
            seen_orders.add(order_id)

            status = data.get("order_status", "UNKNOWN").upper()
            subtotal = float(data.get("subtotal", 0.0))
            tax = float(data.get("tax", 0.0))
            fee = float(data.get("delivery_fee", 0.0))
            discount = float(data.get("discount", 0.0))
            total = float(data.get("total_amount", subtotal + tax + fee - discount))

            cursor.execute(insert_order_sql, (
                order_id,
                data.get("user_id"),
                data.get("restaurant_id"),
                data.get("driver_id"),
                status,
                data.get("order_timestamp"),
                subtotal,
                tax,
                fee,
                discount,
                total,
                current_time
            ))
            order_count += 1

            # Unnest child array of items.
            items = data.get("items", [])
            for item in items:
                q = int(item.get("quantity", 1))
                u_price = float(item.get("unit_price", 0.0))
                t_price = round(q * u_price, 2)

                cursor.execute(insert_item_sql, (
                    order_id,
                    item.get("item_id"),
                    item.get("item_name", "Unknown Item"),
                    q,
                    u_price,
                    t_price,
                    current_time
                ))
                item_count += 1

        conn.commit()
        conn.close()
        print(f"[SILVER] Populated {order_count} orders into 'silver_orders' and {item_count} items into 'silver_order_items'.")
        return order_count, item_count

    def process_silver_payments(self):
        """
        Transforms payment records from bronze_payments into silver_payments.
        """
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        sql_query = """
        WITH ExtractPayments AS (
            SELECT 
                json_extract(raw_json, '$.payment_id') AS payment_id,
                json_extract(raw_json, '$.order_id') AS order_id,
                UPPER(TRIM(json_extract(raw_json, '$.payment_method'))) AS payment_method,
                UPPER(TRIM(json_extract(raw_json, '$.payment_status'))) AS payment_status,
                CAST(json_extract(raw_json, '$.transaction_amount') AS REAL) AS transaction_amount,
                json_extract(raw_json, '$.payment_timestamp') AS payment_timestamp,
                ROW_NUMBER() OVER (
                    PARTITION BY json_extract(raw_json, '$.payment_id') 
                    ORDER BY record_id DESC
                ) AS row_num
            FROM bronze_payments
            WHERE json_extract(raw_json, '$.payment_id') IS NOT NULL
        )
        SELECT payment_id, order_id, payment_method, payment_status, transaction_amount, payment_timestamp
        FROM ExtractPayments
        WHERE row_num = 1;
        """

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM silver_payments;")

        cursor.execute(sql_query)
        rows = cursor.fetchall()

        insert_sql = """
            INSERT INTO silver_payments (payment_id, order_id, payment_method, payment_status, transaction_amount, payment_timestamp, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """

        count = 0
        for r in rows:
            cursor.execute(insert_sql, (
                r["payment_id"],
                r["order_id"],
                r["payment_method"],
                r["payment_status"],
                r["transaction_amount"],
                r["payment_timestamp"],
                current_time
            ))
            count += 1

        conn.commit()
        conn.close()
        print(f"[SILVER] Populated {count} records into 'silver_payments'.")
        return count

    def run_full_silver_transformation(self):
        """
        Orchestrates full transformation of all Bronze tables into Silver tables.
        
        Returns:
            dict: Summary mapping of Silver table names to populated row counts.
        """
        self.create_silver_tables()

        summary = {}
        summary["silver_users"] = self.process_silver_users()
        summary["silver_restaurants"] = self.process_silver_restaurants()
        summary["silver_drivers"] = self.process_silver_drivers()
        summary["silver_menu_items"] = self.process_silver_menu_items()
        
        orders_count, items_count = self.process_silver_orders_and_items()
        summary["silver_orders"] = orders_count
        summary["silver_order_items"] = items_count

        summary["silver_payments"] = self.process_silver_payments()

        return summary


if __name__ == "__main__":
    # Test Silver layer transformation when executing script directly.
    manager = SilverLayerManager()
    summary = manager.run_full_silver_transformation()
    print("[SILVER TEST SUMMARY]:", summary)
