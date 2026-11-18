import smtplib
import threading
from email.message import EmailMessage

from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SUPPORT_NAME


def email_enabled() -> bool:
    return bool(SMTP_USER and SMTP_PASSWORD)


def _send(msg: EmailMessage) -> None:
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"[email] sent to {msg['To']}: {msg['Subject']}")
    except Exception as e:
        print(f"[email] FAILED to {msg['To']}: {e}")


def send_email(to: str, subject: str, body: str) -> bool:
    """Send in a background thread so requests are never slowed down."""
    if not email_enabled():
        print(f"[email] not configured, skipped: {subject}")
        return False

    msg = EmailMessage()
    msg["From"] = f"{SUPPORT_NAME} <{SMTP_USER}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Auto-Submitted"] = "auto-replied"
    msg.set_content(body)

    threading.Thread(target=_send, args=(msg,), daemon=True).start()
    return True


# ---------------- order emails ----------------
_last_emailed = {}   # order_id -> last status emailed (avoids duplicates)

_MESSAGES = {
    "Pending": "We have received your order.",
    "Assigned": "A delivery partner has been assigned to your order.",
    "Picked Up": "Your order has been picked up.",
    "In Transit": "Your order is out for delivery.",
    "Delivered": "Your order has been delivered. Enjoy!",
    "Cancelled": "Your order has been cancelled.",
}


def email_order_update(order) -> None:
    try:
        status = getattr(order.order_status, "value", order.order_status)

        if _last_emailed.get(order.id) == status:
            return
        _last_emailed[order.id] = status

        user = order.customer.user
        if not user or not user.email:
            return

        total = float(order.delivery_charge) + float(order.items_total or 0)
        eta = ""
        if order.eta_minutes and status not in ("Delivered", "Cancelled"):
            eta = f"\nEstimated arrival: about {order.eta_minutes} minutes."

        body = (
            f"Hi {user.full_name},\n\n"
            f"{_MESSAGES.get(status, 'Your order was updated.')}\n\n"
            f"Order: {order.order_number}\n"
            f"Status: {status}\n"
            f"Total: Rs {total:.2f}{eta}\n\n"
            f"Reply to this email if you need help.\n"
            f"{SUPPORT_NAME}"
        )
        send_email(user.email, f"Order {order.order_number}: {status}", body)

    except Exception as e:
        print(f"[email] order email skipped: {e}")