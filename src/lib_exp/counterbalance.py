"""Deterministic permutation crossed with an independent factor; no allocation API."""
from itertools import permutations
from math import factorial

def _validate(conditions, factors):
    conditions, factors = tuple(conditions), tuple(factors)
    for values in (conditions, factors):
        if not values or any(not isinstance(x, str) or not x.strip() for x in values) or len(set(values)) != len(values):
            raise ValueError("nonempty unique string identifiers required")
    if len(conditions) > 8 or len(factors) > 128:
        raise ValueError("design exceeds supported size")
    return conditions, factors

def sequence_count(conditions, factors):
    c, f = _validate(conditions, factors)
    return factorial(len(c)) * len(f)

def sequence(conditions, factors, index):
    c, f = _validate(conditions, factors)
    n = factorial(len(c))
    if type(index) is not int or not 0 <= index < n * len(f):
        raise ValueError("invalid sequence index")
    remaining = list(c)
    order = []
    rank = index % n
    while remaining:
        position, rank = divmod(rank, factorial(len(remaining)-1))
        order.append(remaining.pop(position))
    return tuple(order), f[index // n]
