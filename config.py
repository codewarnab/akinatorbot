from json import load
import os
from dotenv import load_dotenv

load_dotenv()

AKI_MONGO_HOST = os.getenv("AKI_MONGO_HOST")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TELEGRAM_USER_ID = int(os.getenv("ADMIN_TELEGRAM_USER_ID"))
