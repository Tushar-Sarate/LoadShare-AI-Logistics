from langchain_chroma import Chroma

from app.ai.rag.embeddings import embeddings
from app.ai.rag.document_loader import load_documents
from app.ai.rag.text_splitter import split_documents

CHROMA_DIR = "chroma_db"


def build_vectorstore():
    chunks = split_documents(load_documents())
    return Chroma.from_documents(
        chunks, embeddings, persist_directory=CHROMA_DIR
    )


def get_vectorstore():
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)


if __name__ == "__main__":
    build_vectorstore()
    print("Vector store built")