from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

UPI_ID = os.getenv("UPI_ID", "")
UPI_NAME = os.getenv("UPI_NAME", "LoadShare Food")

# Email (Gmail with an app password)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SUPPORT_NAME = os.getenv("SUPPORT_NAME", "LoadShare Support")

_required = {"DATABASE_URL": DATABASE_URL, "SECRET_KEY": SECRET_KEY}
_missing = [name for name, value in _required.items() if not value]
if _missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(_missing)}")