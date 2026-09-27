"""Abstract storage interface for the Akinator bot.

Why a flat file (db_base.py) instead of a store/ package: this repo is a
flat single-purpose bot (config.py, database.py, keyboard.py, strings.py).
A package would add __init__ plumbing and import-path churn for no benefit;
one module keeps `from database import X` working untouched.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class Store(ABC):
    """Persistence contract every DB provider must implement.

    All user-facing semantics live here (defaults, upsert behaviour, which
    leaderboard fields are legal). Providers only translate these to their
    backend. Every method must be thread-safe.
    """

    @abstractmethod
    def init_db(self) -> None:
        """Create schema / collections / indexes if missing. Idempotent."""
        raise NotImplementedError

    # -- users ----------------------------------------------------------
    @abstractmethod
    def addUser(self, user_id: int, first_name: str, last_name: str, user_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def updateUser(self, user_id: int, first_name: str, last_name: str, user_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def getUser(self, user_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def totalUsers(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def getAllUserIds(self) -> List[int]:
        raise NotImplementedError

    # -- user settings / stats ------------------------------------------
    @abstractmethod
    def getLanguage(self, user_id: int) -> str:
        raise NotImplementedError

    @abstractmethod
    def updateLanguage(self, user_id: int, lang_code: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def getChildMode(self, user_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def updateChildMode(self, user_id: int, mode: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def getTotalGuess(self, user_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def updateTotalGuess(self, user_id: int, total_guess: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def getCorrectGuess(self, user_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def updateCorrectGuess(self, user_id: int, correct_guess: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def getWrongGuess(self, user_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def updateWrongGuess(self, user_id: int, wrong_guess: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def getUnfinishedGuess(self, user_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def getTotalQuestions(self, user_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def updateTotalQuestions(self, user_id: int, total_questions: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def getLead(self, what: str) -> List[Tuple[str, Any]]:
        raise NotImplementedError

    # -- groups ----------------------------------------------------------
    @abstractmethod
    def addgroup(self, chat_id: int, title: str, username: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def updategroup(self, chat_id: int, title: str, username: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def getAllGroups(self) -> List[int]:
        raise NotImplementedError

    @abstractmethod
    def gettitle(self, chat_id: int) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def delete_group(self, chat_id: int) -> None:
        raise NotImplementedError

    # -- last-message routing --------------------------------------------
    @abstractmethod
    def add_last_msg_id(self, user_id: int, last_msg_id: int, chat_id: int, current_msg_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_last_msg_id(self, user_id: int, last_msg_id: int, chat_id: int, current_msg_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_last_msg_id(self, user_id: int) -> Optional[int]:
        raise NotImplementedError

    @abstractmethod
    def get_chat_id(self, user_id: int, last_msg_id: int) -> Optional[int]:
        raise NotImplementedError

    @abstractmethod
    def get_user_id(self, last_msg_id: int, chat_id: int) -> Optional[int]:
        raise NotImplementedError

    # -- admin-relay message data -----------------------------------------
    @abstractmethod
    def add_user_message_data(
        self,
        message_id_in_admin_chat: int,
        message_id_in_user_chat: int,
        user_id: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_user_message_data(
        self, message_id_in_admin_chat: int
    ) -> Tuple[Optional[int], Optional[int]]:
        raise NotImplementedError

    @abstractmethod
    def delete_old_user_chatting_data(self) -> None:
        raise NotImplementedError
