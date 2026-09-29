# Zwiggy Medallion Data Warehouse — Technical Documentation (`DOCUMENTATION.md`)

This document provides complete technical specifications, database architecture details, table schemas, data dictionaries, and business rules for the **Zwiggy Medallion Data Warehouse**.

---

## 1. System & Technical Requirements

### 1.1 Prerequisites & Platform Compatibility
- **Operating System**: Linux, macOS, or Windows (cross-platform compatible).
- **Python Runtime**: Python 3.8+ (tested on Python 3.14).
- **Database Engine**: SQLite 3 (built into Python standard library, zero installation required).
- **Disk Storage**: ~10 MB for database file `zwiggy_dwh.db` and sample datasets.

### 1.2 Module Dependencies
All functionality is implemented using Python standard libraries:
- `sqlite3`: Embedded ACID-compliant SQL database management.
- `json`: Parsing raw JSON payloads and generating synthetic sample data.
- `unittest`: Automated test execution and verification.
- `os`, `sys`, `time`, `datetime`, `contextlib`: File paths, logging, timestamps, context managers.

---

## 2. Medallion Architecture Specification

The data warehouse implements the **Medallion Architecture**, a data design pattern introduced by Databricks to incrementally improve data quality as it moves through the pipeline:

```
Raw Sources (JSON)  ===>  BRONZE (Raw Ingestion)  ===>  SILVER (Cleansed & Curated)  ===>  GOLD (Aggregated Marts)
```

| Layer | Primary Purpose | Storage Format | Data Quality Level | Primary Consumers |
| :--- | :--- | :--- | :--- | :--- |
| **Bronze** | Raw landing zone & audit historical record | TEXT (JSON blobs) | Unfiltered, raw | Data Engineers, Auditors |
| **Silver** | Cleaned, deduplicated, relational schema | Typed SQL tables | Cleansed, validated | Data Analysts, Scientists |
| **Gold** | Aggregated data marts & KPI summaries | Analytics tables | High-level aggregated | Executives, BI Dashboards |

---

## 3. Detailed Table Schemas & Data Dictionary

### 3.1 Bronze Layer Tables (Raw Ingestion)

#### Table: `bronze_users`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Surrogate sequence ID for ingestion audit |
| `raw_user_id` | TEXT | NULLABLE | Extracted customer ID (e.g. `USR_001`) |
| `raw_json` | TEXT | NOT NULL | Complete original JSON payload |
| `source_file` | TEXT | NOT NULL | Source file name (`users.json`) |
| `ingested_at` | TEXT | NOT NULL | UTC ISO-8601 timestamp of ingestion |

#### Table: `bronze_restaurants`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Audit sequence ID |
| `raw_restaurant_id` | TEXT | NULLABLE | Extracted restaurant ID (e.g. `RST_001`) |
| `raw_json` | TEXT | NOT NULL | Complete original JSON payload |
| `source_file` | TEXT | NOT NULL | Source file name (`restaurants.json`) |
| `ingested_at` | TEXT | NOT NULL | Ingestion UTC timestamp |

#### Table: `bronze_drivers`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Audit sequence ID |
| `raw_driver_id` | TEXT | NULLABLE | Extracted delivery partner ID (e.g. `DRV_001`) |
| `raw_json` | TEXT | NOT NULL | Complete original JSON payload |
| `source_file` | TEXT | NOT NULL | Source file name (`drivers.json`) |
| `ingested_at` | TEXT | NOT NULL | Ingestion UTC timestamp |

#### Table: `bronze_menu_items`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Audit sequence ID |
| `raw_item_id` | TEXT | NULLABLE | Extracted item ID (e.g. `ITM_001`) |
| `raw_json` | TEXT | NOT NULL | Complete original JSON payload |
| `source_file` | TEXT | NOT NULL | Source file name (`menu_items.json`) |
| `ingested_at` | TEXT | NOT NULL | Ingestion UTC timestamp |

#### Table: `bronze_orders`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Audit sequence ID |
| `raw_order_id` | TEXT | NULLABLE | Extracted order ID (e.g. `ORD_001`) |
| `raw_json` | TEXT | NOT NULL | Complete original JSON order payload with items array |
| `source_file` | TEXT | NOT NULL | Source file name (`orders.json`) |
| `ingested_at` | TEXT | NOT NULL | Ingestion UTC timestamp |

#### Table: `bronze_payments`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `record_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Audit sequence ID |
| `raw_payment_id` | TEXT | NULLABLE | Extracted payment transaction ID (`PAY_001`) |
| `raw_json` | TEXT | NOT NULL | Complete original JSON payload |
| `source_file` | TEXT | NOT NULL | Source file name (`payments.json`) |
| `ingested_at` | TEXT | NOT NULL | Ingestion UTC timestamp |

