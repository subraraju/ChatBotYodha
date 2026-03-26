"""
Conversation storage — Azure Blob primary, local filesystem fallback.

Stores the full JSON of a chat session on close so it can be reviewed later.

Usage:
    from app.services.storage_service import storage_service
    url = await storage_service.save_session(session_id, data_dict)
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

# Optional dep
try:
    from azure.storage.blob import BlobServiceClient
except ImportError:
    BlobServiceClient = None  # type: ignore


LOCAL_DIR = Path("data/chat_sessions")


# ── Interface ─────────────────────────────────────────────────────────

class StorageService:
    """Save / load conversation JSON blobs."""

    def __init__(self) -> None:
        self._blob_client = None
        self._container = settings.AZURE_STORAGE_CONTAINER_NAME or "chatbot-sessions"

        conn_str = settings.AZURE_STORAGE_CONNECTION_STRING
        if conn_str and BlobServiceClient:
            try:
                self._blob_client = BlobServiceClient.from_connection_string(conn_str)
                self._ensure_container()
                logger.info("Azure Blob storage initialised (container=%s)", self._container)
            except Exception as exc:
                logger.warning("Azure Blob init failed — using local: %s", exc)
                self._blob_client = None

    @property
    def backend(self) -> str:
        return "azure" if self._blob_client else "local"

    # ── Save ──────────────────────────────────────────────────────────

    async def save_session(
        self,
        session_id: str,
        data: Dict[str, Any],
    ) -> Optional[str]:
        """
        Persist session dict as JSON.
        Returns URL (Azure) or file path (local), or None on failure.
        """
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        blob_name = f"sessions/session_{session_id}_{ts}.json"
        payload = json.dumps(data, default=str, indent=2)

        if self._blob_client:
            return self._upload_blob(blob_name, payload)
        return self._save_local(blob_name, payload)

    # ── Load ──────────────────────────────────────────────────────────

    async def load_session(self, blob_name: str) -> Optional[Dict]:
        """Load a previously saved session — blob name or local path."""
        if self._blob_client:
            return self._download_blob(blob_name)
        return self._load_local(blob_name)

    # ── Azure helpers ─────────────────────────────────────────────────

    def _ensure_container(self) -> None:
        try:
            self._blob_client.create_container(self._container)
        except Exception:
            pass  # already exists

    def _upload_blob(self, name: str, payload: str) -> Optional[str]:
        try:
            blob = self._blob_client.get_blob_client(self._container, name)
            blob.upload_blob(payload, overwrite=True)
            url = blob.url
            logger.info("Uploaded blob %s", name)
            return url
        except Exception as exc:
            logger.error("Blob upload failed: %s", exc)
            return None

    def _download_blob(self, name: str) -> Optional[Dict]:
        try:
            blob = self._blob_client.get_blob_client(self._container, name)
            raw = blob.download_blob().readall()
            return json.loads(raw)
        except Exception as exc:
            logger.error("Blob download failed: %s", exc)
            return None

    # ── Local helpers ─────────────────────────────────────────────────

    def _save_local(self, name: str, payload: str) -> Optional[str]:
        path = LOCAL_DIR / name
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(payload, encoding="utf-8")
            logger.info("Saved session locally: %s", path)
            return str(path)
        except Exception as exc:
            logger.error("Local save failed: %s", exc)
            return None

    def _load_local(self, name: str) -> Optional[Dict]:
        path = LOCAL_DIR / name
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error("Local load failed: %s", exc)
            return None


# ── Singleton ─────────────────────────────────────────────────────────

storage_service = StorageService()
