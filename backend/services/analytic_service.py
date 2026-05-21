from collections import defaultdict

from backend.models import Transaction
from backend.schemas import AnalyticsSummary, SeriesPoint, TransactionRead


def month_key(transaction: Transaction) -> str:
    return transaction.date.strftime("%b %Y")


def month_sort_key(label: str) -> tuple[int, int]:
    month, year = label.split()
    month_number = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }[month]
    return int(year), month_number


def grouped_sum(transactions: list[Transaction], field: str) -> list[SeriesPoint]:
    buckets: dict[str, float] = defaultdict(float)
    for transaction in transactions:
        buckets[getattr(transaction, field)] += transaction.amount
    return [
        SeriesPoint(label=label, value=round(value, 2))
        for label, value in sorted(buckets.items(), key=lambda item: item[1], reverse=True)
    ]


def monthly_volume(transactions: list[Transaction]) -> list[SeriesPoint]:
    buckets: dict[str, float] = defaultdict(float)
    for transaction in transactions:
        buckets[month_key(transaction)] += transaction.amount
    return [
        SeriesPoint(label=label, value=round(value, 2))
        for label, value in sorted(buckets.items(), key=lambda item: month_sort_key(item[0]))
    ]


def calculate_cagr(series: list[SeriesPoint]) -> float:
    if len(series) < 2 or series[0].value <= 0:
        return 0.0

    periods = len(series) - 1
    return round(((series[-1].value / series[0].value) ** (12 / periods) - 1) * 100, 2)


def build_summary(transactions: list[Transaction]) -> AnalyticsSummary:
    ordered = sorted(transactions, key=lambda transaction: transaction.date)
    monthly = monthly_volume(ordered)
    total = sum(transaction.amount for transaction in ordered)
    count = len(ordered)

    return AnalyticsSummary(
        total_volume=round(total, 2),
        transaction_count=count,
        average_transaction=round(total / count, 2) if count else 0,
        cagr=calculate_cagr(monthly),
        monthly_volume=monthly,
        category_mix=grouped_sum(ordered, "category"),
        method_mix=grouped_sum(ordered, "method"),
        region_mix=grouped_sum(ordered, "region"),
        recent_transactions=[
            TransactionRead.model_validate(transaction)
            for transaction in sorted(ordered, key=lambda item: item.date, reverse=True)[:8]
        ],
    )
