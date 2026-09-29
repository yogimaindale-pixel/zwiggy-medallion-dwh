# ==============================================================================
# FILE: src/gold_layer.py
# PURPOSE: Implements the Gold Layer (Business Aggregations & Data Marts).
# EXPLANATION FOR JUNIOR DEVELOPERS:
# The Gold layer is the top tier in a Medallion Architecture. While Silver tables
# store clean granular row-level data (e.g. single orders), Gold tables store
# pre-aggregated business metrics (e.g. daily sales per restaurant, user LTV,
# driver ratings, city revenue). Business intelligence dashboards (Power BI, Tableau)
# connect directly to Gold tables for fast, pre-computed query results.
# ==============================================================================

# Import 'os' for system path manipulation.
import os

# Import 'sys' to manage module search paths.
import sys

# Import 'datetime' and 'timezone' to record processing audit timestamps.
from datetime import datetime, timezone

# Ensure the root project path is accessible for imports.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database connection helper functions from src/db_connection.py.
from src.db_connection import get_db_connection, execute_sql_script


class GoldLayerManager:
    """
    Manages the creation and population of Gold layer analytical data marts.
    """

    def create_gold_tables(self):
        """
        Executes DDL queries to create Gold layer analytical tables.
        """
        sql_ddl = """
        -- 1. Daily Restaurant Sales Performance Mart
        CREATE TABLE IF NOT EXISTS gold_daily_restaurant_sales (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_date TEXT NOT NULL,
            restaurant_id TEXT NOT NULL,
            restaurant_name TEXT NOT NULL,
            city TEXT NOT NULL,
            total_orders INTEGER NOT NULL,
            completed_orders INTEGER NOT NULL,
            cancelled_orders INTEGER NOT NULL,
            gross_revenue REAL NOT NULL,
            net_revenue REAL NOT NULL,
            avg_order_value REAL NOT NULL,
            cancellation_rate REAL NOT NULL,
            processed_at TEXT NOT NULL,
            FOREIGN KEY (restaurant_id) REFERENCES silver_restaurants(restaurant_id)
        );

        -- 2. User Engagement & Customer Lifetime Value (LTV) Mart
        CREATE TABLE IF NOT EXISTS gold_user_analytics (
            user_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            city TEXT NOT NULL,
            total_orders INTEGER NOT NULL,
            total_spend REAL NOT NULL,
            avg_order_spend REAL NOT NULL,
            first_order_date TEXT,
            last_order_date TEXT,
            rfm_segment TEXT NOT NULL,
            processed_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES silver_users(user_id)
        );

        -- 3. Driver Performance & Earnings Metrics Mart
        CREATE TABLE IF NOT EXISTS gold_driver_metrics (
            driver_id TEXT PRIMARY KEY,
            driver_name TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            city TEXT NOT NULL,
            rating REAL NOT NULL,
            total_deliveries INTEGER NOT NULL,
            total_revenue_handled REAL NOT NULL,
            processed_at TEXT NOT NULL,
            FOREIGN KEY (driver_id) REFERENCES silver_drivers(driver_id)
        );

        -- 4. City Level Business Performance Summary Mart
        CREATE TABLE IF NOT EXISTS gold_city_performance (
            city TEXT PRIMARY KEY,
            total_restaurants INTEGER NOT NULL,
            total_active_users INTEGER NOT NULL,
            total_drivers INTEGER NOT NULL,
            total_orders INTEGER NOT NULL,
            total_city_revenue REAL NOT NULL,
            avg_order_value REAL NOT NULL,
            processed_at TEXT NOT NULL
        );
        """
        execute_sql_script(sql_ddl)
        print("[GOLD] Created all Gold layer business aggregation tables.")

    def process_gold_daily_restaurant_sales(self):
        """
        Aggregates daily order totals and revenue metrics per restaurant from silver_orders.
        
        Returns:
            int: Number of summary rows inserted into gold_daily_restaurant_sales.
        """
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # SQL query performing GROUP BY aggregation on date, restaurant_id, and restaurant_name.
        # Computes Gross Revenue (SUM of total_amount for all orders) and Net Revenue (SUM for DELIVERED orders).
        sql_query = """
        SELECT 
            SUBSTR(o.order_timestamp, 1, 10) AS order_date,
            r.restaurant_id,
            r.restaurant_name,
            r.city,
            COUNT(o.order_id) AS total_orders,
            SUM(CASE WHEN o.order_status = 'DELIVERED' THEN 1 ELSE 0 END) AS completed_orders,
            SUM(CASE WHEN o.order_status = 'CANCELLED' THEN 1 ELSE 0 END) AS cancelled_orders,
            SUM(o.total_amount) AS gross_revenue,
            SUM(CASE WHEN o.order_status = 'DELIVERED' THEN o.total_amount ELSE 0.0 END) AS net_revenue
        FROM silver_orders o
        JOIN silver_restaurants r ON o.restaurant_id = r.restaurant_id
        GROUP BY SUBSTR(o.order_timestamp, 1, 10), r.restaurant_id, r.restaurant_name, r.city;
        """

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM gold_daily_restaurant_sales;")

        cursor.execute(sql_query)
        rows = cursor.fetchall()

        insert_sql = """
            INSERT INTO gold_daily_restaurant_sales (
                order_date, restaurant_id, restaurant_name, city, total_orders,
                completed_orders, cancelled_orders, gross_revenue, net_revenue,
                avg_order_value, cancellation_rate, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        count = 0
        for r in rows:
            tot_orders = r["total_orders"]
            comp_orders = r["completed_orders"]
            canc_orders = r["cancelled_orders"]
            gross_rev = round(r["gross_revenue"], 2)
            net_rev = round(r["net_revenue"], 2)

            # Calculate Average Order Value (AOV) for completed orders.
            aov = round(net_rev / comp_orders, 2) if comp_orders > 0 else 0.0

            # Calculate Cancellation Rate as percentage.
            c_rate = round((canc_orders / tot_orders) * 100.0, 2) if tot_orders > 0 else 0.0

            cursor.execute(insert_sql, (
                r["order_date"],
                r["restaurant_id"],
                r["restaurant_name"],
                r["city"],
                tot_orders,
                comp_orders,
                canc_orders,
                gross_rev,
                net_rev,
                aov,
                c_rate,
                current_time
            ))
            count += 1

        conn.commit()
        conn.close()
        print(f"[GOLD] Populated {count} summary rows into 'gold_daily_restaurant_sales'.")
        return count

    def process_gold_user_analytics(self):
        """
        Calculates User Lifetime Value (LTV), total order frequency, and RFM segmentation.
        """
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Query aggregating all user orders to calculate customer metrics.
        sql_query = """
        SELECT 
            u.user_id,
            u.full_name,
            u.city,
            COUNT(o.order_id) AS total_orders,
            COALESCE(SUM(CASE WHEN o.order_status = 'DELIVERED' THEN o.total_amount ELSE 0.0 END), 0.0) AS total_spend,
            MIN(o.order_timestamp) AS first_order_date,
            MAX(o.order_timestamp) AS last_order_date
        FROM silver_users u
        LEFT JOIN silver_orders o ON u.user_id = o.user_id
        GROUP BY u.user_id, u.full_name, u.city;
        """

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM gold_user_analytics;")

        cursor.execute(sql_query)
        rows = cursor.fetchall()

        insert_sql = """
            INSERT INTO gold_user_analytics (
                user_id, full_name, city, total_orders, total_spend,
                avg_order_spend, first_order_date, last_order_date, rfm_segment, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        count = 0
        for r in rows:
            tot_orders = r["total_orders"]
            tot_spend = round(r["total_spend"], 2)
            avg_spend = round(tot_spend / tot_orders, 2) if tot_orders > 0 else 0.0

            # Derive RFM customer segmentation based on spending and order frequency.
            if tot_orders >= 3 or tot_spend > 1000.0:
                segment = "HIGH_VALUE_VIP"
            elif tot_orders >= 1:
                segment = "ACTIVE_REGULAR"
            else:
                segment = "NEW_INACTIVE"

            cursor.execute(insert_sql, (
                r["user_id"],
                r["full_name"],
                r["city"],
                tot_orders,
                tot_spend,
                avg_spend,
                r["first_order_date"],
                r["last_order_date"],
                segment,
                current_time
            ))
            count += 1

        conn.commit()
        conn.close()
        print(f"[GOLD] Populated {count} user profile metrics into 'gold_user_analytics'.")
        return count

    def process_gold_driver_metrics(self):
        """
        Calculates total deliveries completed and total order revenue handled per driver.
        """
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        sql_query = """
        SELECT 
            d.driver_id,
            d.driver_name,
            d.vehicle_type,
            d.city,
            d.rating,
            COUNT(o.order_id) AS total_deliveries,
            COALESCE(SUM(o.total_amount), 0.0) AS total_revenue_handled
        FROM silver_drivers d
        LEFT JOIN silver_orders o ON d.driver_id = o.driver_id AND o.order_status = 'DELIVERED'
        GROUP BY d.driver_id, d.driver_name, d.vehicle_type, d.city, d.rating;
        """

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM gold_driver_metrics;")

        cursor.execute(sql_query)
        rows = cursor.fetchall()

        insert_sql = """
            INSERT INTO gold_driver_metrics (
                driver_id, driver_name, vehicle_type, city, rating,
                total_deliveries, total_revenue_handled, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """

        count = 0
        for r in rows:
            cursor.execute(insert_sql, (
                r["driver_id"],
                r["driver_name"],
                r["vehicle_type"],
                r["city"],
                r["rating"],
                r["total_deliveries"],
                round(r["total_revenue_handled"], 2),
                current_time
            ))
            count += 1

        conn.commit()
        conn.close()
        print(f"[GOLD] Populated {count} driver records into 'gold_driver_metrics'.")
        return count

    def process_gold_city_performance(self):
        """
        Aggregates city-level business statistics including restaurant count, user count, orders, and total revenue.
        """
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Query performing multi-table aggregations grouped by city.
        sql_query = """
        SELECT 
            c.city,
            (SELECT COUNT(*) FROM silver_restaurants r WHERE r.city = c.city) AS total_restaurants,
            (SELECT COUNT(*) FROM silver_users u WHERE u.city = c.city) AS total_active_users,
            (SELECT COUNT(*) FROM silver_drivers d WHERE d.city = c.city) AS total_drivers,
            (SELECT COUNT(*) FROM silver_orders o JOIN silver_users u2 ON o.user_id = u2.user_id WHERE u2.city = c.city) AS total_orders,
            (SELECT COALESCE(SUM(o2.total_amount), 0.0) FROM silver_orders o2 JOIN silver_users u3 ON o2.user_id = u3.user_id WHERE u3.city = c.city AND o2.order_status = 'DELIVERED') AS total_city_revenue
        FROM (
            SELECT city FROM silver_users
            UNION
            SELECT city FROM silver_restaurants
        ) c;
        """

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM gold_city_performance;")

        cursor.execute(sql_query)
        rows = cursor.fetchall()

        insert_sql = """
            INSERT INTO gold_city_performance (
                city, total_restaurants, total_active_users, total_drivers,
                total_orders, total_city_revenue, avg_order_value, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """

        count = 0
        for r in rows:
            tot_orders = r["total_orders"]
            tot_rev = round(r["total_city_revenue"], 2)
            aov = round(tot_rev / tot_orders, 2) if tot_orders > 0 else 0.0

            cursor.execute(insert_sql, (
                r["city"],
                r["total_restaurants"],
                r["total_active_users"],
                r["total_drivers"],
                tot_orders,
                tot_rev,
                aov,
                current_time
            ))
            count += 1

        conn.commit()
        conn.close()
        print(f"[GOLD] Populated {count} city summary records into 'gold_city_performance'.")
        return count

    def run_full_gold_aggregation(self):
        """
        Orchestrates full aggregation of all Gold layer analytical data marts.
        
        Returns:
            dict: Summary mapping of Gold table names to calculated row counts.
        """
        self.create_gold_tables()

        summary = {}
        summary["gold_daily_restaurant_sales"] = self.process_gold_daily_restaurant_sales()
        summary["gold_user_analytics"] = self.process_gold_user_analytics()
        summary["gold_driver_metrics"] = self.process_gold_driver_metrics()
        summary["gold_city_performance"] = self.process_gold_city_performance()

        return summary


if __name__ == "__main__":
    # Test Gold layer aggregations when script is executed directly.
    manager = GoldLayerManager()
    summary = manager.run_full_gold_aggregation()
    print("[GOLD TEST SUMMARY]:", summary)
