from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.database import get_transactions, init_database
from backend.routers import analytics, auth, forecasting, transaction
from backend.schemas import SystemHealth


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    yield

app = FastAPI(
    title="PayTrend API",
    description="Digital payment growth analytics and forecasting API.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8501", "http://localhost:8501", "null"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transaction.router)
app.include_router(analytics.router)
app.include_router(forecasting.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/app.js")
async def frontend_script():
    return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")


@app.get("/styles.css")
async def frontend_styles():
    return FileResponse(FRONTEND_DIR / "styles.css", media_type="text/css")


@app.get("/api/status")
async def api_status() -> dict[str, object]:
    return {
        "name": "PayTrend API",
        "status": "online",
        "version": app.version,
        "endpoints": ["/auth/signup", "/auth/signin", "/transactions", "/analytics/summary", "/forecasting/growth", "/health"],
    }


@app.get("/health", response_model=SystemHealth, tags=["system"])
async def health() -> SystemHealth:
    transactions = get_transactions()
    latest = max((transaction.date for transaction in transactions), default=None)
    return SystemHealth(
        status="online",
        database="connected",
        transaction_count=len(transactions),
        latest_transaction_date=latest,
    )
