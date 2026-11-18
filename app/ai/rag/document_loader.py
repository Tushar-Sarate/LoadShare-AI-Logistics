from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader

DOCS_DIR = Path("documents")


def load_documents():
    docs = []
    for file in DOCS_DIR.iterdir():
        if file.suffix == ".pdf":
            docs.extend(PyPDFLoader(str(file)).load())
        elif file.suffix == ".txt":
            docs.extend(TextLoader(str(file), encoding="utf-8").load())
    return docs