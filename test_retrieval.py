from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
import qdrant_client

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.llm = Ollama(model="smollm2:135m", request_timeout=180.0)

client = qdrant_client.QdrantClient(host="localhost", port=6333)
vector_store = QdrantVectorStore(client=client, collection_name="dept_docs")
index = VectorStoreIndex.from_vector_store(vector_store)

query = "What is the leave policy?"

engine = index.as_query_engine()
response = engine.query(query)
print("UNFILTERED:")
print(response)
print()

filters = MetadataFilters(filters=[ExactMatchFilter(key="department", value="HR")])
engine_hr = index.as_query_engine(filters=filters)
response_hr = engine_hr.query(query)
print("FILTERED (HR only):")
print(response_hr)
