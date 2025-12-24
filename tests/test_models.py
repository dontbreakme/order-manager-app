import unittest
from datetime import datetime

from shop_manager.models import Customer, Product, Order, OrderItem, ValidationError
from shop_manager.sorting_utils import merge_sort


class TestModels(unittest.TestCase):
    def test_customer_validation(self):
        with self.assertRaises(ValidationError):
            Customer(_name="")  # empty
        with self.assertRaises(ValidationError):
            Customer(_name="Ivan", _email="bad-email")

        c = Customer(_name="Ivan", _email="ivan@example.com", _phone="+371 12345678")
        self.assertEqual(c.name, "Ivan")

    def test_product_validation(self):
        with self.assertRaises(ValidationError):
            Product(_title="", _price=10)
        with self.assertRaises(ValidationError):
            Product(_title="A", _price=-1)

        p = Product(_title="Mouse", _price="12.5")
        self.assertAlmostEqual(p.price, 12.5, places=2)

    def test_order_total(self):
        o = Order(customer_id=1, created_at=datetime(2025,1,1))
        o.add_item(OrderItem(product_id=1, product_title="A", unit_price=10, quantity=2))
        o.add_item(OrderItem(product_id=2, product_title="B", unit_price=5, quantity=1))
        self.assertAlmostEqual(o.total, 25.0, places=2)

    def test_merge_sort(self):
        data = [{"total": 10}, {"total": 3}, {"total": 7}]
        sorted_data = merge_sort(data, key=lambda x: x["total"])
        self.assertEqual([d["total"] for d in sorted_data], [3,7,10])
        sorted_desc = merge_sort(data, key=lambda x: x["total"], reverse=True)
        self.assertEqual([d["total"] for d in sorted_desc], [10,7,3])


if __name__ == "__main__":
    unittest.main()
