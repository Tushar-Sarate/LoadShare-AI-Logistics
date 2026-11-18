from app.ai.langchain.chains import intent_chain, general_chain
from app.ai.rag.rag_chain import ask
from app.ai.langchain.chatbot import chat
from app.ai.langgraph.state import ChatState


def classify_node(state: ChatState) -> dict:
    intent = intent_chain.invoke({"question": state["question"]}).strip().lower()

    if intent not in {"policy", "order", "complaint", "other"}:
        intent = "other"

    return {"intent": intent}


def policy_node(state: ChatState) -> dict:
    return {"answer": ask(state["question"])}


def order_node(state: ChatState) -> dict:
    return {"answer": chat(state["question"], state.get("user"))}


def complaint_node(state: ChatState) -> dict:
    return {
        "answer": (
            "I'm sorry about the problem. Please raise a complaint from the "
            "Complaints section with your order number and a short description. "
            "Our admin team will review it."
        )
    }


def general_node(state: ChatState) -> dict:
    return {"answer": general_chain.invoke({"question": state["question"]})}