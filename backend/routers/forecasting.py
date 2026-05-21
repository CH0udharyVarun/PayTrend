from fastapi import APIRouter, Depends, Query

from backend.auth import current_user
from backend.database import get_transactions
from backend.models import User
from backend.schemas import ForecastResponse
from backend.services.forecasting_service import forecast_growth


router = APIRouter(prefix="/forecasting", tags=["forecasting"])


@router.get("/growth", response_model=ForecastResponse)
async def growth_forecast(
    horizon_months: int = Query(default=6, ge=1, le=18),
    user: User = Depends(current_user),
) -> ForecastResponse:
    return forecast_growth(get_transactions(user.id), horizon_months)
