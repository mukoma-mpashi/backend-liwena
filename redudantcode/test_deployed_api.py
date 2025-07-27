#!/usr/bin/env python3
"""
Test script to debug the deployed API
"""

import requests
import json

API_BASE_URL = "https://cattle-monitoring.onrender.com"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"{method} {endpoint}: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Success: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
        
        print("-" * 50)
        return response
    except Exception as e:
        print(f"❌ Exception: {e}")
        print("-" * 50)
        return None

def main():
    print("🔍 Testing Deployed API...")
    print(f"API Base URL: {API_BASE_URL}")
    print("=" * 60)
    
    # Test basic endpoints
    test_endpoint("/")
    test_endpoint("/health")
    
    # Test debug endpoints
    test_endpoint("/debug/firebase")
    test_endpoint("/debug/data")
    
    # Test main endpoints
    test_endpoint("/cattle")
    test_endpoint("/staff")
    test_endpoint("/alerts")
   # test_endpoint("/dashboard/summary")
    
    print("Testing complete!")

if __name__ == "__main__":
    main()
