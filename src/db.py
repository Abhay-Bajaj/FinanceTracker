import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

DB_PATH = Path("data") / "finance.db"


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(c["name"] == column for c in cols)


def init_db():
    with get_conn() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        # Users table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

        # Transactions table (per-user)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT NOT NULL,              -- YYYY-MM-DD
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                merchant TEXT,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )

        # Budgets table (optional, per-user)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                month TEXT NOT NULL,             -- YYYY-MM
                category TEXT NOT NULL,
                budget_amount REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(user_id, month, category)
            );
            """
        )

        # ---- Migrations for older DBs ----
        if not _column_exists(conn, "transactions", "user_id"):
            conn.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER;")

        if not _column_exists(conn, "budgets", "user_id"):
            conn.execute("ALTER TABLE budgets ADD COLUMN user_id INTEGER;")

        if not _column_exists(conn, "budgets", "created_at"):
            conn.execute("ALTER TABLE budgets ADD COLUMN created_at TEXT;")

        conn.commit()


# -------------------- User helpers --------------------
def user_exists(username: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE LOWER(username) = LOWER(?)",
            (username.strip(),),
        ).fetchone()
    return row is not None


def create_user(username: str, name: str, email: str, password_hash: str) -> int:
    created_at = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO users (username, name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (username.strip(), name.strip(), email.strip(), password_hash, created_at),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(?)",
            (username.strip(),),
        ).fetchone()
    return row


def fetch_users():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return rows


# -------------------- Transactions --------------------
def add_transaction(
    user_id: int,
    date: str,
    amount: float,
    category: str,
    merchant: str,
    notes: str,
):
    created_at = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO transactions (user_id, date, amount, category, merchant, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                date,
                amount,
                category,
                merchant.strip() or None,
                notes.strip() or None,
                created_at,
            ),
        )
        conn.commit()


def fetch_transactions(user_id: int):
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM transactions
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
            """,
            (user_id,),
        ).fetchall()
    return rows


def clear_user_data(user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM transactions WHERE user_id = ?;", (user_id,))
        conn.execute("DELETE FROM budgets WHERE user_id = ?;", (user_id,))
        conn.commit()
