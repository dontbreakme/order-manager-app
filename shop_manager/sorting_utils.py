"""
shop_manager.sorting_utils
=========================

Custom sorting implementation (requirement: own sorting).
We use merge sort to sort orders by date or total.
"""

from __future__ import annotations
from typing import List, Callable, TypeVar

T = TypeVar("T")


def merge_sort(data: List[T], key: Callable[[T], object], reverse: bool = False) -> List[T]:
    """
    Sort a list using merge sort.

    Parameters
    ----------
    data:
        Input list.
    key:
        Key function.
    reverse:
        If True, descending order.

    Returns
    -------
    list
        Sorted list.
    """
    if len(data) <= 1:
        return list(data)

    mid = len(data) // 2
    left = merge_sort(data[:mid], key=key, reverse=reverse)
    right = merge_sort(data[mid:], key=key, reverse=reverse)

    return _merge(left, right, key=key, reverse=reverse)


def _merge(left: List[T], right: List[T], key: Callable[[T], object], reverse: bool) -> List[T]:
    out: List[T] = []
    i = j = 0

    def leq(a, b) -> bool:
        return a <= b if not reverse else a >= b

    while i < len(left) and j < len(right):
        if leq(key(left[i]), key(right[j])):
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1

    out.extend(left[i:])
    out.extend(right[j:])
    return out
