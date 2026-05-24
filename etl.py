# -*- coding: utf-8 -*-
"""
etl.py — The ETL Pipeline
==========================
ETL stands for Extract, Transform, Load.
This file does three things in order:
  1. EXTRACT  → Downloads business data from a free public API
  2. TRANSFORM → Cleans and reshapes the data using pandas
  3. LOAD      → Saves the clean data into a SQLite database (data.db)

We use the DummyJSON API (https://dummyjson.com/) which gives us
realistic e-commerce data: products, categories, prices, and orders.
No API key needed — it's completely free!
"""

# ── Imports ──────────────────────────────────────────────────────────────────
import requests          # lets us make HTTP calls to the internet (download data)
import pandas as pd      # the go-to Python library for working with tables of data
import sqlite3           # built into Python — lets us create and query SQLite databases
import random            # built into Python — we'll use this to generate fake order dates
import sys, io
# Force stdout to use UTF-8 so emoji/special characters print correctly on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from datetime import datetime, timedelta  # for working with dates and times

# Set a random seed so the "random" dates are the same every time we run the script
# (makes results reproducible — a good practice in data engineering)
random.seed(42)

print("=" * 60)
print("  ETL PIPELINE — Business Sales Analytics")
print("=" * 60)


# ══════════════════════════════════════════════════════════════
# PHASE 1: EXTRACT
# Download raw data from the DummyJSON API
# ══════════════════════════════════════════════════════════════
print("\n[EXTRACT]  PHASE 1: EXTRACT")
print("-" * 40)

# --- Extract Products ---
# We ask the API for all 100 products using requests.get()
# The URL parameters (?limit=100&skip=0&select=...) tell the API
# exactly which fields we want back — less data to download!
products_url = (
    "https://dummyjson.com/products"
    "?limit=100&skip=0"
    "&select=id,title,price,discountPercentage,rating,stock,category,brand"
)

print(f"  → Fetching products from: {products_url}")
products_response = requests.get(products_url, timeout=10)  # timeout=10 means "give up after 10 seconds"

# .raise_for_status() will throw an error if the request failed (e.g. 404 Not Found)
products_response.raise_for_status()

# The API returns JSON — we convert it to a Python dictionary with .json()
products_json = products_response.json()

# The actual list of products is inside the "products" key of the response
raw_products = products_json["products"]

print(f"  ✅ Products fetched:  {len(raw_products)} records")

# --- Extract Carts (Orders) ---
# "Carts" in DummyJSON represent shopping orders made by customers
carts_url = "https://dummyjson.com/carts?limit=100"

print(f"  → Fetching carts (orders) from: {carts_url}")
carts_response = requests.get(carts_url, timeout=10)
carts_response.raise_for_status()

carts_json = carts_response.json()
raw_carts = carts_json["carts"]

print(f"  ✅ Carts (orders) fetched: {len(raw_carts)} records")


# ══════════════════════════════════════════════════════════════
# PHASE 2: TRANSFORM
# Clean, reshape, and enrich the raw data
# ══════════════════════════════════════════════════════════════
print("\n[TRANSFORM]  PHASE 2: TRANSFORM")
print("-" * 40)

# ─── 2a. Transform Products Table ────────────────────────────

# Convert the list of product dictionaries into a pandas DataFrame
# A DataFrame is like an Excel spreadsheet — rows and columns
df_products = pd.DataFrame(raw_products)

# Rename columns to be more readable and business-friendly
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

# Calculate the price after applying the discount
# Formula: discounted_price = price × (1 - discount% / 100)
df_products["discounted_price"] = (
    df_products["price_usd"] * (1 - df_products["discount_pct"] / 100)
).round(2)  # round to 2 decimal places (like real currency)

# Estimate a cost price — in a real business this comes from suppliers
# Here we assume the cost is 55% of the selling price (a 45% gross margin)
df_products["cost_price"] = (df_products["price_usd"] * 0.55).round(2)

# Calculate estimated profit per unit sold (after discount)
df_products["profit_per_unit"] = (
    df_products["discounted_price"] - df_products["cost_price"]
).round(2)

# Drop rows where any key column is missing (NaN = Not a Number = missing value)
df_products = df_products.dropna(subset=["product_id", "price_usd", "category"])

# Make category names look nicer (capitalise first letter of each word)
df_products["category"] = df_products["category"].str.replace("-", " ").str.title()

print(f"  ✅ Products table: {df_products.shape[0]} rows × {df_products.shape[1]} columns")
print(f"     Columns: {list(df_products.columns)}")
print(f"\n  Sample (first 3 rows):")
print(df_products[["product_name", "category", "price_usd", "discounted_price", "profit_per_unit"]].head(3).to_string(index=False))


# ─── 2b. Transform Orders Table ──────────────────────────────

# Each cart contains a list of items — we need to "explode" this
# "Exploding" means turning one row with a list into multiple rows,
# one per item in the list.
order_rows = []  # we'll collect individual order line items here

