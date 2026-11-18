from langchain_core.tools import tool

from app.database import SessionLocal

from app.models.user import User
from app.models.customer import Customer
from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order
from app.models.payment import Payment
from app.models.tracking import Tracking
from app.models.complaint import Complaint
from app.models.restaurant import Restaurant, MenuItem
from app.models.order_item import OrderItem

from app.ai.rag.rag_chain import ask


def _find_order(db, order_number: str, user: dict):

    order = db.query(Order).filter(
        Order.order_number == order_number.strip().upper()
    ).first()

    if not order:
        return None

    if user["role"] == "admin":
        return order

    if user["role"] == "customer":
        customer = db.query(Customer).filter(
            Customer.user_id == user["id"]
        ).first()
        if customer and order.customer_id == customer.id:
            return order

    if user["role"] == "delivery_partner":
        partner = db.query(DeliveryPartner).filter(
            DeliveryPartner.user_id == user["id"]
        ).first()
        if partner and order.delivery_partner_id == partner.id:
            return order

    return None


def order_status_for(order_number: str, user: dict) -> str:

    if not user:
        return "Please log in to check an order."

    db = SessionLocal()

    try:
        order = _find_order(db, order_number, user)

        if not order:
            return "Order not found."

        return (
            f"Order {order.order_number}: "
            f"status {order.order_status.value}, "
            f"payment {order.payment_status.value}, "
            f"delivery fee Rs {order.delivery_charge}, "
            f"food total Rs {order.items_total}."
        )

    finally:
        db.close()


def order_tracking_for(order_number: str, user: dict) -> str:

    if not user:
        return "Please log in to check an order."

    db = SessionLocal()

    try:
        order = _find_order(db, order_number, user)

        if not order:
            return "Order not found."

        history = db.query(Tracking).filter(
            Tracking.order_id == order.id
        ).order_by(Tracking.created_at).all()

        if not history:
            return "No tracking history found."

        return "\n".join(
            f"{item.created_at:%d %b %Y %H:%M} - {item.status.value}"
            for item in history
        )

    finally:
        db.close()


@tool
def get_order_status(order_number: str) -> str:
    """Get the status and charges of an order using its order number."""
    return "Use order_status_for"


@tool
def get_order_tracking(order_number: str) -> str:
    """Get the full status history of an order using its order number."""
    return "Use order_tracking_for"


@tool
def search_policy(question: str) -> str:
    """Answer questions about delivery charges, refunds, rules, partner guidelines and FAQ."""
    return ask(question)


tools = [get_order_status, get_order_tracking, search_policy]