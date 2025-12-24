"""
shop_manager.analysis
====================

Data analysis and visualization:
- Top 5 customers by number of orders
- Dynamics of number of orders by dates
- Graph of relationships (customers connected by common products)

This module uses pandas, matplotlib, networkx.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from .db import Database


@dataclass
class AnalysisResultPaths:
    """Paths to generated images."""
    top_customers_png: Path
    orders_dynamics_png: Path
    customer_graph_png: Path


def _ensure_outdir(out_dir: str | Path) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    return out


def build_dataframes(db: Database) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Build DataFrames from DB.

    Returns
    -------
    customers_df, products_df, orders_df, items_df
    """
    customers = [c.to_dict() for c in db.list_customers()]
    products = [p.to_dict() for p in db.list_products()]
    orders = db.list_orders()

    items = []
    for o in orders:
        oid = int(o["id"])
        for it in db.get_order_items(oid):
            d = it.to_dict()
            d["order_id"] = oid
            items.append(d)

    customers_df = pd.DataFrame(customers)
    products_df = pd.DataFrame(products)
    orders_df = pd.DataFrame(orders)
    items_df = pd.DataFrame(items)

    if not orders_df.empty:
        orders_df["created_at"] = pd.to_datetime(orders_df["created_at"])
        orders_df["date"] = orders_df["created_at"].dt.date

    return customers_df, products_df, orders_df, items_df


def top_customers_by_orders(db: Database, out_dir: str | Path = "reports") -> Path:
    """
    Plot top 5 customers by number of orders.

    Returns
    -------
    Path
        Saved PNG path.
    """
    out = _ensure_outdir(out_dir)
    _, _, orders_df, _ = build_dataframes(db)
    if orders_df.empty:
        p = out / "top_customers.png"
        _empty_plot(p, "Нет данных для топ клиентов")
        return p

    g = orders_df.groupby("customer_name")["id"].count().sort_values(ascending=False).head(5)
    fig = plt.figure()
    g.plot(kind="bar")
    plt.title("Топ 5 клиентов по числу заказов")
    plt.xlabel("Клиент")
    plt.ylabel("Кол-во заказов")
    plt.tight_layout()
    p = out / "top_customers.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    return p


def orders_dynamics_by_date(db: Database, out_dir: str | Path = "reports") -> Path:
    """
    Plot order count dynamics by date.

    Returns
    -------
    Path
        Saved PNG path.
    """
    out = _ensure_outdir(out_dir)
    _, _, orders_df, _ = build_dataframes(db)
    if orders_df.empty:
        p = out / "orders_dynamics.png"
        _empty_plot(p, "Нет данных для динамики заказов")
        return p

    g = orders_df.groupby("date")["id"].count().sort_index()
    fig = plt.figure()
    g.plot(kind="line", marker="o")
    plt.title("Динамика количества заказов по датам")
    plt.xlabel("Дата")
    plt.ylabel("Кол-во заказов")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    p = out / "orders_dynamics.png"
    fig.savefig(p, dpi=150)
    plt.close(fig)
    return p


def customer_relationship_graph(db: Database, out_dir: str | Path = "reports") -> Path:
    """
    Build and plot a graph of customer relationships based on common products.

    Logic
    -----
    Two customers are connected if they bought at least one same product.
    Edge weight = number of shared products.

    Returns
    -------
    Path
        Saved PNG path.
    """
    out = _ensure_outdir(out_dir)
    customers_df, _, orders_df, items_df = build_dataframes(db)

    p = out / "customer_graph.png"
    if orders_df.empty or items_df.empty:
        _empty_plot(p, "Нет данных для графа связей клиентов")
        return p

    # Map order_id -> customer_name
    order_to_customer = orders_df.set_index("id")["customer_name"].to_dict()
    items_df["customer_name"] = items_df["order_id"].map(order_to_customer)

    # customer -> set of product ids
    cust_products = items_df.groupby("customer_name")["product_id"].apply(lambda s: set(map(int, s))).to_dict()

    G = nx.Graph()
    for cust in cust_products.keys():
        G.add_node(cust)

    cust_list = list(cust_products.keys())
    for i in range(len(cust_list)):
        for j in range(i + 1, len(cust_list)):
            a, b = cust_list[i], cust_list[j]
            shared = cust_products[a].intersection(cust_products[b])
            if shared:
                G.add_edge(a, b, weight=len(shared))

    fig = plt.figure(figsize=(8, 6))
    if G.number_of_edges() == 0:
        plt.title("Граф связей клиентов (общие товары не найдены)")
        nx.draw(G, with_labels=True)
    else:
        plt.title("Граф связей клиентов (общие товары)")
        pos = nx.spring_layout(G, seed=42)
        weights = [G[u][v]["weight"] for u, v in G.edges()]
        nx.draw(G, pos, with_labels=True, width=weights)
        edge_labels = {(u, v): G[u][v]["weight"] for u, v in G.edges()}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    plt.tight_layout()
    fig.savefig(p, dpi=150)
    plt.close(fig)
    return p


def generate_all_reports(db: Database, out_dir: str | Path = "reports") -> AnalysisResultPaths:
    """Generate all charts and return their paths."""
    out = _ensure_outdir(out_dir)
    return AnalysisResultPaths(
        top_customers_png=top_customers_by_orders(db, out),
        orders_dynamics_png=orders_dynamics_by_date(db, out),
        customer_graph_png=customer_relationship_graph(db, out),
    )


def _empty_plot(path: Path, msg: str) -> None:
    fig = plt.figure()
    plt.text(0.5, 0.5, msg, ha="center", va="center")
    plt.axis("off")
    fig.savefig(path, dpi=150)
    plt.close(fig)
