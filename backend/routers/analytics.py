from fastapi import APIRouter, Depends

from backend.auth import current_user
from backend.database import get_transactions
from backend.models import User
from backend.schemas import AnalyticsSummary
from backend.services.analytic_service import build_summary


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(user: User = Depends(current_user)) -> AnalyticsSummary:
    return build_summary(get_transactions(user.id))
