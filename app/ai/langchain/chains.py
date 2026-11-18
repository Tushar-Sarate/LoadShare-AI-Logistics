from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.ai.llm import llm
from app.ai.prompts import INTENT_PROMPT, SYSTEM_PROMPT


# Chain 1: classify the user message (policy / order / complaint / other)
intent_chain = (
    ChatPromptTemplate.from_template(INTENT_PROMPT)
    | llm
    | StrOutputParser()
)


# Chain 2: general reply for other questions
general_chain = (
    ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}"),
    ])
    | llm
    | StrOutputParser()
)