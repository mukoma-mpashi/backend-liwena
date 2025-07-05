"""
Test script for Firebase integration
Run this after setting up Firebase credentials
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing FastAPI Firebase Backend...")
    
    # Test health check
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Test creating a document
    test_data = {
        "data": {
            "name": "Test User",
            "email": "test@example.com",
            "age": 25,
            "active": True
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/firestore/users/test_user", json=test_data)
        print(f"Create document: {response.status_code} - {response.json()}")
        
        if response.status_code == 200:
            # Test getting the document
            response = requests.get(f"{BASE_URL}/firestore/users/test_user")
            print(f"Get document: {response.status_code} - {response.json()}")
            
            # Test updating the document
            update_data = {
                "data": {
                    "age": 26,
                    "last_updated": "2025-07-04"
                }
            }
            response = requests.put(f"{BASE_URL}/firestore/users/test_user", json=update_data)
            print(f"Update document: {response.status_code} - {response.json()}")
            
            # Test getting collection
            response = requests.get(f"{BASE_URL}/firestore/users")
            print(f"Get collection: {response.status_code} - {response.json()}")
            
    except Exception as e:
        print(f"Firestore tests failed: {e}")
        print("Make sure you have:")
        print("1. Set up Firebase credentials")
        print("2. Started the FastAPI server with: uvicorn main:app --reload")

if __name__ == "__main__":
    test_api()
