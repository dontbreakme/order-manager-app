# Итоговая аттестация по Python — Учёт заказов (GUI + SQLite + Аналитика)

Настольное приложение для менеджеров интернет‑магазина:
- клиенты (контакты),
- товары,
- заказы (позиции),
- импорт/экспорт JSON и CSV,
- анализ и визуализация (pandas + matplotlib + networkx),
- unit‑tests (unittest),
- демонстрация ООП: инкапсуляция / наследование / полиморфизм.

## Быстрый старт

### 1) Установка зависимостей
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Запуск приложения (tkinter)
```bash
python -m shop_manager.main
```

После запуска появится `data.sqlite` (база SQLite) в папке проекта.

### 3) Тесты
```bash
python -m unittest -v
```

## Структура проекта

- `shop_manager/models.py` — модели данных (Customer, Product, Order) + проверки regex (email/phone)
- `shop_manager/db.py` — работа с SQLite + импорт/экспорт CSV/JSON
- `shop_manager/gui.py` — GUI на tkinter (вкладки: Клиенты / Товары / Заказы / Аналитика / Импорт-Экспорт)
- `shop_manager/analysis.py` — анализ и графики (Top 5 клиентов, динамика заказов, граф связей клиентов)
- `shop_manager/sorting_utils.py` — собственная сортировка (merge sort)
- `shop_manager/main.py` — точка входа
- `tests/` — unit‑tests

## Скриншоты

Сделай скрины вкладок приложения (Клиенты/Товары/Заказы/Аналитика/Импорт-Экспорт) и добавь в репозиторий (например, `docs/screens/`), потом вставь их в README.

## Как выполнить требования из ТЗ

- ✅ ООП: `Person -> Customer` (наследование), свойства (инкапсуляция), `to_dict()` (полиморфизм)
- ✅ Файлы и форматы: экспорт/импорт JSON и CSV
- ✅ Хранение: SQLite `data.sqlite`
- ✅ GUI: формы, списки, кнопки, фильтр по имени (клиенты), сортировка заказов
- ✅ Регулярки: email/phone (`models.py`)
- ✅ Сортировка: merge sort (`sorting_utils.py`)
- ✅ try/except: в GUI обработка ошибок + сообщения
- ✅ Тесты: `tests/test_models.py`, `tests/test_analysis.py`

## Git (что залить в репозиторий)

- код проекта,
- `README.md`,
- `.gitignore` (не коммить `.venv`, `__pycache__`, `data.sqlite`, `reports/`),
- минимум 1 коммит с историей.

Пример `.gitignore` ниже.
