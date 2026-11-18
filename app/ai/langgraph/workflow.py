import time

from langgraph.graph import StateGraph, START, END

from app.ai.guardrails import check_input
from app.ai.observability import log_chat
from app.ai.langgraph.state import ChatState
from app.ai.langgraph.nodes import (
    classify_node,
    policy_node,
    order_node,
    complaint_node,
    general_node,
)
from app.ai.langgraph.edges import route_by_intent


graph = StateGraph(ChatState)

graph.add_node("classify", classify_node)
graph.add_node("policy", policy_node)
graph.add_node("order", order_node)
graph.add_node("complaint", complaint_node)
graph.add_node("general", general_node)

graph.add_edge(START, "classify")

graph.add_conditional_edges(
    "classify",
    route_by_intent,
    {
        "policy": "policy",
        "order": "order",
        "complaint": "complaint",
        "general": "general",
    },
)

graph.add_edge("policy", END)
graph.add_edge("order", END)
graph.add_edge("complaint", END)
graph.add_edge("general", END)

workflow = graph.compile()


def run_workflow(question: str, user: dict = None) -> str:
    start = time.perf_counter()

    # Guardrail: block unsafe input before it reaches the LLM
    refusal = check_input(question)
    if refusal:
        log_chat(user, question, "blocked", refusal, start, blocked=True)
        return refusal

    try:
        result = workflow.invoke({
            "question": question,
            "intent": "",
            "answer": "",
            "user": user,
        })
    except Exception as e:
        log_chat(user, question, "error", str(e), start, error=True)
        return "Sorry, something went wrong. Please try again."

    log_chat(user, question, result["intent"], result["answer"], start)
    return result["answer"]