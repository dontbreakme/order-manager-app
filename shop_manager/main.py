"""
shop_manager.main
=================

Entry point.
"""

from __future__ import annotations

from .gui import run_app


def main() -> None:
    """Run GUI application."""
    run_app(db_path="data.sqlite")


if __name__ == "__main__":
    main()
