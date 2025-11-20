"""Sentence Transformer embeddings wrapper for LangChain"""
from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
from typing import List
import os


class SentenceTransformerEmbeddings(Embeddings):
    """LangChain-compatible wrapper for Sentence Transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize Sentence Transformer embeddings
        
        Args:
            model_name: HuggingFace model name
                - "all-MiniLM-L6-v2" (fast, 384 dim, good quality) - DEFAULT
                - "all-mpnet-base-v2" (slower, 768 dim, better quality)
                - "sentence-transformers/all-MiniLM-L6-v2" (explicit)
        """
        print(f"[INFO] Loading Sentence Transformer model: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            print(f"[SUCCESS] Model loaded: {model_name}")
        except Exception as e:
            print(f"[ERROR] Failed to load model {model_name}: {e}")
            # Fallback to default
            print("[INFO] Falling back to default model: all-MiniLM-L6-v2")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.model_name = "all-MiniLM-L6-v2"
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents"""
        if not texts:
            return []
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query"""
        if not text:
            return [0.0] * 384  # Default dimension for all-MiniLM-L6-v2
        embedding = self.model.encode([text], show_progress_bar=False, convert_to_numpy=True)
        return embedding[0].tolist()

