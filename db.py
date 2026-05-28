import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "progress.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                lesson_id   INTEGER PRIMARY KEY,
                completed   INTEGER DEFAULT 0,
                score       REAL DEFAULT 0.0,
                attempts    INTEGER DEFAULT 0,
                updated_at  TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                level       TEXT PRIMARY KEY,
                passed      INTEGER DEFAULT 0,
                best_score  REAL DEFAULT 0.0,
                attempts    INTEGER DEFAULT 0,
                updated_at  TEXT
            )
        """)


def get_lesson_progress(lesson_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM progress WHERE lesson_id = ?", (lesson_id,)
        ).fetchone()
        if row:
            return dict(row)
        return {"lesson_id": lesson_id, "completed": 0, "score": 0.0, "attempts": 0}


def save_lesson_result(lesson_id: int, score: float):
    completed = 1 if score >= 0.5 else 0
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO progress (lesson_id, completed, score, attempts, updated_at)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(lesson_id) DO UPDATE SET
                completed = MAX(completed, excluded.completed),
                score     = MAX(score, excluded.score),
                attempts  = attempts + 1,
                updated_at = excluded.updated_at
        """, (lesson_id, completed, score, now))


def get_test_result(level: str) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM test_results WHERE level = ?", (level,)
        ).fetchone()
        if row:
            return dict(row)
        return {"level": level, "passed": 0, "best_score": 0.0, "attempts": 0}


def save_test_result(level: str, score: float, pass_threshold: float = 0.6):
    passed = 1 if score >= pass_threshold else 0
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO test_results (level, passed, best_score, attempts, updated_at)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(level) DO UPDATE SET
                passed     = MAX(passed, excluded.passed),
                best_score = MAX(best_score, excluded.best_score),
                attempts   = attempts + 1,
                updated_at = excluded.updated_at
        """, (level, passed, score, now))


def get_all_progress() -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM progress ORDER BY lesson_id"
        ).fetchall()
        return [dict(r) for r in rows]
