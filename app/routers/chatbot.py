from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.models.user import User
from app.security.dependencies import get_current_user
from app.ai.langgraph.workflow import run_workflow


router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"]
)


class ChatRequest(BaseModel):

    question: str = Field(min_length=2, max_length=500)


class ChatResponse(BaseModel):

    answer: str


@router.post(
    "/",
    response_model=ChatResponse
)
def ask_chatbot(
    data: ChatRequest,
    current_user: User = Depends(get_current_user)
):

    answer = run_workflow(
        data.question,
        {"id": current_user.id, "role": current_user.role}
    )

    return {"answer": answer}