"""
shop_manager.models
===================

Data models for a small order-management system.

The project demonstrates OOP principles:
- Encapsulation: private attributes with properties + validation
- Inheritance: Person -> Customer
- Polymorphism: to_dict() overridden by subclasses
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import re


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-\(\)]{7,}$")


class ValidationError(ValueError):
    """Raised when validation fails."""


@dataclass
class BaseEntity:
    """
    Base entity with a numeric id.

    Notes
    -----
    Subclasses may override :meth:`to_dict` (polymorphism).
    """
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entity into a JSON-serializable dict."""
        return {"id": self.id}


@dataclass
class Person(BaseEntity):
    """A generic person entity."""
    _name: str = field(default="", repr=False)

    @property
    def name(self) -> str:
        """Person name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        value = (value or "").strip()
        if not value:
            raise ValidationError("Имя не может быть пустым.")
        self._name = value

    def __post_init__(self) -> None:
        if self._name:
            # validate initial value
            self.name = self._name

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"name": self.name})
        return d


@dataclass
class Customer(Person):
    """Customer with contact data."""
    _email: str = field(default="", repr=False)
    _phone: str = field(default="", repr=False)

    @property
    def email(self) -> str:
        """Customer email."""
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        value = (value or "").strip()
        if value and not EMAIL_RE.match(value):
            raise ValidationError("Некорректный email.")
        self._email = value

    @property
    def phone(self) -> str:
        """Customer phone."""
        return self._phone

    @phone.setter
    def phone(self, value: str) -> None:
        value = (value or "").strip()
        if value and not PHONE_RE.match(value):
            raise ValidationError("Некорректный номер телефона.")
        self._phone = value

    def __post_init__(self) -> None:
        super().__post_init__()
        if self._email:
            self.email = self._email
        if self._phone:
            self.phone = self._phone

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"email": self.email, "phone": self.phone})
        return d


@dataclass
class Product(BaseEntity):
    """Product in catalog."""
    _title: str = field(default="", repr=False)
    _price: float = field(default=0.0, repr=False)

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        value = (value or "").strip()
        if not value:
            raise ValidationError("Название товара не может быть пустым.")
        self._title = value

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        try:
            v = float(value)
        except Exception as e:
            raise ValidationError("Цена должна быть числом.") from e
        if v < 0:
            raise ValidationError("Цена не может быть отрицательной.")
        self._price = round(v, 2)

    def __post_init__(self) -> None:
        if self._title:
            self.title = self._title
        self.price = self._price

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({"title": self.title, "price": self.price})
        return d


@dataclass
class OrderItem(BaseEntity):
    """Line item inside an order."""
    product_id: int = 0
    product_title: str = ""
    unit_price: float = 0.0
    quantity: int = 1

    @property
    def line_total(self) -> float:
        """Total cost for this line."""
        return round(self.unit_price * self.quantity, 2)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "product_id": self.product_id,
            "product_title": self.product_title,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "line_total": self.line_total,
        })
        return d


@dataclass
class Order(BaseEntity):
    """Customer order."""
    customer_id: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    items: List[OrderItem] = field(default_factory=list)

    @property
    def total(self) -> float:
        """Order total."""
        return round(sum(i.line_total for i in self.items), 2)

    def add_item(self, item: OrderItem) -> None:
        """Add an item (simple business rule: quantity >= 1)."""
        if item.quantity < 1:
            raise ValidationError("Количество должно быть >= 1.")
        self.items.append(item)

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "customer_id": self.customer_id,
            "created_at": self.created_at.isoformat(timespec="seconds"),
            "total": self.total,
            "items": [i.to_dict() for i in self.items],
        })
        return d
