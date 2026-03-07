import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

# Database
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "url_shortener")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")

# Redis
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
REDIS_URL = os.environ.get("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}")

# Authentication
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-change-in-production")
JWT_LIFETIME_SECONDS = int(os.environ.get("JWT_LIFETIME_SECONDS", "3600"))

# Application
APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
APP_PORT = int(os.environ.get("PORT", os.environ.get("APP_PORT", "8000")))
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")

# Link settings
DEFAULT_LINK_EXPIRATION_DAYS = 365
MAX_CUSTOM_ALIAS_LENGTH = 50
SHORT_CODE_LENGTH = 6
UNUSED_LINKS_DAYS = int(os.environ.get("UNUSED_LINKS_DAYS", "90"))
CLEANUP_INTERVAL_HOURS = int(os.environ.get("CLEANUP_INTERVAL_HOURS", "24"))
