from backend.models import Transaction
from backend.schemas import ForecastPoint, ForecastResponse
from backend.services.analytic_service import monthly_volume


def linear_regression(values: list[float]) -> tuple[float, float]:
    count = len(values)
    if count == 0:
        return 0.0, 0.0

    x_values = list(range(count))
    x_mean = sum(x_values) / count
    y_mean = sum(values) / count
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    slope = numerator / denominator if denominator else 0.0
    intercept = y_mean - slope * x_mean
    return slope, intercept


def add_month(label: str, offset: int) -> str:
    month_name, year_text = label.split()
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_index = months.index(month_name) + offset
    year = int(year_text) + month_index // 12
    month = months[month_index % 12]
    return f"{month} {year}"


def forecast_growth(transactions: list[Transaction], horizon_months: int = 6) -> ForecastResponse:
    historical = monthly_volume(transactions)
    values = [point.value for point in historical]
    slope, intercept = linear_regression(values)

    series = [
        ForecastPoint(label=point.label, value=point.value, projected=False)
        for point in historical
    ]

    if historical:
        last_label = historical[-1].label
        for step in range(1, horizon_months + 1):
            projected_value = max(0, intercept + slope * (len(values) + step - 1))
            series.append(
                ForecastPoint(
                    label=add_month(last_label, step),
                    value=round(projected_value, 2),
                    projected=True,
                )
            )

    current = values[-1] if values else 0
    future = series[-1].value if series else 0
    projected_growth = ((future - current) / current * 100) if current else 0

    return ForecastResponse(
        horizon_months=horizon_months,
        slope=round(slope, 2),
        intercept=round(intercept, 2),
        projected_growth=round(projected_growth, 2),
        series=series,
    )
