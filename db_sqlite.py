"""SQLite implementation of the :class:`db_base.Store` contract.

Moved verbatim from the old monolithic database.py: per-call connections,
a write lock, WAL mode, schema creation, upserts, ISO-8601 UTC ``created_at``
strings (lexicographically comparable for the 24h cleanup), and an
allowlisted leaderboard field for ``getLead``.

Thread-safety: an instance-level :class:`threading.RLock` (re-entrant, so
composed helpers such as ``getUnfinishedGuess`` cannot deadlock) guards every
operation, exactly as the former module-global ``Lock`` did.
"""

import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from db_base import Store


class SQLiteStore(Store):
    """Store backed by a SQLite file. Schema is created on construction."""

    LEAD_ALLOWLIST = frozenset(
        {
            "total_guess",
            "correct_guess",
            "wrong_guess",
            "total_questions",
            "unfinished_guess",
        }
    )

    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = threading.RLock()
        self.init_db()

    # -- internals ------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA busy_timeout = 30000")
        except sqlite3.Error:
            pass
        return conn

    def init_db(self) -> None:
        parent = Path(self._path).expanduser().parent
        if str(parent) and str(parent) != ".":
            parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            conn = self._connect()
            try:
                try:
                    conn.execute("PRAGMA journal_mode=WAL")
                except sqlite3.Error:
                    pass
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        first_name TEXT,
                        last_name TEXT,
                        user_name TEXT,
                        aki_lang TEXT DEFAULT 'en',
                        child_mode INTEGER DEFAULT 1,
                        total_guess INTEGER DEFAULT 0,
                        correct_guess INTEGER DEFAULT 0,
                        wrong_guess INTEGER DEFAULT 0,
                        unfinished_guess INTEGER DEFAULT 0,
                        total_questions INTEGER DEFAULT 0
                    )"""
                )
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS groups (
                        chat_id INTEGER PRIMARY KEY,
                        title TEXT,
                        username TEXT
                    )"""
                )
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS last_msg_ids (
                        user_id INTEGER PRIMARY KEY,
                        last_msg_id INTEGER,
                        chat_id INTEGER,
                        current_msg_id INTEGER
                    )"""
                )
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS user_chatting_data (
                        message_id_in_admin_chat INTEGER PRIMARY KEY,
                        message_id_in_user_chat INTEGER,
                        user_id INTEGER,
                        created_at TEXT
                    )"""
                )
                conn.commit()
            finally:
                conn.close()

    # -- users ----------------------------------------------------------
    def addUser(self, user_id: int, first_name: str, last_name: str, user_name: str) -> None:
        """
        Adding the User to the database. If user already present in the database,
        it will check for any changes in the user_name, first_name, last_name and will update if true.
        """
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
                if row is None:
                    conn.execute(
                        """INSERT INTO users
                           (user_id, first_name, last_name, user_name, aki_lang, child_mode,
                            total_guess, correct_guess, wrong_guess, unfinished_guess, total_questions)
                           VALUES (?, ?, ?, ?, 'en', 1, 0, 0, 0, 0, 0)""",
                        (user_id, first_name, last_name, user_name),
                    )
                    conn.commit()
                else:
                    conn.execute(
                        """UPDATE users SET first_name = ?, last_name = ?, user_name = ?
                           WHERE user_id = ?""",
                        (first_name, last_name, user_name, user_id),
                    )
                    conn.commit()
            finally:
                conn.close()

    def updateUser(self, user_id: int, first_name: str, last_name: str, user_name: str) -> None:
        """
        Update a User in the collection (Table).
        """
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """UPDATE users SET user_name = ?, first_name = ?, last_name = ?
                       WHERE user_id = ?""",
                    (user_name, first_name, last_name, user_id),
                )
                conn.commit()
            finally:
                conn.close()

    def getUser(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Returns the user document (Record)
        """
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
                if row is None:
                    return None
                return dict(row)
            finally:
                conn.close()

    def totalUsers(self) -> int:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
                return int(row["c"]) if row is not None else 0
            finally:
                conn.close()

    def getAllUserIds(self) -> List[int]:
        """
        Get a list of all user IDs available in the database.
        """
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute("SELECT user_id FROM users").fetchall()
                return [row["user_id"] for row in rows]
            finally:
                conn.close()

    # -- user settings / stats ------------------------------------------
    def _get_user_field(self, user_id: int, field: str, default: Any) -> Any:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    f"SELECT {field} FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
                if row is None or row[field] is None:
                    return default
                return row[field]
            finally:
                conn.close()

    def getLanguage(self, user_id: int) -> str:
        """
        Gets(Returns) the Language Code of the user. (str)
        """
        value = self._get_user_field(user_id, "aki_lang", "en")
        return value if value is not None else "en"

    def updateLanguage(self, user_id: int, lang_code: str) -> None:
        """
        Update Akinator Language for the User.
        """
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE users SET aki_lang = ? WHERE user_id = ?",
                    (lang_code, user_id),
                )
                conn.commit()
            finally:
                conn.close()

    def getChildMode(self, user_id: int) -> int:
        """
        Get(Returns) the Child mode status of the user. (str)
        """
        value = self._get_user_field(user_id, "child_mode", 1)
        return value if value is not None else 1

    def updateChildMode(self, user_id: int, mode: int) -> None:
        """
        Update Child Mode of the User.
        """
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE users SET child_mode = ? WHERE user_id = ?",
                    (mode, user_id),
                )
                conn.commit()
            finally:
                conn.close()

    def getTotalGuess(self, user_id: int) -> int:
        value = self._get_user_field(user_id, "total_guess", 0)
        return value if value is not None else 0

    def updateTotalGuess(self, user_id: int, total_guess: int) -> None:
        new_total = self.getTotalGuess(user_id) + total_guess
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE users SET total_guess = ? WHERE user_id = ?",
                    (new_total, user_id),
                )
                conn.commit()
            finally:
                conn.close()

    def getCorrectGuess(self, user_id: int) -> int:
        value = self._get_user_field(user_id, "correct_guess", 0)
        return value if value is not None else 0

    def updateCorrectGuess(self, user_id: int, correct_guess: int) -> None:
        new_value = self.getCorrectGuess(user_id) + correct_guess
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE users SET correct_guess = ? WHERE user_id = ?",
                    (new_value, user_id),
                )
                conn.commit()
            finally:
                conn.close()

    def getWrongGuess(self, user_id: int) -> int:
        value = self._get_user_field(user_id, "wrong_guess", 0)
        return value if value is not None else 0

    def updateWrongGuess(self, user_id: int, wrong_guess: int) -> None:
        new_value = self.getWrongGuess(user_id) + wrong_guess
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE users SET wrong_guess = ? WHERE user_id = ?",
                    (new_value, user_id),
                )
                conn.commit()
            finally:
                conn.close()

    def getUnfinishedGuess(self, user_id: int) -> int:
        crct_wrong_guess = self.getCorrectGuess(user_id) + self.getWrongGuess(user_id)
        unfinished_guess = self.getTotalGuess(user_id) - crct_wrong_guess
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE users SET unfinished_guess = ? WHERE user_id = ?",
                    (unfinished_guess, user_id),
                )
                conn.commit()
                row = conn.execute(
                    "SELECT unfinished_guess FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
                if row is None or row["unfinished_guess"] is None:
                    return 0
                return row["unfinished_guess"]
            finally:
                conn.close()

    def getTotalQuestions(self, user_id: int) -> int:
        """
        """
        value = self._get_user_field(user_id, "total_questions", 0)
        return value if value is not None else 0

    def updateTotalQuestions(self, user_id: int, total_questions: int) -> None:
        new_value = total_questions + self.getTotalQuestions(user_id)
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE users SET total_questions = ? WHERE user_id = ?",
                    (new_value, user_id),
                )
                conn.commit()
            finally:
                conn.close()

    def getLead(self, what: str) -> List[Tuple[str, Any]]:
        if what not in self.LEAD_ALLOWLIST:
            raise ValueError(f"Invalid leaderboard field: {what!r}")
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    f"SELECT first_name, {what} FROM users ORDER BY {what} DESC LIMIT 10"
                ).fetchall()
                result = [
                    (row["first_name"], row[what]) for row in rows
                ]
                result.sort(
                    key=lambda x: x[1] if x[1] is not None else 0, reverse=True
                )
                return result[:10]
            finally:
                conn.close()

    # -- groups ----------------------------------------------------------
    def addgroup(self, chat_id: int, title: str, username: str) -> None:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT chat_id FROM groups WHERE chat_id = ?", (chat_id,)
                ).fetchone()
                if row is None:
                    conn.execute(
                        "INSERT INTO groups (chat_id, title, username) VALUES (?, ?, ?)",
                        (chat_id, title, username),
                    )
                else:
                    conn.execute(
                        "UPDATE groups SET title = ?, username = ? WHERE chat_id = ?",
                        (title, username, chat_id),
                    )
                conn.commit()
            finally:
                conn.close()

    def updategroup(self, chat_id: int, title: str, username: str) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    "UPDATE groups SET title = ?, username = ? WHERE chat_id = ?",
                    (title, username, chat_id),
                )
                conn.commit()
            finally:
                conn.close()

    def getAllGroups(self) -> List[int]:
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute("SELECT chat_id FROM groups").fetchall()
                return [row["chat_id"] for row in rows]
            finally:
                conn.close()

    def gettitle(self, chat_id: int) -> Optional[str]:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT title FROM groups WHERE chat_id = ?", (chat_id,)
                ).fetchone()
                if row is None:
                    return None
                return row["title"]
            finally:
                conn.close()

    def delete_group(self, chat_id: int) -> None:
        """
        Deletes a group based on the provided chat_id.
        """
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("DELETE FROM groups WHERE chat_id = ?", (chat_id,))
                conn.commit()
            finally:
                conn.close()

    # -- last-message routing --------------------------------------------
    def add_last_msg_id(self, user_id: int, last_msg_id: int, chat_id: int, current_msg_id: int) -> None:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT user_id FROM last_msg_ids WHERE user_id = ?", (user_id,)
                ).fetchone()
                if row is None:
                    conn.execute(
                        """INSERT INTO last_msg_ids
                           (user_id, last_msg_id, chat_id, current_msg_id)
                           VALUES (?, ?, ?, ?)""",
                        (user_id, last_msg_id, chat_id, current_msg_id),
                    )
                else:
                    conn.execute(
                        """UPDATE last_msg_ids SET last_msg_id = ?, chat_id = ?,
                           current_msg_id = ? WHERE user_id = ?""",
                        (last_msg_id, chat_id, current_msg_id, user_id),
                    )
                conn.commit()
            finally:
                conn.close()

    def update_last_msg_id(self, user_id: int, last_msg_id: int, chat_id: int, current_msg_id: int) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """INSERT INTO last_msg_ids (user_id, last_msg_id, chat_id, current_msg_id)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(user_id) DO UPDATE SET
                         last_msg_id = excluded.last_msg_id,
                         chat_id = excluded.chat_id,
                         current_msg_id = excluded.current_msg_id""",
                    (user_id, last_msg_id, chat_id, current_msg_id),
                )
                conn.commit()
            finally:
                conn.close()

    def get_last_msg_id(self, user_id: int) -> Optional[int]:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT last_msg_id FROM last_msg_ids WHERE user_id = ?", (user_id,)
                ).fetchone()
                if row is None:
                    return None
                return row["last_msg_id"]
            finally:
                conn.close()

    def get_chat_id(self, user_id: int, last_msg_id: int) -> Optional[int]:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT chat_id FROM last_msg_ids WHERE user_id = ? AND last_msg_id = ?",
                    (user_id, last_msg_id),
                ).fetchone()
                if row is None:
                    return None
                return row["chat_id"]
            finally:
                conn.close()

    def get_user_id(self, last_msg_id: int, chat_id: int) -> Optional[int]:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT user_id FROM last_msg_ids WHERE last_msg_id = ? AND chat_id = ?",
                    (last_msg_id, chat_id),
                ).fetchone()
                if row is None:
                    return None
                return row["user_id"]
            finally:
                conn.close()

    # -- admin-relay message data -----------------------------------------
    def add_user_message_data(
        self,
        message_id_in_admin_chat: int,
        message_id_in_user_chat: int,
        user_id: int,
    ) -> None:
        """stores the data of the user message for replying to it later

        Args:
            message_id_in_admin_chat (int): message id of the message which is forwarded from the user by the bot to admin
        """
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT message_id_in_admin_chat FROM user_chatting_data WHERE message_id_in_admin_chat = ?",
                    (message_id_in_admin_chat,),
                ).fetchone()
                if row is None:
                    conn.execute(
                        """INSERT INTO user_chatting_data
                           (user_id, message_id_in_admin_chat, message_id_in_user_chat, created_at)
                           VALUES (?, ?, ?, ?)""",
                        (
                            user_id,
                            message_id_in_admin_chat,
                            message_id_in_user_chat,
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )
                    conn.commit()
            finally:
                conn.close()

    def find_user_message_data(
        self, message_id_in_admin_chat: int
    ) -> Tuple[Optional[int], Optional[int]]:
        """retrives the message_id and user id using the message_id of the forwaerded message used for replying to the message

        Args:
            message_id_in_admin_chat (int): message id of the message which is forwarded from the user by the bot to admin

        Returns:
            user_id: int
            message_id:int
        """
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    """SELECT message_id_in_user_chat, user_id FROM user_chatting_data
                       WHERE message_id_in_admin_chat = ?""",
                    (message_id_in_admin_chat,),
                ).fetchone()
                if row is not None:
                    # If data is found, return the message_id_in_user_chat and user_id
                    return row["message_id_in_user_chat"], row["user_id"]
                else:
                    # Return None if the message_id_in_admin_chat is not found
                    return None, None
            finally:
                conn.close()

    def delete_old_user_chatting_data(self) -> None:
        with self._lock:
            conn = self._connect()
            try:
                # Define the time threshold for deletion (24 hours ago from the current time)
                threshold_time = datetime.now(timezone.utc) - timedelta(hours=24)
                # created_at stored as timezone-aware ISO strings; ISO-8601 UTC strings compare lexicographically.
                conn.execute(
                    "DELETE FROM user_chatting_data WHERE created_at < ?",
                    (threshold_time.isoformat(),),
                )
                conn.commit()
            finally:
                conn.close()
