from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class Issue:
    id: int
    chat_id: int
    message_id: int
    original_text: str
    translated_text: str
    source_language: str
    kind: str
    status: str
    created_at: str
    updated_at: str


class IssueStore:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    original_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    source_language TEXT NOT NULL,
                    kind TEXT NOT NULL DEFAULT 'unclassified',
                    status TEXT NOT NULL DEFAULT 'unprocessed',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create_issue(
        self,
        chat_id: int,
        message_id: int,
        original_text: str,
        translated_text: str,
        source_language: str,
    ) -> Issue:
        now = _now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO issues (
                    chat_id, message_id, original_text, translated_text,
                    source_language, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (chat_id, message_id, original_text, translated_text, source_language, now, now),
            )
            issue_id = int(cursor.lastrowid)
        return self.get_issue(issue_id)

    def get_issue(self, issue_id: int) -> Issue:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
        if row is None:
            raise KeyError(f"Issue {issue_id} does not exist.")
        return _issue_from_row(row)

    def update_issue(
        self,
        issue_id: int,
        *,
        kind: str | None = None,
        status: str | None = None,
    ) -> Issue:
        issue = self.get_issue(issue_id)
        next_kind = kind or issue.kind
        next_status = status or issue.status
        with self._connect() as connection:
            connection.execute(
                "UPDATE issues SET kind = ?, status = ?, updated_at = ? WHERE id = ?",
                (next_kind, next_status, _now(), issue_id),
            )
        return self.get_issue(issue_id)

    def list_open_issues(self, chat_id: int, limit: int = 20) -> list[Issue]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM issues
                WHERE chat_id = ? AND status != 'done'
                ORDER BY id DESC
                LIMIT ?
                """,
                (chat_id, limit),
            ).fetchall()
        return [_issue_from_row(row) for row in rows]

    def search_issues(self, chat_id: int, keyword: str, limit: int = 20) -> list[Issue]:
        pattern = f"%{keyword}%"
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM issues
                WHERE chat_id = ?
                  AND (original_text LIKE ? OR translated_text LIKE ?)
                ORDER BY id DESC
                LIMIT ?
                """,
                (chat_id, pattern, pattern, limit),
            ).fetchall()
        return [_issue_from_row(row) for row in rows]


def _issue_from_row(row: sqlite3.Row) -> Issue:
    return Issue(**dict(row))


def _now() -> str:
    return datetime.now(UTC).isoformat()
