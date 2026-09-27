"""Thin facade preserving the historic ``from database import X`` API.

The real logic lives in provider modules behind the :class:`db_base.Store`
interface (currently :class:`db_sqlite.SQLiteStore`). This module only picks
a provider from ``config.DB_PROVIDER``, instantiates it once, and delegates
each public function to it -- so ``__main__.py`` needs no changes.

How to add a provider (e.g. MongoDB/Postgres), 3 steps:
  1. Create a new file (e.g. ``db_mongo.py``) with a class implementing
     :class:`db_base.Store` (all methods, thread-safe, schema init in
     ``__init__``). No new third-party deps without updating requirements.
  2. Add one registry line below: ``_STORE_FACTORIES["mongo"] = lambda:
     MongoStore(...)`` (plus any config values it needs in config.py).
  3. Set ``DB_PROVIDER=mongo`` in the environment. Done -- no changes to
     ``__main__.py`` or any other caller.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

from config import DB_PROVIDER, SQLITE_PATH
from db_base import Store
from db_sqlite import SQLiteStore

__all__ = [
    "SQLITE_PATH",
    "store",
    "get_store",
    "init_db",
    "addUser",
    "addgroup",
    "add_last_msg_id",
    "update_last_msg_id",
    "get_last_msg_id",
    "get_chat_id",
    "get_user_id",
    "updategroup",
    "totalUsers",
    "updateUser",
    "getUser",
    "getLanguage",
    "getChildMode",
    "getTotalGuess",
    "getCorrectGuess",
    "getWrongGuess",
    "getUnfinishedGuess",
    "getTotalQuestions",
    "updateLanguage",
    "updateChildMode",
    "updateTotalGuess",
    "updateCorrectGuess",
    "updateWrongGuess",
    "updateTotalQuestions",
    "getLead",
    "getAllUserIds",
    "getAllGroups",
    "gettitle",
    "add_user_message_data",
    "find_user_message_data",
    "delete_group",
    "delete_old_user_chatting_data",
]

_STORE_FACTORIES: Dict[str, Callable[[], Store]] = {
    "sqlite": lambda: SQLiteStore(SQLITE_PATH),
}


def _create_store(provider: str) -> Store:
    if provider in _STORE_FACTORIES:
        return _STORE_FACTORIES[provider]()
    if provider in ("mongo", "mongodb"):
        raise RuntimeError(
            "DB_PROVIDER='mongodb' is not available: pymongo is not installed. "
            "Set DB_PROVIDER=sqlite, or add a MongoDB provider "
            "(see the 3-step recipe in database.py's docstring)."
        )
    raise RuntimeError(
        f"Unknown DB_PROVIDER={provider!r}. "
        f"Known providers: {sorted(_STORE_FACTORIES)}. "
        "Set DB_PROVIDER to one of them (or register a new one; "
        "see the 3-step recipe in database.py's docstring)."
    )


store: Store = _create_store(DB_PROVIDER)


def get_store() -> Store:
    """Return the active process-wide :class:`db_base.Store` instance."""
    return store


def init_db() -> None:
    store.init_db()


def addUser(user_id: int, first_name: str, last_name: str, user_name: str) -> None:
    """
    Adding the User to the database. If user already present in the database,
    it will check for any changes in the user_name, first_name, last_name and will update if true.
    """
    store.addUser(user_id, first_name, last_name, user_name)


def addgroup(chat_id: int, title: str, username: str) -> None:
    store.addgroup(chat_id, title, username)


def add_last_msg_id(user_id: int, last_msg_id: int, chat_id: int, current_msg_id: int) -> None:
    store.add_last_msg_id(user_id, last_msg_id, chat_id, current_msg_id)


def update_last_msg_id(user_id: int, last_msg_id: int, chat_id: int, current_msg_id: int) -> None:
    store.update_last_msg_id(user_id, last_msg_id, chat_id, current_msg_id)


def get_last_msg_id(user_id: int) -> Optional[int]:
    return store.get_last_msg_id(user_id)


def get_chat_id(user_id: int, last_msg_id: int) -> Optional[int]:
    return store.get_chat_id(user_id, last_msg_id)


def get_user_id(last_msg_id: int, chat_id: int) -> Optional[int]:
    return store.get_user_id(last_msg_id, chat_id)


def updategroup(chat_id: int, title: str, username: str) -> None:
    store.updategroup(chat_id, title, username)


def totalUsers() -> int:
    return store.totalUsers()


def updateUser(user_id: int, first_name: str, last_name: str, user_name: str) -> None:
    """
    Update a User in the collection (Table).
    """
    store.updateUser(user_id, first_name, last_name, user_name)


def getUser(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Returns the user document (Record)
    """
    return store.getUser(user_id)


