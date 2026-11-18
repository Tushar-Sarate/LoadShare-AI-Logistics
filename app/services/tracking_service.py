from sqlalchemy.orm import Session
from app.models.tracking import Tracking


def add_tracking(db: Session, order, status, user_id=None, note=None):
    db.add(Tracking(order_id=order.id, status=status, updated_by=user_id, note=note))