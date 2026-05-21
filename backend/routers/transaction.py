from fastapi import APIRouter, Depends, status

from backend.auth import current_user
from backend.database import create_transaction, create_transactions, get_transactions
from backend.models import User
from backend.schemas import TransactionBatchCreate, TransactionCreate, TransactionRead


router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionRead])
async def list_transactions(user: User = Depends(current_user)) -> list[TransactionRead]:
    return [
        TransactionRead.model_validate(transaction)
        for transaction in sorted(get_transactions(user.id), key=lambda item: item.date, reverse=True)
    ]


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def add_transaction(payload: TransactionCreate, user: User = Depends(current_user)) -> TransactionRead:
    return TransactionRead.model_validate(create_transaction(user.id, payload))


@router.post("/batch", response_model=list[TransactionRead], status_code=status.HTTP_201_CREATED)
async def import_transactions(
    payload: TransactionBatchCreate,
    user: User = Depends(current_user),
) -> list[TransactionRead]:
    return [
        TransactionRead.model_validate(transaction)
        for transaction in create_transactions(user.id, payload.transactions)
    ]
