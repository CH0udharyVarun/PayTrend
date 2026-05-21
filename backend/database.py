from datetime import date
import hashlib
import secrets
import sqlite3
from pathlib import Path

from backend.models import Transaction, User
from backend.schemas import TransactionCreate


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "paytrend.sqlite3"
PASSWORD_ITERATIONS = 210_000


SAMPLE_TRANSACTIONS: list[TransactionCreate] = [
    TransactionCreate(date=date(2025, 1, 7), merchant="Metro Basket", category="Retail", method="UPI", region="West", amount=128400),
    TransactionCreate(date=date(2025, 1, 19), merchant="Cloud Cart", category="Ecommerce", method="Card", region="South", amount=164250),
    TransactionCreate(date=date(2025, 2, 4), merchant="Fresh Lane", category="Grocery", method="Wallet", region="North", amount=142800),
    TransactionCreate(date=date(2025, 2, 22), merchant="QuickPay Fuel", category="Utilities", method="UPI", region="East", amount=187600),
    TransactionCreate(date=date(2025, 3, 8), merchant="Urban Threads", category="Retail", method="Card", region="West", amount=214300),
    TransactionCreate(date=date(2025, 3, 24), merchant="Stream Hub", category="Subscriptions", method="UPI", region="South", amount=196700),
    TransactionCreate(date=date(2025, 4, 5), merchant="Cloud Cart", category="Ecommerce", method="UPI", region="North", amount=244900),
    TransactionCreate(date=date(2025, 4, 21), merchant="Health First", category="Healthcare", method="NetBanking", region="East", amount=223500),
    TransactionCreate(date=date(2025, 5, 10), merchant="Metro Basket", category="Retail", method="Wallet", region="West", amount=278300),
    TransactionCreate(date=date(2025, 5, 26), merchant="Travel Grid", category="Travel", method="Card", region="South", amount=302100),
    TransactionCreate(date=date(2025, 6, 11), merchant="Fresh Lane", category="Grocery", method="UPI", region="North", amount=326400),
    TransactionCreate(date=date(2025, 6, 28), merchant="Cloud Cart", category="Ecommerce", method="Card", region="East", amount=354200),
    TransactionCreate(date=date(2025, 7, 9), merchant="QuickPay Fuel", category="Utilities", method="UPI", region="West", amount=381700),
    TransactionCreate(date=date(2025, 7, 25), merchant="Urban Threads", category="Retail", method="Wallet", region="South", amount=402900),
    TransactionCreate(date=date(2025, 8, 13), merchant="Stream Hub", category="Subscriptions", method="UPI", region="North", amount=433100),
    TransactionCreate(date=date(2025, 8, 29), merchant="Travel Grid", category="Travel", method="Card", region="East", amount=471600),
    TransactionCreate(date=date(2025, 9, 6), merchant="Health First", category="Healthcare", method="NetBanking", region="West", amount=492300),
    TransactionCreate(date=date(2025, 9, 19), merchant="Cloud Cart", category="Ecommerce", method="UPI", region="South", amount=526800),
    TransactionCreate(date=date(2025, 10, 8), merchant="Metro Basket", category="Retail", method="Card", region="North", amount=561500),
    TransactionCreate(date=date(2025, 10, 27), merchant="Fresh Lane", category="Grocery", method="Wallet", region="East", amount=589400),
    TransactionCreate(date=date(2025, 11, 12), merchant="Travel Grid", category="Travel", method="UPI", region="West", amount=621900),
    TransactionCreate(date=date(2025, 11, 24), merchant="QuickPay Fuel", category="Utilities", method="Card", region="South", amount=648700),
    TransactionCreate(date=date(2025, 12, 7), merchant="Cloud Cart", category="Ecommerce", method="UPI", region="North", amount=694300),
    TransactionCreate(date=date(2025, 12, 22), merchant="Urban Threads", category="Retail", method="Wallet", region="East", amount=731600),
]


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT NOT NULL,
                merchant TEXT NOT NULL,
                category TEXT NOT NULL,
                method TEXT NOT NULL,
                region TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                status TEXT NOT NULL DEFAULT 'settled',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(transactions)").fetchall()}
        if "user_id" not in columns:
            connection.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER")

        demo_user = get_user_by_email("demo@paytrend.local", connection)
        if demo_user is None:
            demo_user = create_user("Demo User", "demo@paytrend.local", "password123", connection)

        connection.execute(
            "UPDATE transactions SET user_id = ? WHERE user_id IS NULL",
            (demo_user.id,),
        )
        count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        if count == 0:
            create_transactions(demo_user.id, SAMPLE_TRANSACTIONS, connection)
        connection.commit()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str, salt: str | None = None) -> str:
    active_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        active_salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{active_salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt, expected = stored_hash.split("$", 1)
    actual = hash_password(password, salt).split("$", 1)[1]
    return secrets.compare_digest(actual, expected)


def row_to_user(row: sqlite3.Row) -> User:
    return User(id=row["id"], name=row["name"], email=row["email"])


def create_user(
    name: str,
    email: str,
    password: str,
    connection: sqlite3.Connection | None = None,
) -> User:
    owns_connection = connection is None
    active_connection = connection or connect()
    cursor = active_connection.execute(
        """
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
        """,
        (name.strip(), normalize_email(email), hash_password(password)),
    )
    if owns_connection:
        active_connection.commit()
    row = active_connection.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    if owns_connection:
        active_connection.close()
    return row_to_user(row)


def get_user_by_email(email: str, connection: sqlite3.Connection | None = None) -> User | None:
    owns_connection = connection is None
    active_connection = connection or connect()
    row = active_connection.execute(
        "SELECT * FROM users WHERE email = ?",
        (normalize_email(email),),
    ).fetchone()
    if owns_connection:
        active_connection.close()
    return row_to_user(row) if row else None


def authenticate_user(email: str, password: str) -> User | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (normalize_email(email),),
        ).fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        return None
    return row_to_user(row)


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    with connect() as connection:
        connection.execute(
            "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
            (token, user_id),
        )
        connection.commit()
    return token


