"""
Temporary Firebase service that uses HTTP requests for read operations
This bypasses authentication issues while maintaining the same interface
"""

import requests
import json
from typing import Dict, Any

class TemporaryFirebaseService:
    def __init__(self):
        self.database_url = "https://cattlemonitor-57c45-default-rtdb.firebaseio.com"
    
    def get_collection(self, collection_name: str) -> Dict[str, Any]:
        """Get all documents from a collection using HTTP"""
        try:
            response = requests.get(f"{self.database_url}/{collection_name}.json")
            if response.status_code == 200:
                data = response.json()
                if data:
                    # Convert to list format similar to the original service
                    documents = []
                    for doc_id, doc_data in data.items():
                        if isinstance(doc_data, dict):
                            doc_data["id"] = doc_id
                            documents.append(doc_data)
                    return {"success": True, "data": documents}
                else:
                    return {"success": True, "data": []}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_document(self, collection_name: str, document_id: str) -> Dict[str, Any]:
        """Get a single document using HTTP"""
        try:
            response = requests.get(f"{self.database_url}/{collection_name}/{document_id}.json")
            if response.status_code == 200:
                data = response.json()
                if data:
                    if isinstance(data, dict):
                        data["id"] = document_id
                    return {"success": True, "data": data}
                else:
                    return {"success": False, "message": "Document not found"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_document(self, collection_name: str, document_id: str, data: dict) -> Dict[str, Any]:
        """Create a document using HTTP"""
        try:
            response = requests.put(f"{self.database_url}/{collection_name}/{document_id}.json", json=data)
            if response.status_code == 200:
                return {"success": True, "message": f"Document {document_id} created successfully"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_document(self, collection_name: str, document_id: str, data: dict) -> Dict[str, Any]:
        """Update a document using HTTP"""
        try:
            response = requests.patch(f"{self.database_url}/{collection_name}/{document_id}.json", json=data)
            if response.status_code == 200:
                return {"success": True, "message": f"Document {document_id} updated successfully"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_document(self, collection_name: str, document_id: str) -> Dict[str, Any]:
        """Delete a document using HTTP"""
        try:
            response = requests.delete(f"{self.database_url}/{collection_name}/{document_id}.json")
            if response.status_code == 200:
                return {"success": True, "message": f"Document {document_id} deleted successfully"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def set_realtime_data(self, path: str, data: dict) -> Dict[str, Any]:
        """Set data in Realtime Database using HTTP"""
        try:
            response = requests.put(f"{self.database_url}/{path}.json", json=data)
            if response.status_code == 200:
                return {"success": True, "message": f"Data set at {path}"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_realtime_data(self, path: str) -> Dict[str, Any]:
        """Get data from Realtime Database using HTTP"""
        try:
            response = requests.get(f"{self.database_url}/{path}.json")
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_realtime_data(self, path: str, data: dict) -> Dict[str, Any]:
        """Update data in Realtime Database using HTTP"""
        try:
            response = requests.patch(f"{self.database_url}/{path}.json", json=data)
            if response.status_code == 200:
                return {"success": True, "message": f"Data updated at {path}"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_realtime_data(self, path: str) -> Dict[str, Any]:
        """Delete data from Realtime Database using HTTP"""
        try:
            response = requests.delete(f"{self.database_url}/{path}.json")
            if response.status_code == 200:
                return {"success": True, "message": f"Data deleted at {path}"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Create the temporary service instance
temp_firebase_service = TemporaryFirebaseService()

# For testing purposes, you can replace the import in main.py temporarily
print("✅ Temporary Firebase HTTP service initialized")
print("🔧 This bypasses authentication issues for immediate testing")
print("📝 Remember to fix the service account key for production use")

# Export for imports
__all__ = ['temp_firebase_service', 'TemporaryFirebaseService']
