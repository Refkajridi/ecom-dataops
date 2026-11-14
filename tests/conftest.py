import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ingestion"))
from generate_orders import generate


@pytest.fixture(scope="session")
def con():
    c = duckdb.connect(":memory:")
    c.execute("CREATE SCHEMA raw")
    c.execute("""CREATE TABLE raw.orders(
        order_id VARCHAR PRIMARY KEY, customer_id VARCHAR, product_id VARCHAR,
        quantity INTEGER, amount DOUBLE, currency VARCHAR, created_at TIMESTAMP,
        ingested_at TIMESTAMPTZ)""")
    c.execute("""CREATE TABLE raw.products(
        product_id VARCHAR PRIMARY KEY, name VARCHAR, category VARCHAR,
        price DOUBLE, cost DOUBLE, ingested_at TIMESTAMPTZ)""")

    import os
    os.chdir(ROOT)  # generate() lit data/products.csv en relatif
    days = [date(2026, 11, 1) + timedelta(days=i) for i in range(3)]
    orders = pd.concat([generate(d) for d in days], ignore_index=True)
    orders["ingested_at"] = pd.Timestamp.now(tz="UTC")
    c.register("orders_df", orders)
    c.execute("INSERT INTO raw.orders SELECT * FROM orders_df")

    products = pd.read_csv(ROOT / "data" / "products.csv")
    products["ingested_at"] = pd.Timestamp.now(tz="UTC")
    c.register("products_df", products)
    c.execute("INSERT INTO raw.products SELECT * FROM products_df")
    return c