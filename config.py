import os
from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _required_int(name: str) -> int:
    value = _required(name)
    try:
        return int(value)
    except ValueError:
        raise RuntimeError(
            f"Environment variable {name} must be an integer, got {value!r}"
        )


AKI_MONGO_HOST: str = _required("AKI_MONGO_HOST")
BOT_TOKEN: str = _required("BOT_TOKEN")
ADMIN_TELEGRAM_USER_ID: int = _required_int("ADMIN_TELEGRAM_USER_ID")
