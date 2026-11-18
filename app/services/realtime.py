import asyncio

from app.services.email_service import email_order_update

_subscribers = []   # list of dicts: user_id, role, queue
_loop = None


def subscribe(user_id: int, role: str) -> asyncio.Queue:
    """Called from the async stream endpoint."""
    global _loop
    _loop = asyncio.get_running_loop()
    queue = asyncio.Queue(maxsize=100)
    _subscribers.append({"user_id": user_id, "role": role, "queue": queue})
    return queue


def unsubscribe(queue: asyncio.Queue) -> None:
    for sub in list(_subscribers):
        if sub["queue"] is queue:
            _subscribers.remove(sub)


def _put(queue, event):
    try:
        queue.put_nowait(event)
    except asyncio.QueueFull:
        pass


def publish(user_ids: set, roles: set, event: dict) -> None:
    """Safe to call from normal (sync) route functions."""
    if _loop is None:
        return
    for sub in list(_subscribers):
        if sub["user_id"] in user_ids or sub["role"] in roles:
            _loop.call_soon_threadsafe(_put, sub["queue"], event)


def notify_order(order, kind: str = "order_update") -> None:
    """Tell the customer, the partner and all admins that an order changed,
    and email the customer when the status changes."""
    ids = set()

    if order.customer is not None:
        ids.add(order.customer.user_id)
    if order.delivery_partner is not None:
        ids.add(order.delivery_partner.user_id)

    status = getattr(order.order_status, "value", order.order_status)

    publish(ids, {"admin"}, {
        "type": kind,
        "order_id": order.id,
        "status": status,
    })

    email_order_update(order)