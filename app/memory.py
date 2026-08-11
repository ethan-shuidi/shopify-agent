import sqlite3
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    role: str
    content: str


class SQLiteMemory:
    """Small, thread-safe conversation store and event deduplication ledger."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self._write_lock = threading.Lock()

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_conversation_session_id
                ON conversation_messages(session_id, id);

                CREATE TABLE IF NOT EXISTS processed_events (
                    message_id TEXT PRIMARY KEY,
                    processed_at TEXT NOT NULL
                );
                """
            )

    def claim_event(self, message_id: str) -> bool:
        """Return True once for each Feishu message ID."""
        with self._write_lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO processed_events(message_id, processed_at)
                VALUES (?, ?)
                """,
                (message_id, _now()),
            )
            return cursor.rowcount == 1

    def add(self, session_id: str, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError(f"Unsupported conversation role: {role}")
        with self._write_lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_messages(session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, role, content, _now()),
            )

    def recent(self, session_id: str, limit: int) -> list[ConversationMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return [ConversationMessage(role=row[0], content=row[1]) for row in reversed(rows)]

    def reset(self, session_id: str) -> int:
        with self._write_lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM conversation_messages WHERE session_id = ?",
                (session_id,),
            )
            return cursor.rowcount

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path, timeout=10)


def _now() -> str:
    return datetime.now(UTC).isoformat()

