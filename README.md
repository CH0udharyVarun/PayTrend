# PayTrend

PayTrend is a digital payment growth analytics and forecasting platform for monitoring transaction volume, payment-channel performance, regional distribution, and short-term growth outlook. It combines a FastAPI backend, SQLite persistence, validated REST APIs, live transaction intake, CAGR analytics, and regression-based forecasting with an executive dashboard.

## Highlights

```text
- Live SQLite-backed transaction data
- Add validated customer transaction records
- Auto-refreshing dashboard connected to backend APIs
- CAGR, volume trends, payment method mix, category mix, and regional analytics
- Linear-regression forecast for future payment volume
- Service health endpoint for deployment monitoring
- Dependency-light implementation that runs on a standard Python virtual environment
```

## Structure

```text
paytrend/
  backend/
    main.py
    database.py
    models.py
    schemas.py
    routers/
    services/
    alembic/
  frontend/
    app.py
    app.js
    index.html
    styles.css
  data/
    paytrend.sqlite3
  requests/
    test_main.http
```

## Backend

Run the FastAPI app from the project root:

```powershell
.\.venv\Scripts\uvicorn.exe backend.main:app --reload
```

This also works from the project root:

```powershell
.\.venv\Scripts\uvicorn.exe main:app --reload
```

The live dashboard and API will be available at `http://127.0.0.1:8000`.

Useful API routes:

```text
GET /transactions
POST /transactions
POST /transactions/batch
GET /analytics/summary
GET /forecasting/growth?horizon_months=6
GET /health
```

## Frontend

Run the static dashboard server from the project root:

```powershell
.\.venv\Scripts\python.exe frontend\app.py
```

The standalone frontend server will be available at `http://127.0.0.1:8501/index.html`.

The frontend reads live data from the backend through its own `/api` proxy when served on port `8501`. When served by FastAPI on port `8000`, it calls the API directly.

## Local Workflow

```text
1. Open http://127.0.0.1:8000
2. Review KPI cards, trend chart, forecast chart, segment analytics, and transaction ledger
3. Add a transaction from the Live Intake form
4. Confirm dashboard metrics and charts refresh automatically
```

## Data

The app creates `data/paytrend.sqlite3` automatically on first startup and seeds realistic payment transactions. New transactions are persisted locally, so dashboard changes remain after refresh.