---

### 3.2 Silver Layer Tables (Cleaned & Curated)

#### Table: `silver_users`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | TEXT | PRIMARY KEY | Unique customer identifier |
| `full_name` | TEXT | NOT NULL | Trimmed customer full name |
| `email` | TEXT | NOT NULL | Normalized lowercase customer email |
| `phone_number` | TEXT | DEFAULT 'N/A' | Customer phone number |
| `city` | TEXT | NOT NULL | Primary delivery city |
| `registered_at` | TEXT | NOT NULL | Registration date timestamp |
| `processed_at` | TEXT | NOT NULL | Silver layer processing timestamp |

#### Table: `silver_restaurants`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `restaurant_id` | TEXT | PRIMARY KEY | Unique restaurant identifier |
| `restaurant_name` | TEXT | NOT NULL | Restaurant display name |
| `cuisine_type` | TEXT | NOT NULL | Primary cuisine category |
| `city` | TEXT | NOT NULL | Restaurant operating city |
| `rating` | REAL | DEFAULT 0.0 | Customer rating (0.0 - 5.0) |
| `is_active` | INTEGER | DEFAULT 1 | Active status flag (1 = Active, 0 = Inactive) |
| `processed_at` | TEXT | NOT NULL | Processing timestamp |

#### Table: `silver_drivers`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `driver_id` | TEXT | PRIMARY KEY | Unique delivery partner identifier |
| `driver_name` | TEXT | NOT NULL | Delivery partner name |
| `vehicle_type` | TEXT | NOT NULL | Vehicle category (Motorcycle, Scooter, E-Bike) |
| `city` | TEXT | NOT NULL | Operating city |
| `rating` | REAL | DEFAULT 0.0 | Driver rating score |
| `is_active` | INTEGER | DEFAULT 1 | Active status flag |
| `processed_at` | TEXT | NOT NULL | Processing timestamp |

#### Table: `silver_menu_items`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `item_id` | TEXT | PRIMARY KEY | Unique menu dish identifier |
| `restaurant_id` | TEXT | FOREIGN KEY | Parent restaurant ID |
| `item_name` | TEXT | NOT NULL | Name of dish |
| `price` | REAL | NOT NULL | Price in INR |
| `is_available` | INTEGER | DEFAULT 1 | Availability status flag |
| `processed_at` | TEXT | NOT NULL | Processing timestamp |

#### Table: `silver_orders`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `order_id` | TEXT | PRIMARY KEY | Unique order transaction ID |
| `user_id` | TEXT | FOREIGN KEY | Customer ID |
| `restaurant_id` | TEXT | FOREIGN KEY | Restaurant ID |
| `driver_id` | TEXT | FOREIGN KEY (NULLABLE)| Delivery driver ID (NULL if cancelled) |
| `order_status` | TEXT | NOT NULL | Uppercase status (`DELIVERED`, `CANCELLED`, `PENDING`) |
| `order_timestamp` | TEXT | NOT NULL | ISO order timestamp |
| `subtotal` | REAL | NOT NULL | Item subtotal sum |
| `tax` | REAL | NOT NULL | Calculated tax amount |
| `delivery_fee` | REAL | NOT NULL | Delivery fee |
| `discount` | REAL | NOT NULL | Applied discount amount |
| `total_amount` | REAL | NOT NULL | Final net amount billed to customer |
| `processed_at` | TEXT | NOT NULL | Processing timestamp |

#### Table: `silver_order_items`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `order_item_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Line item sequence ID |
| `order_id` | TEXT | FOREIGN KEY | Parent order ID |
| `item_id` | TEXT | NOT NULL | Item ID |
| `item_name` | TEXT | NOT NULL | Item name |
| `quantity` | INTEGER | NOT NULL | Quantity ordered |
| `unit_price` | REAL | NOT NULL | Price per single unit |
| `total_price` | REAL | NOT NULL | Quantity $\times$ Unit Price |
| `processed_at` | TEXT | NOT NULL | Processing timestamp |

#### Table: `silver_payments`
| Column | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `payment_id` | TEXT | PRIMARY KEY | Payment transaction ID |
| `order_id` | TEXT | FOREIGN KEY | Linked order ID |
| `payment_method` | TEXT | NOT NULL | Mode of payment (`UPI`, `CREDIT_CARD`, `DEBIT_CARD`, etc.) |
| `payment_status` | TEXT | NOT NULL | Status (`SUCCESS`, `FAILED`, `PENDING`) |
| `transaction_amount` | REAL | NOT NULL | Amount paid |
| `payment_timestamp` | TEXT | NOT NULL | Timestamp of transaction |
| `processed_at` | TEXT | NOT NULL | Processing timestamp |

