"""
shop_manager.gui
================

Tkinter GUI for managing customers, products, orders, and analytics.

Features
--------
- Add customers/products/orders
- List and filter data
- Export/Import JSON and CSV
- Generate analysis charts

Run via: python -m shop_manager.main
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from .db import Database
from .models import Customer, Product, Order, OrderItem, ValidationError
from .analysis import generate_all_reports
from .sorting_utils import merge_sort


class App(ttk.Frame):
    """Main application frame."""

    def __init__(self, master: tk.Tk, db: Database) -> None:
        super().__init__(master)
        self.master = master
        self.db = db

        self._build_ui()
        self.refresh_all()

    # ---------------- UI ----------------

    def _build_ui(self) -> None:
        self.master.title("Учёт заказов интернет-магазина (Python итоговая)")
        self.master.geometry("1050x650")

        nb = ttk.Notebook(self)
        self.tab_customers = ttk.Frame(nb)
        self.tab_products = ttk.Frame(nb)
        self.tab_orders = ttk.Frame(nb)
        self.tab_analytics = ttk.Frame(nb)
        self.tab_io = ttk.Frame(nb)

        nb.add(self.tab_customers, text="Клиенты")
        nb.add(self.tab_products, text="Товары")
        nb.add(self.tab_orders, text="Заказы")
        nb.add(self.tab_analytics, text="Аналитика")
        nb.add(self.tab_io, text="Импорт/Экспорт")
        nb.pack(fill="both", expand=True)

        self._build_customers_tab()
        self._build_products_tab()
        self._build_orders_tab()
        self._build_analytics_tab()
        self._build_io_tab()

        self.pack(fill="both", expand=True)

    def _build_customers_tab(self) -> None:
        frm = self.tab_customers

        form = ttk.LabelFrame(frm, text="Добавить клиента")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Имя*").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(form, text="Email").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Label(form, text="Телефон").grid(row=0, column=4, sticky="w", padx=5, pady=5)

        self.ent_c_name = ttk.Entry(form, width=30)
        self.ent_c_email = ttk.Entry(form, width=30)
        self.ent_c_phone = ttk.Entry(form, width=20)
        self.ent_c_name.grid(row=0, column=1, padx=5, pady=5)
        self.ent_c_email.grid(row=0, column=3, padx=5, pady=5)
        self.ent_c_phone.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(form, text="Добавить", command=self.add_customer).grid(row=0, column=6, padx=10, pady=5)

        # list + filter
        box = ttk.LabelFrame(frm, text="Список клиентов")
        box.pack(fill="both", expand=True, padx=10, pady=10)

        frow = ttk.Frame(box)
        frow.pack(fill="x", padx=5, pady=5)
        ttk.Label(frow, text="Поиск по имени:").pack(side="left")
        self.ent_c_search = ttk.Entry(frow, width=40)
        self.ent_c_search.pack(side="left", padx=6)
        ttk.Button(frow, text="Найти", command=self.refresh_customers).pack(side="left")
        ttk.Button(frow, text="Сброс", command=self._clear_customer_search).pack(side="left", padx=6)

        self.tv_customers = ttk.Treeview(box, columns=("id","name","email","phone"), show="headings", height=18)
        for c, t, w in [("id","ID",60),("name","Имя",260),("email","Email",260),("phone","Телефон",160)]:
            self.tv_customers.heading(c, text=t)
            self.tv_customers.column(c, width=w, anchor="w")
        self.tv_customers.pack(fill="both", expand=True, padx=5, pady=5)

    def _build_products_tab(self) -> None:
        frm = self.tab_products

        form = ttk.LabelFrame(frm, text="Добавить товар")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Название*").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(form, text="Цена*").grid(row=0, column=2, sticky="w", padx=5, pady=5)

        self.ent_p_title = ttk.Entry(form, width=40)
        self.ent_p_price = ttk.Entry(form, width=12)
        self.ent_p_title.grid(row=0, column=1, padx=5, pady=5)
        self.ent_p_price.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(form, text="Добавить", command=self.add_product).grid(row=0, column=4, padx=10, pady=5)

        box = ttk.LabelFrame(frm, text="Список товаров")
        box.pack(fill="both", expand=True, padx=10, pady=10)

        self.tv_products = ttk.Treeview(box, columns=("id","title","price"), show="headings", height=20)
        for c, t, w in [("id","ID",60),("title","Название",420),("price","Цена",100)]:
            self.tv_products.heading(c, text=t)
            self.tv_products.column(c, width=w, anchor="w")
        self.tv_products.pack(fill="both", expand=True, padx=5, pady=5)

    def _build_orders_tab(self) -> None:
        frm = self.tab_orders

        top = ttk.Frame(frm)
        top.pack(fill="x", padx=10, pady=10)

        # Create order section
        create = ttk.LabelFrame(top, text="Создать заказ")
        create.pack(side="left", fill="both", expand=True, padx=(0,8))

        ttk.Label(create, text="Клиент:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.cmb_order_customer = ttk.Combobox(create, state="readonly", width=35)
        self.cmb_order_customer.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(create, text="Товар:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.cmb_order_product = ttk.Combobox(create, state="readonly", width=35)
        self.cmb_order_product.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(create, text="Кол-во:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.ent_order_qty = ttk.Entry(create, width=8)
        self.ent_order_qty.insert(0, "1")
        self.ent_order_qty.grid(row=1, column=3, padx=5, pady=5)

        ttk.Button(create, text="Добавить позицию", command=self.add_order_item_ui).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(create, text="Сохранить заказ", command=self.save_order).grid(row=2, column=2, padx=5, pady=5, sticky="w")

        self.tv_order_items = ttk.Treeview(create, columns=("product","price","qty","total"), show="headings", height=8)
        for c, t, w in [("product","Товар",240),("price","Цена",80),("qty","Кол-во",70),("total","Сумма",80)]:
            self.tv_order_items.heading(c, text=t)
            self.tv_order_items.column(c, width=w, anchor="w")
        self.tv_order_items.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

        create.grid_rowconfigure(3, weight=1)

        # Orders list section
        box = ttk.LabelFrame(top, text="Список заказов")
        box.pack(side="left", fill="both", expand=True)

        frow = ttk.Frame(box)
        frow.pack(fill="x", padx=5, pady=5)

        ttk.Label(frow, text="Сортировка:").pack(side="left")
        self.cmb_sort = ttk.Combobox(frow, state="readonly", values=["По дате (новые)", "По дате (старые)", "По сумме (убыв.)", "По сумме (возр.)"], width=18)
        self.cmb_sort.current(0)
        self.cmb_sort.pack(side="left", padx=6)

        ttk.Button(frow, text="Применить", command=self.refresh_orders).pack(side="left")
        ttk.Button(frow, text="Показать позиции", command=self.show_selected_order_items).pack(side="left", padx=6)

        self.tv_orders = ttk.Treeview(box, columns=("id","customer","created_at","total"), show="headings", height=16)
        for c, t, w in [("id","ID",60),("customer","Клиент",220),("created_at","Дата",160),("total","Сумма",100)]:
            self.tv_orders.heading(c, text=t)
            self.tv_orders.column(c, width=w, anchor="w")
        self.tv_orders.pack(fill="both", expand=True, padx=5, pady=5)

        # bottom details
        self.lbl_order_details = ttk.Label(frm, text="Выберите заказ и нажмите 'Показать позиции'.")
        self.lbl_order_details.pack(fill="x", padx=10, pady=(0,10))

        self._pending_items: List[OrderItem] = []

    def _build_analytics_tab(self) -> None:
        frm = self.tab_analytics
        ctl = ttk.Frame(frm)
        ctl.pack(fill="x", padx=10, pady=10)

        ttk.Button(ctl, text="Сгенерировать отчёты (PNG)", command=self.generate_reports).pack(side="left")
        ttk.Button(ctl, text="Открыть папку reports", command=self.open_reports_folder).pack(side="left", padx=10)

        self.txt_analytics = tk.Text(frm, height=25)
        self.txt_analytics.pack(fill="both", expand=True, padx=10, pady=10)
        self.txt_analytics.insert("1.0", "Нажмите 'Сгенерировать отчёты', чтобы получить графики.\n")

    def _build_io_tab(self) -> None:
        frm = self.tab_io
        box = ttk.LabelFrame(frm, text="Импорт / Экспорт")
        box.pack(fill="x", padx=10, pady=10)

        ttk.Button(box, text="Экспорт JSON", command=self.export_json).grid(row=0, column=0, padx=6, pady=6, sticky="w")
        ttk.Button(box, text="Импорт JSON", command=self.import_json).grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ttk.Button(box, text="Экспорт CSV (папка)", command=self.export_csv).grid(row=1, column=0, padx=6, pady=6, sticky="w")
        ttk.Button(box, text="Открыть CSV папку", command=self.open_csv_folder).grid(row=1, column=1, padx=6, pady=6, sticky="w")

        note = ttk.Label(frm, text="Подсказка: JSON удобен для полного переноса базы, CSV — для таблиц.")
        note.pack(fill="x", padx=10, pady=(0,10))

    # ---------------- actions ----------------

    def refresh_all(self) -> None:
        self.refresh_customers()
        self.refresh_products()
        self.refresh_orders()
        self._refresh_order_comboboxes()

    def _clear_customer_search(self) -> None:
        self.ent_c_search.delete(0, tk.END)
        self.refresh_customers()

    def add_customer(self) -> None:
        try:
            cust = Customer(_name=self.ent_c_name.get(), _email=self.ent_c_email.get(), _phone=self.ent_c_phone.get())
            self.db.add_customer(cust)
            self.ent_c_name.delete(0, tk.END)
            self.ent_c_email.delete(0, tk.END)
            self.ent_c_phone.delete(0, tk.END)
            self.refresh_all()
        except ValidationError as e:
            messagebox.showerror("Ошибка валидации", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить клиента: {e}")

    def add_product(self) -> None:
        try:
            prod = Product(_title=self.ent_p_title.get(), _price=self.ent_p_price.get())
            self.db.add_product(prod)
            self.ent_p_title.delete(0, tk.END)
            self.ent_p_price.delete(0, tk.END)
            self.refresh_all()
        except ValidationError as e:
            messagebox.showerror("Ошибка валидации", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить товар: {e}")

    def refresh_customers(self) -> None:
        self.tv_customers.delete(*self.tv_customers.get_children())
        q = (self.ent_c_search.get() or "").strip().lower()
        for c in self.db.list_customers():
            if q and q not in c.name.lower():
                continue
            self.tv_customers.insert("", "end", values=(c.id, c.name, c.email, c.phone))

    def refresh_products(self) -> None:
        self.tv_products.delete(*self.tv_products.get_children())
        for p in self.db.list_products():
            self.tv_products.insert("", "end", values=(p.id, p.title, f"{p.price:.2f}"))

    def _refresh_order_comboboxes(self) -> None:
        customers = self.db.list_customers()
        products = self.db.list_products()

        self._customer_by_label: Dict[str, int] = {f"{c.id} — {c.name}": int(c.id) for c in customers}
        self._product_by_label: Dict[str, Product] = {f"{p.id} — {p.title}": p for p in products}

        self.cmb_order_customer["values"] = list(self._customer_by_label.keys())
        self.cmb_order_product["values"] = list(self._product_by_label.keys())

        if customers and not self.cmb_order_customer.get():
            self.cmb_order_customer.current(0)
        if products and not self.cmb_order_product.get():
            self.cmb_order_product.current(0)

    def add_order_item_ui(self) -> None:
        try:
            if not self.cmb_order_product.get():
                raise ValidationError("Сначала выберите товар.")
            prod = self._product_by_label[self.cmb_order_product.get()]
            qty = int(self.ent_order_qty.get())
            if qty < 1:
                raise ValidationError("Количество должно быть >= 1.")
            item = OrderItem(product_id=int(prod.id), product_title=prod.title, unit_price=float(prod.price), quantity=qty)
            self._pending_items.append(item)
            self._render_pending_items()
        except (ValueError, ValidationError) as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить позицию: {e}")

    def _render_pending_items(self) -> None:
        self.tv_order_items.delete(*self.tv_order_items.get_children())
        for it in self._pending_items:
            self.tv_order_items.insert("", "end", values=(it.product_title, f"{it.unit_price:.2f}", it.quantity, f"{it.line_total:.2f}"))

    def save_order(self) -> None:
        try:
            if not self.cmb_order_customer.get():
                raise ValidationError("Выберите клиента.")
            if not self._pending_items:
                raise ValidationError("Добавьте хотя бы 1 позицию в заказ.")
            cust_id = self._customer_by_label[self.cmb_order_customer.get()]
            order = Order(customer_id=cust_id, created_at=datetime.now())
            for it in self._pending_items:
                order.add_item(it)
            self.db.add_order(order)
            self._pending_items = []
            self._render_pending_items()
            self.refresh_orders()
            messagebox.showinfo("Готово", "Заказ сохранён.")
        except ValidationError as e:
            messagebox.showerror("Ошибка валидации", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить заказ: {e}")

    def refresh_orders(self) -> None:
        self.tv_orders.delete(*self.tv_orders.get_children())
        orders = self.db.list_orders()

        # custom sort requirement (merge_sort)
        mode = self.cmb_sort.get() if hasattr(self, "cmb_sort") else "По дате (новые)"
        if mode == "По дате (новые)":
            orders = merge_sort(orders, key=lambda x: x["created_at"], reverse=True)
        elif mode == "По дате (старые)":
            orders = merge_sort(orders, key=lambda x: x["created_at"], reverse=False)
        elif mode == "По сумме (убыв.)":
            orders = merge_sort(orders, key=lambda x: float(x["total"]), reverse=True)
        elif mode == "По сумме (возр.)":
            orders = merge_sort(orders, key=lambda x: float(x["total"]), reverse=False)

        for o in orders:
            self.tv_orders.insert("", "end", values=(o["id"], o["customer_name"], o["created_at"], f"{float(o['total']):.2f}"))

    def show_selected_order_items(self) -> None:
        sel = self.tv_orders.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Сначала выберите заказ в таблице.")
            return
        oid = int(self.tv_orders.item(sel[0])["values"][0])
        items = self.db.get_order_items(oid)
        lines = [f"Заказ #{oid}:"]
        for it in items:
            lines.append(f"  - {it.product_title} × {it.quantity} = {it.line_total:.2f}")
        lines.append(f"Итого: {sum(i.line_total for i in items):.2f}")
        self.lbl_order_details.config(text="\n".join(lines))

    def generate_reports(self) -> None:
        try:
            paths = generate_all_reports(self.db, out_dir=Path("reports"))
            self.txt_analytics.delete("1.0", tk.END)
            self.txt_analytics.insert("1.0",
                "Сгенерировано:\n"
                f"- {paths.top_customers_png}\n"
                f"- {paths.orders_dynamics_png}\n"
                f"- {paths.customer_graph_png}\n\n"
                "Откройте папку reports, чтобы увидеть PNG.\n"
            )
            messagebox.showinfo("Готово", "Отчёты сформированы в папке reports.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось построить отчёты: {e}")

    def open_reports_folder(self) -> None:
        path = Path("reports").resolve()
        messagebox.showinfo("Путь", f"Папка reports: {path}\n(Откройте вручную в проводнике.)")

    def export_json(self) -> None:
        try:
            path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
            if not path:
                return
            self.db.export_json(path)
            messagebox.showinfo("Готово", f"Экспортировано в {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Экспорт JSON не удался: {e}")

    def import_json(self) -> None:
        try:
            path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
            if not path:
                return
            if messagebox.askyesno("Импорт", "Очистить текущую базу перед импортом?"):
                clear = True
            else:
                clear = False
            self.db.import_json(path, clear_first=clear)
            self.refresh_all()
            messagebox.showinfo("Готово", "Импорт выполнен.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Импорт JSON не удался: {e}")

    def export_csv(self) -> None:
        try:
            folder = filedialog.askdirectory()
            if not folder:
                return
            self.db.export_csv(folder)
            messagebox.showinfo("Готово", f"CSV сохранены в {folder}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Экспорт CSV не удался: {e}")

    def open_csv_folder(self) -> None:
        messagebox.showinfo("Подсказка", "CSV папку выбираешь при экспорте — открой её в проводнике.")


def run_app(db_path: str = "data.sqlite") -> None:
    """Application entrypoint."""
    db = Database(db_path)
    db.connect()

    root = tk.Tk()
    try:
        App(root, db)
        root.mainloop()
    finally:
        db.close()
