"""Azure Blob Storage service for storing conversation files."""

import os
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import AzureError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AzureBlobStorageService:
    """Service for handling Azure Blob Storage operations."""
    
    def __init__(self):
        """Initialize Azure Blob Storage client."""
        self.connection_string = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_BLOB_STORAGE_CONTAINER_NAME", "contoso")
        
        if not self.connection_string:
            raise ValueError("AZURE_BLOB_STORAGE_CONNECTION_STRING environment variable is not set")
        
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            self._ensure_container_exists()
        except Exception as e:
            print(f"Failed to initialize Azure Blob Storage client: {e}")
            raise
    
    def _ensure_container_exists(self):
        """Ensure the container exists, create if it doesn't."""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
                print(f"Created container: {self.container_name}")
        except Exception as e:
            print(f"Error ensuring container exists: {e}")
            # Don't raise here as container might already exist
    
    def upload_conversation_file(self, session_id: str, conversation_data: Dict[str, Any]) -> Optional[str]:
        """
        Upload conversation data as JSON file to Azure Blob Storage.
        
        Args:
            session_id: The session ID for the conversation
            conversation_data: The conversation data to store
            
        Returns:
            The complete downloadable blob URL if successful, None if failed
        """
        try:
            # Create file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"session_{session_id}_{timestamp}.json"
            blob_path = f"yodhaassistant/documents/sessions/{file_name}"
            
            # Convert data to JSON string
            json_data = json.dumps(conversation_data, indent=2, ensure_ascii=False, default=str)
            
            # Upload to blob storage
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_path
            )
            
            blob_client.upload_blob(json_data, overwrite=True, content_type="application/json")
            
            # Generate the complete downloadable URL
            complete_url = blob_client.url
            
            print(f"Successfully uploaded conversation to: {blob_path}")
            print(f"Complete downloadable URL: {complete_url}")
            return complete_url
            
        except AzureError as e:
            print(f"Azure error uploading conversation: {e}")
            traceback.print_exc()
            return None
        except Exception as e:
            print(f"Error uploading conversation: {e}")
            traceback.print_exc()
            return None
    
    def generate_conversation_data(self, session, customer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate conversation data structure for storage.
        
        Args:
            session: The customer session object
            customer_id: Optional customer ID if available
            
        Returns:
            Dictionary containing conversation data
        """
        try:
            # Create conversation export data
            export_data = {
                "export_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "company_name": os.getenv("COMPANY_NAME", "Contoso"),
                    "session_id": getattr(session, 'session_id', 'unknown'),
                    "total_messages": len(getattr(session, 'messages', [])),
                    "app_version": "1.0",
                    "export_format": "customer_service_chat_azure",
                    "storage_type": "azure_blob"
                },
                "session_info": {
                    "customer_id": customer_id or getattr(session, 'customer_id', None),
                    "customer_state": getattr(session, 'customer_state', {}).value if hasattr(getattr(session, 'customer_state', {}), 'value') else 'unknown',
                    "customer_info": getattr(session, 'customer_info', {}),
                    "recent_purchases": getattr(session, 'recent_purchases', []),
                    "session_start_time": getattr(session, 'start_time', datetime.now().isoformat()),
                    "session_end_time": datetime.now().isoformat()
                },
                "conversation": []
            }
            
            # Add messages to export
            messages = getattr(session, 'messages', [])
            for i, message in enumerate(messages):
                message_data = {
                    "message_id": i + 1,
                    "timestamp": getattr(message, 'timestamp', datetime.now().isoformat()),
                    "role": getattr(message, 'role', 'unknown'),
                    "content": getattr(message, 'content', ''),
                    "metadata": {
                        "message_type": getattr(message, 'type', 'text'),
                        "has_debug_info": hasattr(message, 'debug_info') and message.debug_info is not None
                    }
                }
                export_data["conversation"].append(message_data)
            
            return export_data
            
        except Exception as e:
            print(f"Error generating conversation data: {e}")
            traceback.print_exc()
            return {
                "export_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "error": f"Failed to generate conversation data: {str(e)}"
                },
                "conversation": []
            }


def test_azure_connection():
    """Test Azure Blob Storage connection."""
    try:
        service = AzureBlobStorageService()
        print("✅ Azure Blob Storage connection successful")
        return True
    except Exception as e:
        print(f"❌ Azure Blob Storage connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test the Azure connection
    test_azure_connection()
