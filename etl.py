# -*- coding: utf-8 -*-
"""
ETL pipeline to fetch products and carts data from DummyJSON API,
transform and enrich the datasets, and load them into a SQLite database.
"""

from datetime import datetime, timedelta
import io
import random
import sqlite3
import sys
import pandas as pd
import requests

# Force stdout to use UTF-8 for proper emoji/special character output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ensure reproducibility for simulated order dates
random.seed(42)

print("=" * 60)
print("  ETL Pipeline - Sales Analytics")
print("=" * 60)

# ---------------------------------------------------------
# 1. EXTRACT
# ---------------------------------------------------------
print("\n[1/4] Extracting data from API...")

# Fetch products
products_url = (
    "https://dummyjson.com/products"
    "?limit=100&skip=0"
    "&select=id,title,price,discountPercentage,rating,stock,category,brand"
)
try:
    response = requests.get(products_url, timeout=10)
    response.raise_for_status()
    raw_products = response.json()["products"]
    print(f"  - Products retrieved: {len(raw_products)}")
except Exception as e:
    print(f"  - Error fetching products: {e}")
    sys.exit(1)

# Fetch carts (used as orders)
carts_url = "https://dummyjson.com/carts?limit=100"
try:
    response = requests.get(carts_url, timeout=10)
    response.raise_for_status()
    raw_carts = response.json()["carts"]
    print(f"  - Carts/Orders retrieved: {len(raw_carts)}")
except Exception as e:
    print(f"  - Error fetching carts: {e}")
    sys.exit(1)


# ---------------------------------------------------------
# 2. TRANSFORM
# ---------------------------------------------------------
print("\n[2/4] Transforming data...")

# Transform products table
df_products = pd.DataFrame(raw_products)
df_products = df_products.rename(columns={
    "id":                 "product_id",
    "title":              "product_name",
    "price":              "price_usd",
    "discountPercentage": "discount_pct",
    "rating":             "avg_rating",
    "stock":              "units_in_stock",
    "category":           "category",
    "brand":              "brand",
})

# Calculate pricing and margins
df_products["discounted_price"] = (
    df_products["price_usd"] * (1 - df_products["discount_pct"] / 100)
).round(2)

df_products["cost_price"] = (df_products["price_usd"] * 0.55).round(2)
df_products["profit_per_unit"] = (
    df_products["discounted_price"] - df_products["cost_price"]
).round(2)

# Drop missing critical fields & clean up category names
df_products = df_products.dropna(subset=["product_id", "price_usd", "category"])
df_products["category"] = df_products["category"].str.replace("-", " ").str.title()

print(f"  - Products table shape: {df_products.shape}")

# Transform orders table
order_rows = []
for cart in raw_carts:
    cart_id = cart["id"]
    user_id = cart["userId"]

    # Simulate a realistic purchase date in the last 6 months
    days_ago = random.randint(0, 180)
    order_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    for item in cart["products"]:
        order_rows.append({
            "order_id": cart_id,
            "user_id": user_id,
            "order_date": order_date,
            "product_id": item["id"],
            "product_name": item["title"],
            "quantity": item["quantity"],
            "unit_price": item["price"],
        })

df_orders = pd.DataFrame(order_rows)
df_orders["revenue"] = (df_orders["unit_price"] * df_orders["quantity"]).round(2)

# Enrich orders with product metadata
df_orders = df_orders.merge(
    df_products[["product_id", "category", "discount_pct", "profit_per_unit", "brand"]],
    on="product_id",
    how="left"
)

df_orders["profit"] = (df_orders["profit_per_unit"] * df_orders["quantity"]).round(2)
df_orders["order_date"] = pd.to_datetime(df_orders["order_date"])
df_orders = df_orders.sort_values("order_date").reset_index(drop=True)

# Drop incomplete records
df_orders = df_orders.dropna(subset=["order_id", "product_id", "revenue", "category", "profit"])

print(f"  - Orders table shape: {df_orders.shape}")


# ---------------------------------------------------------
# 3. LOAD
# ---------------------------------------------------------
print("\n[3/4] Loading to SQLite...")

DB_PATH = "data.db"
try:
    conn = sqlite3.connect(DB_PATH)
    df_products.to_sql("products", conn, if_exists="replace", index=False)
    df_orders.to_sql("orders", conn, if_exists="replace", index=False)
    conn.close()
    print(f"  - Tables successfully saved to {DB_PATH}")
except Exception as e:
    print(f"  - Database write failed: {e}")
    sys.exit(1)


# ---------------------------------------------------------
# 4. VERIFY
# ---------------------------------------------------------
print("\n[4/4] Verifying stored data...")

try:
    conn = sqlite3.connect(DB_PATH)
    verify_products = pd.read_sql("SELECT COUNT(*) AS total_products FROM products", conn)
    verify_orders   = pd.read_sql("SELECT COUNT(*) AS total_orders   FROM orders",   conn)
    verify_revenue  = pd.read_sql("SELECT ROUND(SUM(revenue), 2) AS total_revenue FROM orders", conn)
    verify_cats     = pd.read_sql("SELECT DISTINCT category FROM products ORDER BY category", conn)
    conn.close()

    print(f"  - Products in DB: {verify_products['total_products'][0]}")
    print(f"  - Orders in DB:   {verify_orders['total_orders'][0]}")
    print(f"  - Total Revenue:  ${verify_revenue['total_revenue'][0]:,.2f}")
    print(f"  - Categories:     {list(verify_cats['category'])}")
except Exception as e:
    print(f"  - Data verification failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("  ETL completed successfully!")
print("=" * 60)
