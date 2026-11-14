import os
import sys
from datetime import UTC, date, datetime, timedelta

import duckdb
import pandas as pd
import requests
from generate_orders import generate

DB = os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")
DAYS = 7

def upsert(con, table, df):
    con.register("df", df)
    con.execute(f"INSERT OR REPLACE INTO raw.{table} SELECT * FROM df")
    con.unregister("df")

def fetch_fx(start: date, end: date) -> pd.DataFrame:
    url = f"https://api.frankfurter.dev/v1/{start}..{end}"
    r = requests.get(url, params={"base": "EUR", "symbols": "USD"}, timeout=30)
    r.raise_for_status()
    rows = [{"rate_date": d, "base": "EUR", "quote": "USD", "rate": v["USD"]}
            for d, v in r.json()["rates"].items()]
    df = pd.DataFrame(rows)
    df["rate_date"] = pd.to_datetime(df["rate_date"]).dt.date
    return df

def main():
    os.makedirs(os.path.dirname(DB) or ".", exist_ok=True)
    con = duckdb.connect(DB)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute("""CREATE TABLE IF NOT EXISTS raw.orders(
        order_id VARCHAR PRIMARY KEY, customer_id VARCHAR, product_id VARCHAR,
        quantity INTEGER, amount DOUBLE, currency VARCHAR, created_at TIMESTAMP,
        ingested_at TIMESTAMPTZ)""")
    con.execute("""CREATE TABLE IF NOT EXISTS raw.products(
        product_id VARCHAR PRIMARY KEY, name VARCHAR, category VARCHAR,
        price DOUBLE, cost DOUBLE, ingested_at TIMESTAMPTZ)""")
    con.execute("""CREATE TABLE IF NOT EXISTS raw.fx_rates(
        rate_date DATE, base VARCHAR, quote VARCHAR, rate DOUBLE,
        ingested_at TIMESTAMPTZ, PRIMARY KEY(rate_date, base, quote))""")

    now = datetime.now(UTC)
    today = date.today()
    days = [today - timedelta(days=i) for i in range(DAYS)]

    orders = pd.concat([generate(d) for d in days], ignore_index=True)
    orders["ingested_at"] = now
    upsert(con, "orders", orders)

    products = pd.read_csv("data/products.csv")
    products["ingested_at"] = now
    upsert(con, "products", products)

    fx = fetch_fx(min(days), max(days))
    fx["ingested_at"] = now
    upsert(con, "fx_rates", fx)

    n = con.execute("select count(*) from raw.orders").fetchone()[0]
    print(f"OK: {n} commandes")

if __name__ == "__main__":
    sys.exit(main())
