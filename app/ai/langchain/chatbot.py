from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from app.ai.llm import llm
from app.ai.prompts import SYSTEM_PROMPT
from app.ai.rag.rag_chain import ask
from app.ai.tools import tools, order_status_for, order_tracking_for

llm_with_tools = llm.bind_tools(tools)


def run_tool(name: str, args: dict, user: dict) -> str:
    # The user comes from the login token, never from the LLM
    if name == "get_order_status":
        return order_status_for(args.get("order_number", ""), user)
    if name == "get_order_tracking":
        return order_tracking_for(args.get("order_number", ""), user)
    if name == "search_policy":
        return ask(args.get("question", ""))
    return "Unknown tool."


def chat(question: str, user: dict = None) -> str:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=question),
    ]

    response = llm_with_tools.invoke(messages)

    if not response.tool_calls:
        return response.content

    messages.append(response)

    for call in response.tool_calls:
        result = run_tool(call["name"], call["args"], user)
        messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

    final = llm_with_tools.invoke(messages)
    return final.content