for cart in raw_carts:
    cart_id  = cart["id"]       # unique order ID
    user_id  = cart["userId"]   # which customer placed the order

    # Simulate a random order date in the last 180 days (6 months)
    # timedelta(days=...) subtracts a number of days from today's date
    days_ago   = random.randint(0, 180)
    order_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    # Loop through every product in this cart
    for item in cart["products"]:
        order_rows.append({
            "order_id":    cart_id,
            "user_id":     user_id,
            "order_date":  order_date,
            "product_id":  item["id"],
            "product_name": item["title"],
            "quantity":    item["quantity"],
            "unit_price":  item["price"],      # price at time of purchase
        })

# Convert the list of order dictionaries into a DataFrame
df_orders = pd.DataFrame(order_rows)

# Calculate the total revenue for each line item
# Revenue = how much money we received = unit_price × quantity
df_orders["revenue"] = (df_orders["unit_price"] * df_orders["quantity"]).round(2)

# Join (merge) orders with the products table to bring in category and profit info
# This is like a SQL JOIN — matching rows where product_id is the same in both tables
df_orders = df_orders.merge(
    df_products[["product_id", "category", "discount_pct", "profit_per_unit", "brand"]],
    on="product_id",     # the column to match on
    how="left"           # keep all orders even if a product isn't in the products table
)

# Calculate the estimated profit for each line item
df_orders["profit"] = (df_orders["profit_per_unit"] * df_orders["quantity"]).round(2)

# Convert order_date from a string to a proper datetime object
# This lets us do date-based filtering later (e.g. "show orders from last 30 days")
df_orders["order_date"] = pd.to_datetime(df_orders["order_date"])

# Sort orders from oldest to newest (chronological order)
df_orders = df_orders.sort_values("order_date").reset_index(drop=True)

# Drop rows missing critical data, including rows where the product
# wasn't found in our catalog (category = NaN after the JOIN)
df_orders = df_orders.dropna(subset=["order_id", "product_id", "revenue", "category", "profit"])

print(f"\n  ✅ Orders table:   {df_orders.shape[0]} rows × {df_orders.shape[1]} columns")
print(f"     Columns: {list(df_orders.columns)}")
print(f"\n  Sample (first 3 rows):")
print(df_orders[["order_id", "order_date", "product_name", "category", "quantity", "revenue", "profit"]].head(3).to_string(index=False))


# ══════════════════════════════════════════════════════════════
# PHASE 3: LOAD
# Save the clean DataFrames into a SQLite database (data.db)
# ══════════════════════════════════════════════════════════════
print("\n[LOAD]  PHASE 3: LOAD")
print("-" * 40)

# sqlite3.connect() creates the database file if it doesn't exist yet
# Think of it like opening (or creating) an Excel workbook
DB_PATH = "data.db"
conn = sqlite3.connect(DB_PATH)

# df.to_sql() writes a DataFrame as a table inside the database
# if_exists="replace" means: overwrite the table if it already exists
# index=False means: don't write the DataFrame's row numbers as a column
df_products.to_sql("products", conn, if_exists="replace", index=False)
print(f"  ✅ 'products' table saved → {len(df_products)} rows")

df_orders.to_sql("orders", conn, if_exists="replace", index=False)
print(f"  ✅ 'orders'   table saved → {len(df_orders)} rows")

# Always close the connection when you're done — like saving and closing a file
conn.close()

print(f"\n  ✅ Database saved to: {DB_PATH}")


# ══════════════════════════════════════════════════════════════
# PHASE 4: VERIFY
# Read back from the database to confirm everything was saved correctly
# ══════════════════════════════════════════════════════════════
print("\n[VERIFY]  PHASE 4: VERIFY (reading back from data.db)")
print("-" * 40)

# Reconnect and run a quick SQL query to check the data is there
conn = sqlite3.connect(DB_PATH)

# pd.read_sql() runs a SQL query and returns the result as a DataFrame
verify_products = pd.read_sql("SELECT COUNT(*) AS total_products FROM products", conn)
verify_orders   = pd.read_sql("SELECT COUNT(*) AS total_orders   FROM orders",   conn)
verify_revenue  = pd.read_sql("SELECT ROUND(SUM(revenue), 2) AS total_revenue FROM orders", conn)
verify_cats     = pd.read_sql("SELECT DISTINCT category FROM products ORDER BY category", conn)

conn.close()

print(f"  Products in database : {verify_products['total_products'][0]}")
print(f"  Orders in database   : {verify_orders['total_orders'][0]}")
print(f"  Total revenue (all)  : ${verify_revenue['total_revenue'][0]:,.2f}")
print(f"  Categories           : {list(verify_cats['category'])}")

print("\n" + "=" * 60)
print("  >>> ETL COMPLETE! data.db is ready for the dashboard.")
print("=" * 60)
