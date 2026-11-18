from app.ai.langgraph.state import ChatState


# Decide which node runs after classify_node
def route_by_intent(state: ChatState) -> str:
    intent = state["intent"]

    if intent == "policy":
        return "policy"
    if intent == "order":
        return "order"
    if intent == "complaint":
        return "complaint"
    return "general"