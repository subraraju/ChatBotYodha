"""
Admin endpoints — PDF upload for FAISS re-indexing, config info.
"""

import logging
import os
import tempfile
from typing import List

from fastapi import APIRouter, UploadFile, File

from app.config import settings
from app.schemas import DocUploadResponse, ConfigResponse
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/config", response_model=ConfigResponse)
def get_config():
    return ConfigResponse(
        company_name=settings.COMPANY_NAME,
        llm_provider=settings.LLM_PROVIDER,
        embedding_model=settings.EMBEDDING_MODEL,
        storage_backend="azure" if settings.AZURE_STORAGE_CONNECTION_STRING else "local",
    )


@router.post("/upload-docs", response_model=DocUploadResponse)
async def upload_docs(files: List[UploadFile] = File(...)):
    """
    Accept PDF / TXT files, extract text, chunk, and rebuild the FAISS index.
    """
    if not embedding_service.ready:
        return DocUploadResponse(
            success=False,
            message="Embedding service not available (missing deps or model).",
        )

    chunks: list = []
    processed = 0

    for f in files:
        raw = await f.read()
        filename = f.filename or "unknown"
        ext = os.path.splitext(filename)[1].lower()

        try:
            if ext == ".pdf":
                text = _extract_pdf(raw)
            elif ext in (".txt", ".md"):
                text = raw.decode("utf-8", errors="replace")
            else:
                logger.warning("Skipping unsupported file type: %s", filename)
                continue

            file_chunks = _chunk_text(text, filename)
            chunks.extend(file_chunks)
            processed += 1
            logger.info("Processed %s → %d chunks", filename, len(file_chunks))

        except Exception as exc:
            logger.error("Failed to process %s: %s", filename, exc)

    if not chunks:
        return DocUploadResponse(
            success=False, message="No valid documents found.", files_processed=0
        )

    total = embedding_service.rebuild_index(chunks)
    return DocUploadResponse(
        success=True,
        message=f"Indexed {total} chunks from {processed} file(s).",
        files_processed=processed,
        total_chunks=total,
    )


# ── Helpers ───────────────────────────────────────────────────────────

def _extract_pdf(raw_bytes: bytes) -> str:
    """Extract text from a PDF using PyPDF2 (or pymupdf if available)."""
    try:
        import fitz  # pymupdf

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(raw_bytes)
            tmp.flush()
            doc = fitz.open(tmp.name)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            os.unlink(tmp.name)
            return text
    except ImportError:
        pass

    try:
        from PyPDF2 import PdfReader
        import io

        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except ImportError:
        raise RuntimeError("Install pymupdf or PyPDF2 to process PDFs")


def _chunk_text(
    text: str, source: str, chunk_size: int = 500, overlap: int = 50
) -> List[dict]:
    """Split *text* into overlapping chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunk_text = " ".join(chunk_words)
        if chunk_text.strip():
            product_name = os.path.splitext(os.path.basename(source))[0]
            chunks.append(
                {
                    "text": chunk_text,
                    "source": source,
                    "product_name": product_name,
                    "chunk_index": len(chunks),
                }
            )
        i += chunk_size - overlap
    return chunks
