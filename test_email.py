import imaplib
import smtplib

from app.config import IMAP_HOST, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER

print("SMTP_USER set:", bool(SMTP_USER), "| SMTP_PASSWORD set:", bool(SMTP_PASSWORD))

try:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASSWORD)
    print("SEND login OK")
except Exception as e:
    print("SEND login FAILED:", e)

try:
    m = imaplib.IMAP4_SSL(IMAP_HOST)
    m.login(SMTP_USER, SMTP_PASSWORD)
    m.logout()
    print("READ login OK")
except Exception as e:
    print("READ login FAILED:", e)