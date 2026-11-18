from typing import Optional, TypedDict


class ChatState(TypedDict):
    question: str
    intent: str
    answer: str
    user: Optional[dict]