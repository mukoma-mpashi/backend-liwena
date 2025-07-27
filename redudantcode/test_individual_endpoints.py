"""
Simple test to isolate the cattle endpoint issue
"""

import requests
import json

def test_individual_endpoints():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Individual Endpoints...")
    
    # Test basic health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test cattle endpoint with detailed error info
    try:
        print("\n🐄 Testing cattle endpoint...")
        response = requests.get(f"{base_url}/cattle")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('data', []))} cattle")
        else:
            print(f"❌ Error response:")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw error text: {response.text}")
    except Exception as e:
        print(f"❌ Exception during cattle test: {e}")
    
    # Test staff endpoint
    try:
        print("\n👥 Testing staff endpoint...")
        response = requests.get(f"{base_url}/staff")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('data', []))} staff")
        else:
            print(f"❌ Error response:")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw error text: {response.text}")
    except Exception as e:
        print(f"❌ Exception during staff test: {e}")
    
    # Test alerts endpoint
    try:
        print("\n🚨 Testing alerts endpoint...")
        response = requests.get(f"{base_url}/alerts")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data.get('data', []))} alerts")
        else:
            print(f"❌ Error response:")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw error text: {response.text}")
    except Exception as e:
        print(f"❌ Exception during alerts test: {e}")

if __name__ == "__main__":
    test_individual_endpoints()
