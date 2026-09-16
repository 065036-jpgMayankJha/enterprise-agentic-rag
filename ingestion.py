from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
import qdrant_client

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

client = qdrant_client.QdrantClient(host="localhost", port=6333)
vector_store = QdrantVectorStore(client=client, collection_name="dept_docs")
storage_context = StorageContext.from_defaults(vector_store=vector_store)

documents = SimpleDirectoryReader(
    "data/processed", recursive=True, required_exts=[".md"]
).load_data()

for doc in documents:
    parts = doc.metadata["file_path"].split("/")
    dept_index = parts.index("processed") + 1
    doc.metadata["department"] = parts[dept_index]

index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

print(f"Ingested {len(documents)} document(s) into Qdrant.")
for doc in documents:
    print(f"  - {doc.metadata['department']}: {doc.metadata['file_name']}")
