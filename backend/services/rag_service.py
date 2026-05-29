"""
RAG Service — Retrieval-Augmented Generation for SOC knowledge base.
Uses Qdrant and FastEmbed for lightweight, local vector search.
"""
import logging
from typing import List

from config import settings

logger = logging.getLogger(__name__)

# Try importing ML dependencies, but make them optional
try:
    from qdrant_client import QdrantClient
    from langchain_qdrant import QdrantVectorStore
    from fastembed import TextEmbedding
    RAG_DEPS_AVAILABLE = True
except ImportError:
    RAG_DEPS_AVAILABLE = False
    logger.info("RAG dependencies not installed (qdrant-client, fastembed) — RAG disabled")


from langchain_core.embeddings import Embeddings

class FastEmbeddingsWrapper(Embeddings):
    """Wrapper to make FastEmbed compatible with LangChain's Embeddings interface."""
    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        self.model = TextEmbedding(model_name=model_name)
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # FastEmbed returns a generator of numpy arrays, we need list of lists
        return [list(embedding) for embedding in self.model.embed(texts)]
        
    def embed_query(self, text: str) -> List[float]:
        return list(next(self.model.embed([text])))


class RAGService:
    def __init__(self):
        self._initialized = False
        self.client = None
        self.vector_store = None
        self.embeddings = None

        if not RAG_DEPS_AVAILABLE:
            logger.info("RAGService running in disabled mode (dependencies missing)")
            return

        try:
            # Connect to Qdrant Docker container, fallback to memory if unavailable
            try:
                self.client = QdrantClient(url="http://localhost:6333", timeout=2.0)
                # Verify connection
                self.client.get_collections()
                location = "http://localhost:6333"
                logger.info("Connected to Qdrant Docker container")
            except Exception:
                logger.warning("Qdrant Docker not reachable, falling back to local memory vector store")
                self.client = QdrantClient(":memory:")
                location = ":memory:"

            # FastEmbed is lightweight and uses ONNX, no PyTorch needed
            self.embeddings = FastEmbeddingsWrapper(model_name="BAAI/bge-small-en-v1.5")
            
            # Ensure collection exists
            from qdrant_client.http.models import Distance, VectorParams
            try:
                self.client.get_collection("soc_kb")
            except Exception:
                self.client.create_collection(
                    collection_name="soc_kb",
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
            
            self.vector_store = QdrantVectorStore(
                client=self.client,
                collection_name="soc_kb",
                embedding=self.embeddings,
            )
            self._initialized = True
            logger.info("RAGService initialized with Qdrant and FastEmbed")
        except Exception as e:
            logger.warning(f"RAGService init failed: {e} — RAG disabled")

    def add_documents(self, texts: List[str], metadatas: List[dict]):
        if not self._initialized:
            logger.warning("RAG not available — cannot add documents")
            return
        try:
            self.vector_store.add_texts(texts, metadatas=metadatas)
            logger.info(f"Added {len(texts)} documents to knowledge base.")
        except Exception as e:
            logger.error(f"Error adding documents to RAG: {e}")

    def search(self, query: str, k: int = 3) -> List[dict]:
        if not self._initialized:
            return []
        try:
            results = self.vector_store.similarity_search(query, k=k)
            return [{"text": doc.page_content, "metadata": doc.metadata} for doc in results]
        except Exception as e:
            logger.warning(f"RAG search error: {e}")
            return []

rag_service = RAGService()
