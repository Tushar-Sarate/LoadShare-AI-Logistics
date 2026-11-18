from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.ai.llm import llm
from app.ai.rag.retriever import get_retriever

prompt = ChatPromptTemplate.from_template(
    """You are the support assistant for LoadShare AI Logistics.
Answer only from the context below. If the answer is not there, say you don't know.
Reply in plain text without markdown, bullets or stars.

Context:
{context}

Question: {question}"""
)


def ask(question: str) -> str:
    docs = get_retriever().invoke(question)
    context = "\n\n".join(d.page_content for d in docs)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"context": context, "question": question})