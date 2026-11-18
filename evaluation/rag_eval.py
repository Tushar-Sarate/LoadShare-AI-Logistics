import re
import time

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.ai.rag.embeddings import embeddings
from app.ai.rag.document_loader import load_documents
from app.ai.rag.rag_chain import ask
from app.ai.langchain.chains import intent_chain

# (question, keywords: the answer is correct if ANY keyword appears)
CASES = [
    ("How is the delivery fee calculated for food orders?", ["rs 20"]),
    ("How much is charged for each extra km after 2 km?", ["rs 7"]),
    ("What is the maximum package weight?", ["50 kg"]),
        ("How is the parcel delivery charge calculated?", ["rs 30"]),
    ("Can I cancel a delivered order?", ["cannot", "can't", "can not"]),
    ("How long does a refund take?", ["5 to 7", "5-7"]),
    ("Which payment methods are accepted?", ["upi"]),
    ("Do COD orders get a refund?", [
        "no refund", "not refund", "not eligible", "not given",
        "no payment", "not receive", "do not receive",
    ]),
    ("When can a customer cancel an order?", ["pending"]),
    ("What are the order statuses?", ["in transit"]),
    ("What happens if no partner is available?", ["pending"]),
    ("Which items are prohibited?", ["explosives"]),
    ("When does a partner become available again?", ["delivered"]),
    ("Can a partner have more than one active order?", ["only one", "one active"]),
    ("What should a partner do if the address is wrong?", ["contact support"]),
    ("What are the complaint statuses?", ["resolved"]),
    ("What happens after repeated complaints about a partner?", ["deactivated"]),
    ("Can a partner ask the customer for extra money?", ["not ask", "must not", "extra money"]),
    ("How do I become a delivery partner?", ["delivery_partner", "delivery partner"]),
    ("Are UPI payments marked paid immediately?", ["paid"]),
]

OUT_OF_SCOPE = [
    "Who is the prime minister of India?",
    "What is the capital of France?",
    "Write me a poem about cricket.",
]

REFUSAL_PHRASES = ["don't know", "do not know", "not in", "cannot", "can't", "only help"]

INTENT_CASES = [
    ("How long does a refund take?", "policy"),
    ("What is the maximum weight allowed?", "policy"),
    ("Where is my order LS-ABC1234567?", "order"),
    ("What is the status of order LS-ABC1234567?", "order"),
    ("My package arrived damaged", "complaint"),
    ("The delivery partner was rude", "complaint"),
    ("Hello, how are you?", "other"),
    ("Tell me a joke", "other"),
]


def clean(text):
    text = text.lower()
    text = text.replace("*", "").replace("₹", "rs ").replace("rs.", "rs")
    text = text.replace("–", "-").replace("‑", "-").replace("’", "'")
    return re.sub(r"\s+", " ", text)


def hit(text, keywords):
    text = clean(text)
    return any(k in text for k in keywords)


def retrieval_hit_rate(chunk_size, overlap, k=4):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap
    )
    chunks = splitter.split_documents(load_documents())

    store = Chroma.from_documents(
        chunks, embeddings, collection_name=f"eval_{chunk_size}"
    )
    retriever = store.as_retriever(search_kwargs={"k": k})

    hits = 0
    for question, keywords in CASES:
        docs = retriever.invoke(question)
        if hit(" ".join(d.page_content for d in docs), keywords):
            hits += 1

    return len(chunks), hits / len(CASES)


def main():
    print("\n=== 1. Retrieval hit rate by chunk size (top-4) ===")
    for size, overlap in [(400, 50), (800, 100), (1200, 150)]:
        n, rate = retrieval_hit_rate(size, overlap)
        print(f"chunk_size={size:<5} chunks={n:<3} hit_rate={rate:.0%}")

    print("\n=== 2. Answer accuracy ===")
    correct = 0
    for question, keywords in CASES:
        answer = ask(question)
        ok = hit(answer, keywords)
        correct += ok
        print(("PASS  " if ok else "FAIL  ") + question)
        if not ok:
            print("      ANSWER:", answer.replace("\n", " ")[:250])
        time.sleep(1)
    print(f"Answer accuracy: {correct}/{len(CASES)} = {correct / len(CASES):.0%}")

    print("\n=== 3. Out-of-scope check (should refuse) ===")
    refused = 0
    for question in OUT_OF_SCOPE:
        answer = ask(question)
        ok = hit(answer, REFUSAL_PHRASES)
        refused += ok
        print(("PASS  " if ok else "FAIL  ") + question)
        if not ok:
            print("      ANSWER:", answer.replace("\n", " ")[:250])
        time.sleep(1)
    print(f"Refused out-of-scope: {refused}/{len(OUT_OF_SCOPE)}")

    print("\n=== 4. Intent routing accuracy ===")
    right = 0
    for question, expected in INTENT_CASES:
        got = intent_chain.invoke({"question": question}).strip().lower()
        ok = got == expected
        right += ok
        print(("PASS  " if ok else "FAIL  ") + f"{question} -> {got} (expected {expected})")
        time.sleep(1)
    print(f"Intent accuracy: {right}/{len(INTENT_CASES)} = {right / len(INTENT_CASES):.0%}")


if __name__ == "__main__":
    main()