def getLanguage(user_id: int) -> str:
    """
    Gets(Returns) the Language Code of the user. (str)
    """
    return store.getLanguage(user_id)


def getChildMode(user_id: int) -> int:
    """
    Get(Returns) the Child mode status of the user. (str)
    """
    return store.getChildMode(user_id)


def getTotalGuess(user_id: int) -> int:
    return store.getTotalGuess(user_id)


def getCorrectGuess(user_id: int) -> int:
    return store.getCorrectGuess(user_id)


def getWrongGuess(user_id: int) -> int:
    return store.getWrongGuess(user_id)


def getUnfinishedGuess(user_id: int) -> int:
    return store.getUnfinishedGuess(user_id)


def getTotalQuestions(user_id: int) -> int:
    """
    """
    return store.getTotalQuestions(user_id)


def updateLanguage(user_id: int, lang_code: str) -> None:
    """
    Update Akinator Language for the User.
    """
    store.updateLanguage(user_id, lang_code)


def updateChildMode(user_id: int, mode: int) -> None:
    """
    Update Child Mode of the User.
    """
    store.updateChildMode(user_id, mode)


def updateTotalGuess(user_id: int, total_guess: int) -> None:
    store.updateTotalGuess(user_id, total_guess)


def updateCorrectGuess(user_id: int, correct_guess: int) -> None:
    store.updateCorrectGuess(user_id, correct_guess)


def updateWrongGuess(user_id: int, wrong_guess: int) -> None:
    store.updateWrongGuess(user_id, wrong_guess)


def updateTotalQuestions(user_id: int, total_questions: int) -> None:
    store.updateTotalQuestions(user_id, total_questions)


def getLead(what: str) -> List[Tuple[str, Any]]:
    return store.getLead(what)


def getAllUserIds() -> List[int]:
    """
    Get a list of all user IDs available in the database.
    """
    return store.getAllUserIds()


def getAllGroups() -> List[int]:
    return store.getAllGroups()


def gettitle(chat_id: int) -> Optional[str]:
    return store.gettitle(chat_id)


def add_user_message_data(
    message_id_in_admin_chat: int, message_id_in_user_chat: int, user_id: int
) -> None:
    """stores the data of the user message for replying to it later

    Args:
        message_id_in_admin_chat (int): message id of the message which is forwarded from the user by the bot to admin
    """
    store.add_user_message_data(message_id_in_admin_chat, message_id_in_user_chat, user_id)


def find_user_message_data(
    message_id_in_admin_chat: int,
) -> Tuple[Optional[int], Optional[int]]:
    """retrives the message_id and user id using the message_id of the forwaerded message used for replying to the message

    Args:
        message_id_in_admin_chat (int): message id of the message which is forwarded from the user by the bot to admin

    Returns:
        user_id: int
        message_id:int
    """
    return store.find_user_message_data(message_id_in_admin_chat)


def delete_group(chat_id: int) -> None:
    """
    Deletes a group based on the provided chat_id.
    """
    store.delete_group(chat_id)


def delete_old_user_chatting_data() -> None:
    store.delete_old_user_chatting_data()
