"""
MNC-style database setup — e-commerce, finance, and HR operations.
Creates SQLite DB with 200-500 rows per table, seasonal patterns, and planted anomalies.
Run: python sql_agent/db_setup.py
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import random
import sqlite3
from datetime import datetime, timedelta

from faker import Faker
from loguru import logger

from config.settings import DB_PATH, ensure_directories

fake = Faker()
random.seed(42)
Faker.seed(42)

REGIONS = ["North", "South", "East", "West", "Central"]
SEGMENTS = ["Enterprise", "SMB", "Startup", "Government", "Education"]
STATUSES = ["completed", "pending", "shipped", "cancelled", "returned"]
CATEGORIES = ["Electronics", "Software", "Services", "Hardware", "Consulting"]
DEPARTMENTS = ["Engineering", "Sales", "Marketing", "Finance", "Operations", "HR"]
COST_CENTERS = ["CC-001", "CC-002", "CC-003", "CC-004", "CC-005"]


def _get_conn():
    ensure_directories()
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _seasonal_factor(dt: datetime) -> float:
    """Higher sales in Nov-Dec, lower in Jan-Feb."""
    month = dt.month
    factors = {1: 0.7, 2: 0.75, 3: 0.85, 4: 0.9, 5: 0.95, 6: 1.0,
               7: 1.0, 8: 1.05, 9: 1.1, 10: 1.15, 11: 1.3, 12: 1.5}
    return factors.get(month, 1.0)


def setup_database(force: bool = False) -> str:
    """Create and populate all tables. Returns DB path."""
    conn = _get_conn()
    c = conn.cursor()

    if force:
        for tbl in ["order_items", "orders", "products", "customers",
                    "sales_metrics", "employees", "budgets", "transactions"]:
            c.execute(f"DROP TABLE IF EXISTS {tbl}")

    # ── Customers ────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        region TEXT,
        segment TEXT,
        created_date TEXT,
        lifetime_value REAL DEFAULT 0,
        churn_risk REAL DEFAULT 0
    )""")

    c.execute("SELECT COUNT(*) FROM customers")
    if c.fetchone()[0] == 0:
        customers = []
        for i in range(1, 401):
            created = fake.date_between(start_date="-3y", end_date="today")
            ltv = round(random.uniform(500, 150000), 2)
            customers.append((
                i, fake.company(), fake.company_email(),
                random.choice(REGIONS), random.choice(SEGMENTS),
                str(created), ltv, round(random.uniform(0, 1), 2)
            ))
        c.executemany(
            "INSERT OR IGNORE INTO customers VALUES (?,?,?,?,?,?,?,?)", customers
        )
        logger.info(f"Inserted {len(customers)} customers")

    # ── Products ─────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        price REAL,
        cost REAL,
        stock_quantity INTEGER,
        sku TEXT UNIQUE
    )""")

    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        product_names = [
            "NexusPro Suite", "DataBridge Connector", "CloudVault Storage",
            "AI Analyst Lite", "AI Analyst Pro", "SecureEdge Firewall",
            "SmartDash BI", "AutoReport Engine", "VoiceBot Platform",
            "DevOps Toolkit", "CRM Accelerator", "ERP Integrator",
            "Mobile MDM Suite", "Compliance Scanner", "Network Monitor Pro",
            "Backup & Recovery", "API Gateway", "Identity Manager",
            "Load Balancer X", "Data Warehouse Kit",
        ]
        products = []
        for i, name in enumerate(product_names, 1):
            price = round(random.uniform(99, 9999), 2)
            products.append((
                i, name, random.choice(CATEGORIES),
                price, round(price * random.uniform(0.3, 0.6), 2),
                random.randint(0, 500), f"SKU-{i:04d}"
            ))
        c.executemany(
            "INSERT OR IGNORE INTO products VALUES (?,?,?,?,?,?,?)", products
        )
        logger.info(f"Inserted {len(products)} products")

    # ── Orders ────────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        order_date TEXT,
        status TEXT,
        total_amount REAL,
        region TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )""")

    c.execute("SELECT COUNT(*) FROM orders")
    if c.fetchone()[0] == 0:
        orders = []
        for i in range(1, 501):
            cust_id = random.randint(1, 400)
            order_dt = fake.date_between(start_date="-2y", end_date="today")
            sf = _seasonal_factor(datetime.combine(order_dt, datetime.min.time()))
            amount = round(random.uniform(200, 50000) * sf, 2)
            orders.append((
                i, cust_id, str(order_dt),
                random.choice(STATUSES), amount,
                random.choice(REGIONS)
            ))
        c.executemany(
            "INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?)", orders
        )
        logger.info(f"Inserted {len(orders)} orders")

    # ── Order Items ───────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        unit_price REAL,
        FOREIGN KEY(order_id) REFERENCES orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    )""")

    c.execute("SELECT COUNT(*) FROM order_items")
    if c.fetchone()[0] == 0:
        items = []
        item_id = 1
        for order_id in range(1, 501):
            n_items = random.randint(1, 4)
            for _ in range(n_items):
                prod_id = random.randint(1, 20)
                qty = random.randint(1, 10)
                price = round(random.uniform(99, 9999), 2)
                items.append((item_id, order_id, prod_id, qty, price))
                item_id += 1
        c.executemany(
            "INSERT OR IGNORE INTO order_items VALUES (?,?,?,?,?)", items
        )
        logger.info(f"Inserted {len(items)} order items")

    # ── Sales Metrics (with anomalies planted) ────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS sales_metrics (
        id INTEGER PRIMARY KEY,
        date TEXT,
        region TEXT,
        revenue REAL,
        units_sold INTEGER,
        returns INTEGER,
        metric_type TEXT
    )""")

    c.execute("SELECT COUNT(*) FROM sales_metrics")
    if c.fetchone()[0] == 0:
        metrics = []
        metric_id = 1
        today = datetime.today()
        # Generate last 90 days of daily data per region
        anomaly_dates = {
            "South": today.date(),       # most recent day → monitor catches it
            "East": (today - timedelta(days=1)).date(),
        }
        for day_offset in range(90, -1, -1):
            dt = today - timedelta(days=day_offset)
            sf = _seasonal_factor(dt)
            for region in REGIONS:
                base_rev = random.uniform(5000, 20000) * sf
                # Plant anomalies — sudden drops
                if region in anomaly_dates and dt.date() == anomaly_dates[region]:
                    base_rev *= 0.30  # 70% drop
                revenue = round(base_rev, 2)
                units = int(random.uniform(10, 200) * sf)
                returns = int(units * random.uniform(0.01, 0.05))
                metrics.append((
                    metric_id, str(dt.date()), region,
                    revenue, units, returns, "daily"
                ))
                metric_id += 1
        c.executemany(
            "INSERT OR IGNORE INTO sales_metrics VALUES (?,?,?,?,?,?,?)", metrics
        )
        logger.info(f"Inserted {len(metrics)} sales metric rows with anomalies planted")

    # ── Employees ─────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        name TEXT,
        department TEXT,
        role TEXT,
        salary REAL,
        hire_date TEXT,
        region TEXT,
        performance_score REAL
    )""")

    c.execute("SELECT COUNT(*) FROM employees")
    if c.fetchone()[0] == 0:
        employees = []
        for i in range(1, 251):
            salary = round(random.uniform(40000, 200000), 2)
            employees.append((
                i, fake.name(), random.choice(DEPARTMENTS),
                fake.job(), salary,
                str(fake.date_between(start_date="-10y", end_date="today")),
                random.choice(REGIONS),
                round(random.uniform(2.0, 5.0), 1)
            ))
        c.executemany(
            "INSERT OR IGNORE INTO employees VALUES (?,?,?,?,?,?,?,?)", employees
        )
        logger.info(f"Inserted {len(employees)} employees")

    # ── Budgets ───────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY,
        department TEXT,
        cost_center TEXT,
        fiscal_year INTEGER,
        quarter INTEGER,
        allocated REAL,
        spent REAL,
        category TEXT
    )""")

    c.execute("SELECT COUNT(*) FROM budgets")
    if c.fetchone()[0] == 0:
        budgets = []
        bid = 1
        for dept in DEPARTMENTS:
            for year in [2023, 2024, 2025]:
                for quarter in [1, 2, 3, 4]:
                    allocated = round(random.uniform(50000, 500000), 2)
                    spent = round(allocated * random.uniform(0.6, 1.1), 2)
                    budgets.append((
                        bid, dept, random.choice(COST_CENTERS),
                        year, quarter, allocated, spent,
                        random.choice(["OpEx", "CapEx", "R&D", "Marketing"])
                    ))
                    bid += 1
        c.executemany(
            "INSERT OR IGNORE INTO budgets VALUES (?,?,?,?,?,?,?,?)", budgets
        )
        logger.info(f"Inserted {len(budgets)} budget records")

    # ── Transactions ──────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        date TEXT,
        type TEXT,
        amount REAL,
        currency TEXT,
        department TEXT,
        description TEXT,
        approved_by TEXT
    )""")

    c.execute("SELECT COUNT(*) FROM transactions")
    if c.fetchone()[0] == 0:
        tx_types = ["invoice", "payment", "refund", "expense", "payroll"]
        transactions = []
        for i in range(1, 401):
            dt = fake.date_between(start_date="-1y", end_date="today")
            transactions.append((
                i, str(dt), random.choice(tx_types),
                round(random.uniform(100, 250000), 2),
                random.choice(["USD", "EUR", "GBP", "INR"]),
                random.choice(DEPARTMENTS),
                fake.sentence(nb_words=6),
                fake.name()
            ))
        c.executemany(
            "INSERT OR IGNORE INTO transactions VALUES (?,?,?,?,?,?,?,?)", transactions
        )
        logger.info(f"Inserted {len(transactions)} transactions")

    conn.commit()
    conn.close()

    # Summary
    conn2 = sqlite3.connect(DB_PATH)
    c2 = conn2.cursor()
    print("\n" + "="*50)
    print("DATABASE SETUP COMPLETE")
    print("="*50)
    for tbl in ["customers", "products", "orders", "order_items",
                "sales_metrics", "employees", "budgets", "transactions"]:
        c2.execute(f"SELECT COUNT(*) FROM {tbl}")
        count = c2.fetchone()[0]
        print(f"  {tbl:20s}: {count:>5} rows")
    print(f"\n  Location: {DB_PATH}")
    print("  Anomalies planted in: South (today), East (yesterday)")
    print("="*50)
    conn2.close()
    return DB_PATH


if __name__ == "__main__":
    setup_database(force="--force" in sys.argv)
