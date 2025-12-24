import unittest
from pathlib import Path
import os
import tempfile

from shop_manager.db import Database
from shop_manager.models import Customer, Product, Order, OrderItem
from shop_manager.analysis import top_customers_by_orders, orders_dynamics_by_date, customer_relationship_graph


class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test.sqlite"
        self.db = Database(self.db_path)
        self.db.connect()

        # seed data
        c1 = Customer(_name="Alice", _email="alice@example.com", _phone="+11111111")
        c2 = Customer(_name="Bob", _email="bob@example.com", _phone="+22222222")
        c1.id = self.db.add_customer(c1)
        c2.id = self.db.add_customer(c2)

        p1 = Product(_title="Keyboard", _price=50)
        p2 = Product(_title="Mouse", _price=20)
        p1.id = self.db.add_product(p1)
        p2.id = self.db.add_product(p2)

        o1 = Order(customer_id=c1.id); o1.add_item(OrderItem(product_id=p1.id, product_title=p1.title, unit_price=p1.price, quantity=1))
        o2 = Order(customer_id=c1.id); o2.add_item(OrderItem(product_id=p2.id, product_title=p2.title, unit_price=p2.price, quantity=2))
        o3 = Order(customer_id=c2.id); o3.add_item(OrderItem(product_id=p2.id, product_title=p2.title, unit_price=p2.price, quantity=1))
        self.db.add_order(o1); self.db.add_order(o2); self.db.add_order(o3)

    def tearDown(self):
        self.db.close()
        self.tmpdir.cleanup()

    def test_reports_create_files(self):
        out_dir = Path(self.tmpdir.name) / "reports"
        p1 = top_customers_by_orders(self.db, out_dir)
        p2 = orders_dynamics_by_date(self.db, out_dir)
        p3 = customer_relationship_graph(self.db, out_dir)
        self.assertTrue(p1.exists())
        self.assertTrue(p2.exists())
        self.assertTrue(p3.exists())


if __name__ == "__main__":
    unittest.main()
