"""
FAISS-based document embedding + vector search for product documentation.

On first use it loads a pre-built FAISS index from  data/index/.
Admin can rebuild the index by uploading PDFs via the /admin/upload-docs endpoint.

Usage:
    from app.services.embedding_service import embedding_service
    results = embedding_service.search("warranty policy for widget X", top_k=5)
"""

import json
import logging
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

try:
    import faiss
except ImportError:
    faiss = None  # type: ignore
    logger.warning("faiss-cpu not installed — vector search disabled")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore
    logger.warning("sentence-transformers not installed — embedding disabled")


INDEX_DIR = Path(settings.EMBEDDING_INDEX_DIR)
FAISS_FILE = INDEX_DIR / "faiss_vector_store.index"
META_FILE = INDEX_DIR / "faiss_vector_store.pkl"


class EmbeddingService:
    """Wraps a SentenceTransformer model + FAISS index.  Lazy-loads on first use."""

    def __init__(self) -> None:
        self._model: Optional[Any] = None
        self._index: Optional[Any] = None
        self._metadata: List[Dict[str, Any]] = []
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Lazy-load model + index on first real use."""
        if self._initialized:
            return
        self._initialized = True

        if SentenceTransformer is None or faiss is None:
            logger.info("Embedding service disabled (missing deps)")
            return

        # Load model
        try:
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Loaded embedding model: %s", settings.EMBEDDING_MODEL)
        except Exception as exc:
            logger.warning("Primary embedding model failed (%s), trying fallback", exc)
            try:
                self._model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                logger.error("No embedding model available")

        # Load index
        self._load_index()

    # ── public --------------------------------------------------------

    @property
    def ready(self) -> bool:
        self._ensure_initialized()
        return self._model is not None and self._index is not None

    def search(
        self, query: str, top_k: int = 5, return_debug: bool = False
    ) -> List[Dict[str, Any]]:
        """Return top-k chunks matching *query*."""
        self._ensure_initialized()
        if not self.ready:
            return []

        vec = self._model.encode([query])
        distances, indices = self._index.search(np.array(vec, dtype="float32"), top_k)

        results: List[Dict[str, Any]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue
            meta = self._metadata[idx]
            entry: Dict[str, Any] = {
                "text": meta.get("text", ""),
                "source": meta.get("source", ""),
                "product_name": meta.get("product_name", ""),
                "score": float(dist),
            }
            if return_debug:
                entry["metadata"] = meta
            results.append(entry)
        return results

    def rebuild_index(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Build a new FAISS index from *chunks*.
        Each chunk: {"text": str, "source": str, "product_name": str, ...}.
        Returns number of vectors indexed.
        """
        if self._model is None or faiss is None:
            raise RuntimeError("embedding model not available")
        self._ensure_initialized()

        texts = [c["text"] for c in chunks]
        vecs = self._model.encode(texts, show_progress_bar=True)
        vecs = np.array(vecs, dtype="float32")

        dim = vecs.shape[1]
        idx = faiss.IndexFlatL2(dim)
        idx.add(vecs)

        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(idx, str(FAISS_FILE))
        with open(META_FILE, "wb") as f:
            pickle.dump(chunks, f)

        self._index = idx
        self._metadata = chunks
        logger.info("Rebuilt FAISS index: %d vectors, dim=%d", idx.ntotal, dim)
        return idx.ntotal

    # ── private -------------------------------------------------------

    def _load_index(self) -> None:
        if not FAISS_FILE.exists() or not META_FILE.exists():
            logger.info("No pre-built FAISS index found at %s", INDEX_DIR)
            return
        try:
            self._index = faiss.read_index(str(FAISS_FILE))
            with open(META_FILE, "rb") as f:
                self._metadata = pickle.load(f)
            logger.info(
                "Loaded FAISS index: %d vectors, %d metadata entries",
                self._index.ntotal,
                len(self._metadata),
            )
        except Exception as exc:
            logger.error("Failed to load FAISS index: %s", exc)


# ── Singleton ─────────────────────────────────────────────────────────

embedding_service = EmbeddingService()
