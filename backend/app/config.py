import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "monitoring")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
GNS3_USERNAME = os.getenv("GNS3_USERNAME", "")
GNS3_PASSWORD = os.getenv("GNS3_PASSWORD", "")

GNS3_URL = os.getenv("GNS3_URL", "http://127.0.0.1:3080")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY manquante dans le .env — génère-la avec "
        "`python -c \"import secrets; print(secrets.token_hex(32))\"`"
    )

SESSION_MAX_AGE_SECONDS = 7 * 24 * 3600  # 7 jours

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)