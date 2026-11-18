from app.ai.llm import llm
from app.ai.rag.rag_chain import ask
from app.models.order import Order, OrderStatus
from app.services.tracking_service import add_tracking
from app.services.realtime import publish


def process_complaint(db, complaint, user, order=None):
    """Handle a complaint automatically.

    Returns (reply_text, resolved).
    The AI can cancel a Pending order. It never approves refunds.
    """
    text = f"{complaint.subject}. {complaint.description}"

    # 1) Cancellation request on a Pending order: do it directly
    if order is not None and "cancel" in text.lower() \
            and order.order_status == OrderStatus.pending:

        order.order_status = OrderStatus.cancelled
        add_tracking(db, order, OrderStatus.cancelled, user.id,
                     "Cancelled at customer request (support agent)")
        complaint.status = "Resolved"
        db.commit()

        publish(set(), {"admin"}, {"type": "order_update", "order_id": order.id})

        return (
            f"Hi {user.full_name},\n\n"
            f"As you asked, we have cancelled order {order.order_number}. "
            f"No further action is needed.\n\nLoadShare Support"
        ), True

    # 2) Everything else: answer from policy and facts, then hand to the team
    facts = "No specific order was mentioned."
    if order is not None:
        facts = (
            f"Order {order.order_number}, status {order.order_status.value}, "
            f"payment {order.payment_status.value}."
        )

    try:
        policy = ask(text)
    except Exception:
        policy = "No policy information available."

    prompt = f"""You are a polite customer support agent for LoadShare Food.
Write a short email reply (max 120 words) to the customer.

Customer message: {text}
Order facts: {facts}
Company policy answer: {policy}

Rules:
- Use only the facts above. Do not invent details.
- Do NOT promise a refund. Say our team will review the case and reply within 24 hours.
- Plain text, no markdown, no subject line.
- Start with "Hi {user.full_name},"
- End with "LoadShare Support"
"""

    try:
        reply = llm.invoke(prompt).content.replace("**", "")
    except Exception:
        reply = (
            f"Hi {user.full_name},\n\nThank you for contacting us. "
            f"Our team will review your issue and reply within 24 hours.\n\n"
            f"LoadShare Support"
        )

    complaint.status = "In Progress"
    db.commit()

    return reply, False