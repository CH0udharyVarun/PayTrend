from datetime import date
from typing import NamedTuple


class Transaction(NamedTuple):
    id: int
    user_id: int
    date: date
    merchant: str
    category: str
    method: str
    region: str
    amount: float
    status: str = "settled"


class User(NamedTuple):
    id: int
    name: str
    email: str
