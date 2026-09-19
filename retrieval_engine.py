import os
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
import qdrant_client

Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")

_client = qdrant_client.QdrantClient(
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key=os.getenv("QDRANT_API_KEY") or None,
)
_vector_store = QdrantVectorStore(client=_client, collection_name="dept_docs")
_index = VectorStoreIndex.from_vector_store(_vector_store)


def query_documents(question: str, department: str = None) -> dict:
    """
    Retrieve raw document chunks relevant to a question, optionally scoped to one department.
    No local LLM synthesis — retrieval only. Synthesis happens downstream in the CrewAI agent.

    Args:
        question: the user's question
        department: one of HR, Finance, Legal, Customer, or None for all

    Returns:
        dict with 'sources' (filenames), 'raw_chunks' (retrieved text + score), 'department'
    """
    if department:
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key="department", value=department)]
        )
        retriever = _index.as_retriever(filters=filters)
    else:
        retriever = _index.as_retriever()

    nodes = retriever.retrieve(question)

    sources = list({
        node.metadata.get("file_name", "unknown")
        for node in nodes
    })

    raw_chunks = [
        {
            "file_name": node.metadata.get("file_name", "unknown"),
            "text": node.get_text(),
            "score": round(node.score, 3) if node.score else None,
        }
        for node in nodes
    ]

    return {
        "sources": sources,
        "raw_chunks": raw_chunks,
        "department": department or "all",
    }


if __name__ == "__main__":
    import json
    result = query_documents("What is the leave policy?", department="HR")
    print(json.dumps(result, indent=2))
