import firebase_admin
from firebase_admin import credentials, db
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FirebaseService:
    def __init__(self):
        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            # For service account key file
            service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
            database_url = os.getenv("FIREBASE_DATABASE_URL")
            service_account_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
            
            if service_account_key:
                # For deployment - service account key as JSON string
                try:
                    service_account_info = json.loads(service_account_key)
                    cred = credentials.Certificate(service_account_info)
                    firebase_admin.initialize_app(cred, {
                        'databaseURL': database_url
                    })
                except json.JSONDecodeError:
                    print("Error: Invalid JSON in FIREBASE_SERVICE_ACCOUNT_KEY")
                    raise
            elif service_account_path and os.path.exists(service_account_path):
                # For local development - service account key file
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': database_url
                })
            else:
                # Alternative: Initialize with default credentials (for production)
                firebase_admin.initialize_app()
        
        # Initialize Realtime Database client
        self.realtime_db = db.reference()
    
    # Realtime Database methods for collections (simulating Firestore behavior)
    def create_document(self, collection_name: str, document_id: str, data: dict):
        """Create a document in Realtime Database"""
        try:
            self.realtime_db.child(collection_name).child(document_id).set(data)
            return {"success": True, "message": f"Document {document_id} created successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_document(self, collection_name: str, document_id: str):
        """Get a document from Realtime Database"""
        try:
            data = self.realtime_db.child(collection_name).child(document_id).get()
            if data:
                return {"success": True, "data": data}
            else:
                return {"success": False, "message": "Document not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_document(self, collection_name: str, document_id: str, data: dict):
        """Update a document in Realtime Database"""
        try:
            self.realtime_db.child(collection_name).child(document_id).update(data)
            return {"success": True, "message": f"Document {document_id} updated successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_document(self, collection_name: str, document_id: str):
        """Delete a document from Realtime Database"""
        try:
            self.realtime_db.child(collection_name).child(document_id).delete()
            return {"success": True, "message": f"Document {document_id} deleted successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_collection(self, collection_name: str):
        """Get all documents from a collection in Realtime Database"""
        try:
            data = self.realtime_db.child(collection_name).get()
            if data:
                # Convert to list format similar to Firestore
                documents = []
                for doc_id, doc_data in data.items():
                    # Ensure doc_data is a dictionary
                    if isinstance(doc_data, dict):
                        # Add the document ID if it's not already present
                        doc_with_id = {"id": doc_id, **doc_data}
                        documents.append(doc_with_id)
                    else:
                        # Handle case where doc_data is not a dict
                        documents.append({"id": doc_id, "data": doc_data})
                return {"success": True, "data": documents}
            else:
                return {"success": True, "data": []}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Direct Realtime Database methods (for direct path access)
    def set_realtime_data(self, path: str, data: dict):
        """Set data in Realtime Database"""
        try:
            self.realtime_db.child(path).set(data)
            return {"success": True, "message": f"Data set at {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_realtime_data(self, path: str):
        """Get data from Realtime Database"""
        try:
            data = self.realtime_db.child(path).get()
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_realtime_data(self, path: str, data: dict):
        """Update data in Realtime Database"""
        try:
            self.realtime_db.child(path).update(data)
            return {"success": True, "message": f"Data updated at {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_realtime_data(self, path: str):
        """Delete data from Realtime Database"""
        try:
            self.realtime_db.child(path).delete()
            return {"success": True, "message": f"Data deleted at {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Global Firebase service instance
firebase_service = FirebaseService()
