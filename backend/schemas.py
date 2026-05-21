from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    date: date
    merchant: str
    category: str
    method: str
    region: str
    amount: float = Field(ge=0)
    status: str


class TransactionCreate(BaseModel):
    date: date
    merchant: str = Field(min_length=2, max_length=80)
    category: str = Field(min_length=2, max_length=40)
    method: str = Field(min_length=2, max_length=30)
    region: str = Field(min_length=2, max_length=30)
    amount: float = Field(gt=0)
    status: str = Field(default="settled", min_length=2, max_length=30)


class TransactionBatchCreate(BaseModel):
    transactions: list[TransactionCreate] = Field(min_length=1, max_length=200)


class UserRead(BaseModel):
    id: int
    name: str
    email: str


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=1, max_length=128)


class AuthResponse(BaseModel):
    token: str
    user: UserRead


class MetricCard(BaseModel):
    label: str
    value: float
    change: float
    suffix: str = ""


class SeriesPoint(BaseModel):
    label: str
    value: float


class AnalyticsSummary(BaseModel):
    total_volume: float
    transaction_count: int
    average_transaction: float
    cagr: float
    monthly_volume: list[SeriesPoint]
    category_mix: list[SeriesPoint]
    method_mix: list[SeriesPoint]
    region_mix: list[SeriesPoint]
    recent_transactions: list[TransactionRead]


class SystemHealth(BaseModel):
    status: str
    database: str
    transaction_count: int
    latest_transaction_date: date | None
    service: str = "PayTrend API"


class ForecastPoint(BaseModel):
    label: str
    value: float
    projected: bool


class ForecastResponse(BaseModel):
    horizon_months: int
    slope: float
    intercept: float
    projected_growth: float
    series: list[ForecastPoint]
