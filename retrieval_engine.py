from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
import qdrant_client

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.llm = Ollama(model="smollm2:135m", request_timeout=180.0)

_client = qdrant_client.QdrantClient(host="localhost", port=6333)
_vector_store = QdrantVectorStore(client=_client, collection_name="dept_docs")
_index = VectorStoreIndex.from_vector_store(_vector_store)


def query_documents(question: str, department: str = None) -> dict:
    """
    Query the RAG engine, optionally scoped to one department.

    Args:
        question: the user's question
        department: one of HR, Finance, Legal, Customer, or None for all

    Returns:
        dict with 'answer', 'sources' (filenames), 'raw_chunks' (actual retrieved text), 'department'
    """
    if department:
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key="department", value=department)]
        )
        engine = _index.as_query_engine(filters=filters)
    else:
        engine = _index.as_query_engine()

    response = engine.query(question)

    sources = list({
        node.metadata.get("file_name", "unknown")
        for node in response.source_nodes
    })

    raw_chunks = [
        {
            "file_name": node.metadata.get("file_name", "unknown"),
            "text": node.get_text(),
            "score": round(node.score, 3) if node.score else None,
        }
        for node in response.source_nodes
    ]

    return {
        "answer": str(response),
        "sources": sources,
        "raw_chunks": raw_chunks,
        "department": department or "all",
    }


if __name__ == "__main__":
    import json
    result = query_documents("What is the leave policy?", department="HR")
    print(json.dumps(result, indent=2))
