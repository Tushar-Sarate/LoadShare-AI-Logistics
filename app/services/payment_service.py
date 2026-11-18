from app.models.order import PaymentStatus


def get_payment_status(method: str) -> PaymentStatus:
    # Cash on delivery stays pending until delivery
    if method == "COD":
        return PaymentStatus.pending
    return PaymentStatus.paid