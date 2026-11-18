import logging

logger = logging.getLogger("notifications")


def send_notification(user_id: int, message: str):
    # Placeholder: logs the message. Email/SMS can be added here later.
    logger.info(f"Notification to user {user_id}: {message}")