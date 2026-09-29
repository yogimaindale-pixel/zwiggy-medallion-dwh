# ==============================================================================
# FILE: data/sample_data_generator.py
# PURPOSE: Generates realistic mock JSON dataset for the Zwiggy platform.
# EXPLANATION FOR JUNIOR DEVELOPERS:
# Real-world data engineering pipelines process input data from external APIs
# or file streams. For local development and testing, we generate synthetic data
# that matches the structure of actual Zwiggy food delivery records.
# ==============================================================================

# Import the 'json' library to serialize Python dictionaries into formatted JSON text.
import json

# Import the 'os' library to build folder paths and save files to disk.
import os

# Import 'sys' to adjust module resolution paths.
import sys

# Import 'datetime' and 'timedelta' to generate realistic historical timestamp values.
from datetime import datetime, timedelta

# Import 'random' to simulate varied order prices, ratings, and status distributions.
import random

# Ensure the root project path is available for imports.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import RAW_DATA_DIR path from our central database configuration.
from config.database_config import RAW_DATA_DIR


def generate_all_sample_data():
    """
    Generates synthetic JSON data files representing Zwiggy core business entities:
      1. users.json         (Customer profiles)
      2. restaurants.json   (Restaurant partners)
      3. drivers.json       (Delivery partners)
      4. menu_items.json    (Restaurant food menu catalog)
      5. orders.json        (Transactional customer orders)
      6. payments.json      (Payment processing transactions)
    """
    # Fix the random seed so that every execution produces identical sample records.
    random.seed(42)

    # Define cities where Zwiggy operates.
    cities = ["Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Pune"]

    # --------------------------------------------------------------------------
    # 1. GENERATE USERS DATA
    # --------------------------------------------------------------------------
    # Create a list of 10 sample customer profile dictionaries.
    users_data = [
        {
            "user_id": f"USR_{i:03d}",
            "full_name": f"Customer_{i}",
            "email": f"customer_{i}@example.com",
            "phone_number": f"+919876543{i:02d}",
            "city": cities[i % len(cities)],
            "registered_at": "2024-01-15T10:30:00Z"
        }
        for i in range(1, 11)
    ]

    # Save the users list as a formatted JSON file in RAW_DATA_DIR.
    users_file_path = os.path.join(RAW_DATA_DIR, "users.json")
    with open(users_file_path, "w", encoding="utf-8") as f:
        # 'json.dump' converts the Python list into JSON text with 2-space indentation.
        json.dump(users_data, f, indent=2)

    # --------------------------------------------------------------------------
    # 2. GENERATE RESTAURANTS DATA
    # --------------------------------------------------------------------------
    # Define a list of restaurant cuisines and names.
    cuisines = ["Indian", "Italian", "Chinese", "Biryani", "Fast Food"]
    restaurant_names = [
        "Spicy Punjab Bistro", "Bella Italia Pasta", "Wok & Roll Chinese",
        "Royal Hyderabadi Biryani", "Burger King Junction", "Sagar Ratna South",
        "Tandoori Flames", "Pizza Express Hub"
    ]

    restaurants_data = [
        {
            "restaurant_id": f"RST_{i:03d}",
            "restaurant_name": name,
            "cuisine_type": cuisines[i % len(cuisines)],
            "city": cities[i % len(cities)],
            "rating": round(3.5 + (i * 0.2) % 1.5, 1),
            "is_active": True
        }
        for i, name in enumerate(restaurant_names, start=1)
    ]

    restaurants_file_path = os.path.join(RAW_DATA_DIR, "restaurants.json")
    with open(restaurants_file_path, "w", encoding="utf-8") as f:
        json.dump(restaurants_data, f, indent=2)

    # --------------------------------------------------------------------------
    # 3. GENERATE DRIVERS DATA
    # --------------------------------------------------------------------------
    vehicles = ["Motorcycle", "Scooter", "Electric Bike"]
    drivers_data = [
        {
            "driver_id": f"DRV_{i:03d}",
            "driver_name": f"DeliveryPartner_{i}",
            "vehicle_type": vehicles[i % len(vehicles)],
            "city": cities[i % len(cities)],
            "rating": round(4.0 + (i * 0.1) % 1.0, 1),
            "is_active": True
        }
        for i in range(1, 7)
    ]

    drivers_file_path = os.path.join(RAW_DATA_DIR, "drivers.json")
    with open(drivers_file_path, "w", encoding="utf-8") as f:
        json.dump(drivers_data, f, indent=2)

    # --------------------------------------------------------------------------
    # 4. GENERATE MENU ITEMS DATA
    # --------------------------------------------------------------------------
    menu_items_data = []
    item_id_counter = 1
    sample_dishes = {
        "Indian": [("Paneer Butter Masala", 280), ("Dal Makhani", 220), ("Garlic Naan", 50)],
        "Italian": [("Margherita Pizza", 350), ("Penne Arrabbiata", 310), ("Garlic Bread", 150)],
        "Chinese": [("Hakka Noodles", 200), ("Veg Manchurian", 220), ("Spring Rolls", 180)],
        "Biryani": [("Chicken Dum Biryani", 320), ("Mutton Biryani", 420), ("Raita", 40)],
        "Fast Food": [("Crispy Veg Burger", 120), ("French Fries", 100), ("Cold Coffee", 140)]
    }

    for r in restaurants_data:
        r_id = r["restaurant_id"]
        c_type = r["cuisine_type"]
        dishes = sample_dishes.get(c_type, sample_dishes["Indian"])
        
        for dish_name, price in dishes:
            menu_items_data.append({
                "item_id": f"ITM_{item_id_counter:03d}",
                "restaurant_id": r_id,
                "item_name": dish_name,
                "price": price,
                "is_available": True
            })
            item_id_counter += 1

    menu_file_path = os.path.join(RAW_DATA_DIR, "menu_items.json")
    with open(menu_file_path, "w", encoding="utf-8") as f:
        json.dump(menu_items_data, f, indent=2)

    # --------------------------------------------------------------------------
    # 5. GENERATE ORDERS & PAYMENTS DATA
    # --------------------------------------------------------------------------
    orders_data = []
    payments_data = []
    
    # Base timestamp for order simulations.
    base_date = datetime(2024, 2, 1, 12, 0, 0)
    statuses = ["DELIVERED", "DELIVERED", "DELIVERED", "CANCELLED", "DELIVERED"]
    payment_methods = ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NET_BANKING", "CASH"]

    for i in range(1, 21):
        order_id = f"ORD_{i:03d}"
        user = users_data[i % len(users_data)]
        
        # Pick a restaurant in the user's city if possible, or fallback.
        city_restaurants = [r for r in restaurants_data if r["city"] == user["city"]]
        restaurant = city_restaurants[0] if city_restaurants else restaurants_data[i % len(restaurants_data)]
        
        # Pick a driver in the same city.
        city_drivers = [d for d in drivers_data if d["city"] == user["city"]]
        driver = city_drivers[0] if city_drivers else drivers_data[i % len(drivers_data)]
        
        # Select items from this restaurant's menu.
        rest_items = [m for m in menu_items_data if m["restaurant_id"] == restaurant["restaurant_id"]]
        if not rest_items:
            rest_items = menu_items_data[:2]

        selected_item = rest_items[i % len(rest_items)]
        quantity = (i % 3) + 1
        subtotal = selected_item["price"] * quantity
        tax = round(subtotal * 0.05, 2)
        delivery_fee = 40.0
        discount = 20.0 if subtotal > 300 else 0.0
        total_amount = round(subtotal + tax + delivery_fee - discount, 2)

        order_status = statuses[i % len(statuses)]
        order_time = base_date + timedelta(days=(i // 2), hours=(i % 5))

        orders_data.append({
            "order_id": order_id,
            "user_id": user["user_id"],
            "restaurant_id": restaurant["restaurant_id"],
            "driver_id": driver["driver_id"] if order_status == "DELIVERED" else None,
            "order_status": order_status,
            "order_timestamp": order_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "items": [
                {
                    "item_id": selected_item["item_id"],
                    "item_name": selected_item["item_name"],
                    "quantity": quantity,
                    "unit_price": selected_item["price"]
                }
            ],
            "subtotal": subtotal,
            "tax": tax,
            "delivery_fee": delivery_fee,
            "discount": discount,
            "total_amount": total_amount
        })

        # Generate a corresponding payment record for completed orders.
        if order_status == "DELIVERED":
            payments_data.append({
                "payment_id": f"PAY_{i:03d}",
                "order_id": order_id,
                "payment_method": payment_methods[i % len(payment_methods)],
                "payment_status": "SUCCESS",
                "transaction_amount": total_amount,
                "payment_timestamp": (order_time + timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
            })

    orders_file_path = os.path.join(RAW_DATA_DIR, "orders.json")
    with open(orders_file_path, "w", encoding="utf-8") as f:
        json.dump(orders_data, f, indent=2)

    payments_file_path = os.path.join(RAW_DATA_DIR, "payments.json")
    with open(payments_file_path, "w", encoding="utf-8") as f:
        json.dump(payments_data, f, indent=2)

    print(f"[DATA GEN] Successfully created 6 sample JSON files in '{RAW_DATA_DIR}'.")


if __name__ == "__main__":
    # Execute sample data generation when this script is run directly.
    generate_all_sample_data()
