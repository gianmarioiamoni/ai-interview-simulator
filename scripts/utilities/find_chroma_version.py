# scripts/utilities/find_chroma_version.py

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

def find_chroma_version() -> str:

    chroma = Chroma(
        collection_name="interview_questions",
        embedding_function=OpenAIEmbeddings(),
        persist_directory="storage/chroma/interview_corpus",
    )

    return chroma.version