def get_user_by_token(token: str) -> User | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT users.*
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
    return row_to_user(row) if row else None


def delete_session(token: str) -> None:
    with connect() as connection:
        connection.execute("DELETE FROM sessions WHERE token = ?", (token,))
        connection.commit()


def row_to_transaction(row: sqlite3.Row) -> Transaction:
    return Transaction(
        id=row["id"],
        user_id=row["user_id"],
        date=date.fromisoformat(row["date"]),
        merchant=row["merchant"],
        category=row["category"],
        method=row["method"],
        region=row["region"],
        amount=row["amount"],
        status=row["status"],
    )


def create_transaction(
    user_id: int,
    payload: TransactionCreate,
    connection: sqlite3.Connection | None = None,
) -> Transaction:
    owns_connection = connection is None
    active_connection = connection or connect()
    cursor = active_connection.execute(
        """
        INSERT INTO transactions (user_id, date, merchant, category, method, region, amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            payload.date.isoformat(),
            payload.merchant,
            payload.category,
            payload.method,
            payload.region,
            payload.amount,
            payload.status,
        ),
    )
    if owns_connection:
        active_connection.commit()
    row = active_connection.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    if owns_connection:
        active_connection.close()
    return row_to_transaction(row)


def create_transactions(
    user_id: int,
    payloads: list[TransactionCreate],
    connection: sqlite3.Connection | None = None,
) -> list[Transaction]:
    owns_connection = connection is None
    active_connection = connection or connect()
    created = [create_transaction(user_id, payload, active_connection) for payload in payloads]
    if owns_connection:
        active_connection.commit()
        active_connection.close()
    return created


def get_transactions(user_id: int | None = None) -> list[Transaction]:
    with connect() as connection:
        if user_id is None:
            rows = connection.execute("SELECT * FROM transactions ORDER BY date ASC, id ASC").fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM transactions WHERE user_id = ? ORDER BY date ASC, id ASC",
                (user_id,),
            ).fetchall()
    return [row_to_transaction(row) for row in rows]
