from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any
from app.models.pydantic_models import ChatSession, ChatMessage
from dotenv import load_dotenv

load_dotenv()


class AzureBlobService:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv(
            "AZURE_STORAGE_CONTAINER_NAME", "chatbot-sessions"
        )

        if not self.connection_string:
            raise ValueError(
                "AZURE_STORAGE_CONNECTION_STRING not found in environment variables"
            )

        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        self._ensure_container_exists()

    def _ensure_container_exists(self):
        """Ensure the container exists, create if it doesn't"""
        try:
            self.blob_service_client.get_container_client(
                self.container_name
            ).get_container_properties()
        except ResourceNotFoundError:
            self.blob_service_client.create_container(self.container_name)

    def save_chat_session(self, session: ChatSession) -> str:
        """Save chat session to Azure Blob Storage"""
        blob_name = f"{session.session_id}.json"
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )

        session_data = session.model_dump(mode="json")
        # Convert datetime objects to ISO format strings
        session_data["created_at"] = session.created_at.isoformat()
        session_data["updated_at"] = session.updated_at.isoformat()
        for message in session_data["messages"]:
            message["timestamp"] = (
                message["timestamp"]
                if isinstance(message["timestamp"], str)
                else message["timestamp"].isoformat()
            )

        blob_client.upload_blob(json.dumps(session_data, indent=2), overwrite=True)
        return blob_name

    def load_chat_session(self, session_id: str) -> ChatSession:
        """Load chat session from Azure Blob Storage"""
        blob_name = f"{session_id}.json"
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )

        try:
            blob_data = blob_client.download_blob().readall()
            session_data = json.loads(blob_data)

            # Convert ISO format strings back to datetime objects
            session_data["created_at"] = datetime.fromisoformat(
                session_data["created_at"]
            )
            session_data["updated_at"] = datetime.fromisoformat(
                session_data["updated_at"]
            )
            for message in session_data["messages"]:
                message["timestamp"] = datetime.fromisoformat(message["timestamp"])

            return ChatSession(**session_data)
        except ResourceNotFoundError:
            raise FileNotFoundError(f"Chat session {session_id} not found")

    def list_user_sessions(self, customer_email: str) -> List[str]:
        """List all session IDs for a specific user"""
        blob_list = self.blob_service_client.get_container_client(
            self.container_name
        ).list_blobs()
        user_sessions = []

        for blob in blob_list:
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name, blob=blob.name
                )
                blob_data = blob_client.download_blob().readall()
                session_data = json.loads(blob_data)

                if session_data.get("customer_email") == customer_email:
                    user_sessions.append(session_data.get("session_id"))
            except:
                continue

        return user_sessions

    def delete_chat_session(self, session_id: str):
        """Delete a chat session from Azure Blob Storage"""
        blob_name = f"{session_id}.json"
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )
        blob_client.delete_blob()


class LocalChatStorage:
    """Fallback local storage for chat sessions"""

    def __init__(self, storage_dir: str = "chat_sessions"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def save_chat_session(self, session: ChatSession) -> str:
        """Save chat session locally"""
        file_path = os.path.join(self.storage_dir, f"{session.session_id}.json")

        session_data = session.model_dump(mode="json")
        # Convert datetime objects to ISO format strings
        session_data["created_at"] = session.created_at.isoformat()
        session_data["updated_at"] = session.updated_at.isoformat()
        for message in session_data["messages"]:
            message["timestamp"] = (
                message["timestamp"]
                if isinstance(message["timestamp"], str)
                else message["timestamp"].isoformat()
            )

        with open(file_path, "w") as f:
            json.dump(session_data, f, indent=2)
        return file_path

    def load_chat_session(self, session_id: str) -> ChatSession:
        """Load chat session from local storage"""
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Chat session {session_id} not found")

        with open(file_path, "r") as f:
            session_data = json.load(f)

        # Convert ISO format strings back to datetime objects
        session_data["created_at"] = datetime.fromisoformat(session_data["created_at"])
        session_data["updated_at"] = datetime.fromisoformat(session_data["updated_at"])
        for message in session_data["messages"]:
            message["timestamp"] = datetime.fromisoformat(message["timestamp"])

        return ChatSession(**session_data)

    def list_user_sessions(self, customer_email: str) -> List[str]:
        """List all session IDs for a specific user"""
        user_sessions = []

        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.storage_dir, filename), "r") as f:
                        session_data = json.load(f)

                    if session_data.get("customer_email") == customer_email:
                        user_sessions.append(session_data.get("session_id"))
                except:
                    continue

        return user_sessions


# Try to use Azure Blob Storage, fall back to local storage
try:
    chat_storage = AzureBlobService()
    print("Using Azure Blob Storage for chat sessions")
except:
    chat_storage = LocalChatStorage()
    print("Using local storage for chat sessions")