---

### 3.3 Gold Layer Tables (Aggregated Data Marts)

#### Table: `gold_daily_restaurant_sales`
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `summary_id` | INTEGER PRIMARY KEY | Auto-increment sequence ID |
| `order_date` | TEXT | Order date formatted as `YYYY-MM-DD` |
| `restaurant_id` | TEXT | Restaurant unique identifier |
| `restaurant_name` | TEXT | Restaurant display name |
| `city` | TEXT | Restaurant city |
| `total_orders` | INTEGER | Total count of orders received |
| `completed_orders` | INTEGER | Count of successfully delivered orders |
| `cancelled_orders` | INTEGER | Count of cancelled orders |
| `gross_revenue` | REAL | Sum of all order amounts |
| `net_revenue` | REAL | Sum of delivered order amounts |
| `avg_order_value` | REAL | Average Order Value (AOV = Net Revenue / Completed Orders) |
| `cancellation_rate` | REAL | Cancellation percentage = (Cancelled Orders / Total Orders) $\times$ 100 |
| `processed_at` | TEXT | Processing UTC timestamp |

#### Table: `gold_user_analytics`
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `user_id` | TEXT PRIMARY KEY | Customer identifier |
| `full_name` | TEXT | Customer name |
| `city` | TEXT | Customer city |
| `total_orders` | INTEGER | Total lifetime order count |
| `total_spend` | REAL | Total lifetime delivered order spend (LTV) |
| `avg_order_spend` | REAL | Average spend per order |
| `first_order_date` | TEXT | Date of customer's first order |
| `last_order_date` | TEXT | Date of customer's most recent order |
| `rfm_segment` | TEXT | Customer RFM Segment (`HIGH_VALUE_VIP`, `ACTIVE_REGULAR`, `NEW_INACTIVE`) |
| `processed_at` | TEXT | Processing UTC timestamp |

#### Table: `gold_driver_metrics`
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `driver_id` | TEXT PRIMARY KEY | Delivery driver identifier |
| `driver_name` | TEXT | Delivery driver name |
| `vehicle_type` | TEXT | Vehicle category |
| `city` | TEXT | Operating city |
| `rating` | REAL | Driver rating score |
| `total_deliveries` | INTEGER | Total completed orders delivered |
| `total_revenue_handled` | REAL | Cumulative revenue of orders delivered |
| `processed_at` | TEXT | Processing UTC timestamp |

#### Table: `gold_city_performance`
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `city` | TEXT PRIMARY KEY | City name |
| `total_restaurants` | INTEGER | Total registered restaurants in city |
| `total_active_users` | INTEGER | Total active customers in city |
| `total_drivers` | INTEGER | Total active delivery partners in city |
| `total_orders` | INTEGER | Cumulative orders placed in city |
| `total_city_revenue` | REAL | Total revenue generated in city |
| `avg_order_value` | REAL | Average order value for the city |
| `processed_at` | TEXT | Processing UTC timestamp |

---

## 4. Business Transformation Rules & Formulas

### 4.1 Deduplication Logic
Raw Bronze data may contain duplicate records due to retry mechanisms or streaming re-ingestion. Deduplication in Silver tables uses the SQL window function `ROW_NUMBER()`:

```sql
ROW_NUMBER() OVER (
    PARTITION BY json_extract(raw_json, '$.user_id')
    ORDER BY record_id DESC
) AS row_num
```
Records where `row_num = 1` are selected, ensuring only the latest version of each record is kept.

### 4.2 Financial Formulas
1. **Total Order Amount**:
   $$\text{Total Amount} = \text{Subtotal} + \text{Tax} + \text{Delivery Fee} - \text{Discount}$$
2. **Average Order Value (AOV)**:
   $$\text{AOV} = \frac{\text{Net Revenue}}{\text{Completed Orders}}$$
3. **Cancellation Rate**:
   $$\text{Cancellation Rate (\%)} = \left(\frac{\text{Cancelled Orders}}{\text{Total Orders}}\right) \times 100$$

### 4.3 Customer RFM Segmentation Rules
- **HIGH_VALUE_VIP**: $\text{Total Orders} \ge 3$ OR $\text{Total Spend} > 1000.00$ INR.
- **ACTIVE_REGULAR**: $1 \le \text{Total Orders} < 3$.
- **NEW_INACTIVE**: $\text{Total Orders} = 0$.
