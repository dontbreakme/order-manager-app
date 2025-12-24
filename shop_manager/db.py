"""
shop_manager.db
===============

SQLite storage layer + import/export (CSV/JSON).

Schema
------
customers(id, name, email, phone)
products(id, title, price)
orders(id, customer_id, created_at)
order_items(id, order_id, product_id, unit_price, quantity)

Notes
-----
All operations use parameterized SQL to avoid SQL injection.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import Customer, Product, Order, OrderItem


class Database:
    """SQLite database wrapper."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Open connection and initialize schema if needed."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self._init_schema()

    @property
    def conn(self) -> sqlite3.Connection:
        """Active SQLite connection."""
        if self._conn is None:
            self.connect()
        assert self._conn is not None
        return self._conn

    def close(self) -> None:
        """Close connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT
            );

            CREATE TABLE IF NOT EXISTS products(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS order_items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id)
            );
            """
        )
        self.conn.commit()

    # -------------------- Customers --------------------

    def add_customer(self, customer: Customer) -> int:
        """Insert a customer and return id."""
        cur = self.conn.execute(
            "INSERT INTO customers(name, email, phone) VALUES(?,?,?)",
            (customer.name, customer.email, customer.phone),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_customers(self) -> List[Customer]:
        """Return all customers."""
        rows = self.conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
        out: List[Customer] = []
        for r in rows:
            out.append(Customer(id=r["id"], _name=r["name"], _email=r["email"] or "", _phone=r["phone"] or ""))
        return out

    # -------------------- Products --------------------

    def add_product(self, product: Product) -> int:
        """Insert a product and return id."""
        cur = self.conn.execute(
            "INSERT INTO products(title, price) VALUES(?,?)",
            (product.title, float(product.price)),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list_products(self) -> List[Product]:
        """Return all products."""
        rows = self.conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
        return [Product(id=r["id"], _title=r["title"], _price=r["price"]) for r in rows]

    # -------------------- Orders --------------------

    def add_order(self, order: Order) -> int:
        """Insert an order with items and return order id."""
        cur = self.conn.execute(
            "INSERT INTO orders(customer_id, created_at) VALUES(?,?)",
            (order.customer_id, order.created_at.isoformat(timespec="seconds")),
        )
        order_id = int(cur.lastrowid)
        for it in order.items:
            self.conn.execute(
                "INSERT INTO order_items(order_id, product_id, unit_price, quantity) VALUES(?,?,?,?)",
                (order_id, it.product_id, float(it.unit_price), int(it.quantity)),
            )
        self.conn.commit()
        return order_id

    def list_orders(self) -> List[Dict[str, Any]]:
        """
        List orders with computed total and customer name.

        Returns
        -------
        list[dict]
            {id, customer_id, customer_name, created_at, total}
        """
        rows = self.conn.execute(
            """
            SELECT o.id, o.customer_id, c.name AS customer_name, o.created_at,
                   IFNULL(SUM(oi.unit_price * oi.quantity), 0) AS total
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            LEFT JOIN order_items oi ON oi.order_id = o.id
            GROUP BY o.id
            ORDER BY o.id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def get_order_items(self, order_id: int) -> List[OrderItem]:
        """Get order items."""
        rows = self.conn.execute(
            """
            SELECT oi.*, p.title AS product_title
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            ORDER BY oi.id
            """,
            (order_id,),
        ).fetchall()
        return [
            OrderItem(
                id=r["id"],
                product_id=r["product_id"],
                product_title=r["product_title"],
                unit_price=r["unit_price"],
                quantity=r["quantity"],
            )
            for r in rows
        ]

    # -------------------- Export / Import --------------------

    def export_json(self, path: str | Path) -> None:
        """Export DB contents to JSON."""
        data = {
            "customers": [c.to_dict() for c in self.list_customers()],
            "products": [p.to_dict() for p in self.list_products()],
            "orders": [],
        }
        for o in self.list_orders():
            oid = int(o["id"])
            data["orders"].append({
                "id": oid,
                "customer_id": int(o["customer_id"]),
                "created_at": o["created_at"],
                "total": float(o["total"]),
                "items": [it.to_dict() for it in self.get_order_items(oid)],
            })
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def export_csv(self, folder: str | Path) -> None:
        """Export each table to separate CSV files inside folder."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)

        def write_csv(filename: str, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
            with (folder / filename).open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                w.writeheader()
                for r in rows:
                    w.writerow(r)

        customers = [c.to_dict() for c in self.list_customers()]
        products = [p.to_dict() for p in self.list_products()]
        orders = self.list_orders()
        items = []
        for o in orders:
            for it in self.get_order_items(int(o["id"])):
                d = it.to_dict()
                d["order_id"] = int(o["id"])
                items.append(d)

        write_csv("customers.csv", customers, ["id", "name", "email", "phone"])
        write_csv("products.csv", products, ["id", "title", "price"])
        write_csv("orders.csv", orders, ["id", "customer_id", "customer_name", "created_at", "total"])
        write_csv("order_items.csv", items, ["id", "order_id", "product_id", "product_title", "unit_price", "quantity", "line_total"])

    def import_json(self, path: str | Path, clear_first: bool = False) -> None:
        """Import from JSON created by export_json()."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if clear_first:
            self._clear_all()

        # Keep mapping old->new ids (because AUTOINCREMENT)
        cust_map: Dict[int, int] = {}
        prod_map: Dict[int, int] = {}

        for c in data.get("customers", []):
            cust = Customer(_name=c["name"], _email=c.get("email", ""), _phone=c.get("phone", ""))
            new_id = self.add_customer(cust)
            cust_map[int(c.get("id") or new_id)] = new_id

        for p in data.get("products", []):
            prod = Product(_title=p["title"], _price=p["price"])
            new_id = self.add_product(prod)
            prod_map[int(p.get("id") or new_id)] = new_id

        for o in data.get("orders", []):
            created_at = datetime.fromisoformat(o["created_at"])
            order = Order(customer_id=cust_map.get(int(o["customer_id"]), int(o["customer_id"])), created_at=created_at)
            for it in o.get("items", []):
                order.add_item(OrderItem(
                    product_id=prod_map.get(int(it["product_id"]), int(it["product_id"])),
                    product_title=it.get("product_title", ""),
                    unit_price=float(it["unit_price"]),
                    quantity=int(it["quantity"]),
                ))
            self.add_order(order)

    def _clear_all(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            DELETE FROM order_items;
            DELETE FROM orders;
            DELETE FROM products;
            DELETE FROM customers;
            """
        )
        self.conn.commit()
