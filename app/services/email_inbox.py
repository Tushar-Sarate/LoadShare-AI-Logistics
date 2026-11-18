import email
import imaplib
import re
import threading
import time
from email.header import decode_header, make_header
from email.utils import parseaddr

from app.config import IMAP_HOST, SMTP_USER, SMTP_PASSWORD
from app.database import SessionLocal

# Import all models so SQLAlchemy can resolve relationships
from app.models.user import User
from app.models.customer import Customer
from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order, OrderStatus
from app.models.payment import Payment
from app.models.tracking import Tracking
from app.models.complaint import Complaint
from app.models.restaurant import Restaurant, MenuItem
from app.models.order_item import OrderItem

from app.ai.guardrails import check_input
from app.ai.langchain.chains import intent_chain
from app.ai.langgraph.workflow import run_workflow
from app.services.email_service import send_email, email_enabled
from app.services.support_agent import process_complaint

POLL_SECONDS = 60
MAX_REPLIES_PER_HOUR = 5

_replies = {}   # sender -> list of timestamps


def _rate_limited(sender: str) -> bool:
    now = time.time()
    recent = [t for t in _replies.get(sender, []) if now - t < 3600]
    _replies[sender] = recent
    if len(recent) >= MAX_REPLIES_PER_HOUR:
        return True
    recent.append(now)
    return False


def _clean(value) -> str:
    try:
        return str(make_header(decode_header(value or "")))
    except Exception:
        return value or ""


def _body(msg) -> str:
    text = ""
    if msg.is_multipart():
        for part in msg.walk():
            disposition = str(part.get("Content-Disposition", ""))
            if part.get_content_type() == "text/plain" and "attachment" not in disposition:
                text = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", "replace")
                break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            text = payload.decode(msg.get_content_charset() or "utf-8", "replace")

    # Remove quoted replies
    lines = []
    for line in text.splitlines():
        if line.strip().startswith(">") or re.match(r"^On .* wrote:", line.strip()):
            break
        lines.append(line)

    return "\n".join(lines).strip()[:1500]


def _find_order(db, customer, text):
    match = re.search(r"LS-[A-Z0-9]{10}", text.upper())

    if match:
        order = db.query(Order).filter(
            Order.order_number == match.group(0),
            Order.customer_id == customer.id
        ).first()
        if order:
            return order

    return db.query(Order).filter(
        Order.customer_id == customer.id
    ).order_by(Order.created_at.desc()).first()


def _handle(db, msg) -> None:
    sender = parseaddr(msg.get("From", ""))[1].lower()
    subject = _clean(msg.get("Subject", "(no subject)"))

    # Never answer ourselves, bots or auto-replies (prevents email loops)
    if (
        not sender
        or sender == SMTP_USER.lower()
        or re.search(r"no-?reply|mailer-daemon|postmaster", sender)
        or msg.get("Auto-Submitted", "no").lower() != "no"
        or msg.get("Precedence", "").lower() in ("bulk", "junk", "list")
    ):
        return

    if _rate_limited(sender):
        print(f"[inbox] rate limit reached for {sender}")
        return

    reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    body = _body(msg)
    text = f"{subject}. {body}".strip()

    user = db.query(User).filter(User.email == sender).first()

    if not user or user.role != "customer":
        send_email(
            sender, reply_subject,
            "Hello,\n\nWe could not find a customer account for this email address. "
            "Please register in the LoadShare Food app with this email, then write to us again.\n\n"
            "LoadShare Support"
        )
        return

    refusal = check_input(text)
    if refusal:
        send_email(sender, reply_subject, refusal + "\n\nLoadShare Support")
        return

    customer = db.query(Customer).filter(Customer.user_id == user.id).first()
    if not customer:
        send_email(
            sender, reply_subject,
            "Please complete your customer profile in the app first.\n\nLoadShare Support"
        )
        return

    order = _find_order(db, customer, text)

    try:
        intent = intent_chain.invoke({"question": text}).strip().lower()
    except Exception:
        intent = "other"

    # Complaint or cancellation: create it and let the support agent act
    if intent == "complaint" or "cancel" in text.lower():
        from app.models.complaint import Complaint as ComplaintModel

        complaint = ComplaintModel(
            customer_id=customer.id,
            order_id=order.id if order else None,
            subject=subject[:150] if len(subject) >= 5 else "Customer email",
            description=body if len(body) >= 10 else (body + " (sent by email)")
        )
        db.add(complaint)
        db.commit()
        db.refresh(complaint)

        reply, _ = process_complaint(db, complaint, user, order)
        send_email(sender, reply_subject, reply + f"\n\n(Complaint #{complaint.id})")
        return

    # Everything else goes through the same workflow as the chatbot
    question = text
    if order:
        question += f"\nMy order number is {order.order_number}"

    answer = run_workflow(
        question,
        {"id": user.id, "role": user.role}
    ).replace("**", "")

    send_email(
        sender, reply_subject,
        f"Hi {user.full_name},\n\n{answer}\n\nLoadShare Support"
    )


def _poll_once() -> None:
    imap = imaplib.IMAP4_SSL(IMAP_HOST)
    try:
        imap.login(SMTP_USER, SMTP_PASSWORD)
        imap.select("INBOX")

        status, data = imap.search(None, "UNSEEN")
        ids = data[0].split()[:10] if status == "OK" else []

        for num in ids:
            status, parts = imap.fetch(num, "(RFC822)")   # marks as read
            if status != "OK":
                continue

            msg = email.message_from_bytes(parts[0][1])

            db = SessionLocal()
            try:
                _handle(db, msg)
            except Exception as e:
                db.rollback()
                print(f"[inbox] failed to handle a message: {e}")
            finally:
                db.close()
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def _loop() -> None:
    print("[inbox] support inbox worker started")
    while True:
        try:
            _poll_once()
        except Exception as e:
            print(f"[inbox] poll error: {e}")
        time.sleep(POLL_SECONDS)


def start_inbox_worker() -> None:
    if not email_enabled():
        print("[inbox] email not configured, inbox worker not started")
        return
    threading.Thread(target=_loop, daemon=True).start()