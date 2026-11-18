import json
import logging
import time
from pathlib import Path

Path("logs").mkdir(exist_ok=True)

logger = logging.getLogger("chatbot")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler("logs/chatbot.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


def log_chat(user, question, intent, answer, start, blocked=False, error=False):
    logger.info(json.dumps({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user["id"] if user else None,
        "role": user["role"] if user else None,
        "question": question,
        "intent": intent,
        "blocked": blocked,
        "error": error,
        "latency_ms": round((time.perf_counter() - start) * 1000),
        "answer_chars": len(answer),
    }))