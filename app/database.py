import sqlite3
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "app.db"


def get_conn() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def transaction():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with transaction() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vocab_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                target_word TEXT NOT NULL,
                translation TEXT NOT NULL,
                exposure_count INTEGER NOT NULL DEFAULT 0,
                unlocked INTEGER NOT NULL DEFAULT 0,
                UNIQUE(session_id, target_word),
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS word_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                target_word TEXT NOT NULL,
                exposure_count INTEGER NOT NULL DEFAULT 0,
                unlocked INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                UNIQUE(session_id, target_word),
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                target_word TEXT NOT NULL,
                selected_translation TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
            """
        )

        legacy_vocab_words_exists = conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table' AND name = 'vocab_words'
            """
        ).fetchone()
        if legacy_vocab_words_exists:
            conn.execute(
                """
                INSERT OR IGNORE INTO vocab_items(
                    session_id,
                    target_word,
                    translation,
                    exposure_count,
                    unlocked
                )
                SELECT session_id, target_word, translation, exposure_count, unlocked
                FROM vocab_words
                """
            )
