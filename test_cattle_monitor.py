"""
Test script for Cattle Monitor API
Run this after starting the FastAPI server
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_cattle_monitor_api():
    print("🐄 Testing Cattle Monitor API...")
    
    # Test health check
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    print("\n" + "="*50)
    print("TESTING CATTLE ENDPOINTS")
    print("="*50)
    
    # Test getting all cattle
    try:
        response = requests.get(f"{BASE_URL}/cattle")
        print(f"GET /cattle: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('data', []))} cattle records")
            for cattle in data.get('data', [])[:2]:  # Show first 2
                print(f"  - {cattle.get('id')}: {cattle.get('type')} - {cattle.get('status')}")
    except Exception as e:
        print(f"Failed to get cattle: {e}")
    
    # Test getting cattle by status
    try:
        response = requests.get(f"{BASE_URL}/cattle/status/Grazing")
        print(f"GET /cattle/status/Grazing: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('data', []))} grazing cattle")
    except Exception as e:
        print(f"Failed to get cattle by status: {e}")
    
    # Test getting cattle by location
    try:
        response = requests.get(f"{BASE_URL}/cattle/location/North Field")
        print(f"GET /cattle/location/North Field: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('data', []))} cattle in North Field")
    except Exception as e:
        print(f"Failed to get cattle by location: {e}")
    
    # Test creating new cattle
    try:
        new_cattle = {
            "type": "Holstein",
            "status": "Grazing",
            "location": "South Field",
            "lastMovement": datetime.now().isoformat() + "Z",
            "position": {"x": 25, "y": 35}
        }
        response = requests.post(f"{BASE_URL}/cattle", json=new_cattle)
        print(f"POST /cattle: {response.status_code}")
        if response.status_code == 200:
            print("✅ Successfully created new cattle record")
    except Exception as e:
        print(f"Failed to create cattle: {e}")
    
    print("\n" + "="*50)
    print("TESTING STAFF ENDPOINTS")
    print("="*50)
    
    # Test getting all staff
    try:
        response = requests.get(f"{BASE_URL}/staff")
        print(f"GET /staff: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('data', []))} staff records")
            for staff in data.get('data', []):
                print(f"  - {staff.get('name')}: {staff.get('role')} - {staff.get('status')}")
    except Exception as e:
        print(f"Failed to get staff: {e}")
    
    # Test getting staff by status
    try:
        response = requests.get(f"{BASE_URL}/staff/status/Online")
        print(f"GET /staff/status/Online: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('data', []))} online staff")
    except Exception as e:
        print(f"Failed to get staff by status: {e}")
    
    print("\n" + "="*50)
    print("TESTING ALERT ENDPOINTS")
    print("="*50)
    
    # Test getting all alerts
    try:
        response = requests.get(f"{BASE_URL}/alerts")
        print(f"GET /alerts: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('data', []))} alerts")
            for alert in data.get('data', []):
                print(f"  - {alert.get('type')}: {alert.get('message')}")
    except Exception as e:
        print(f"Failed to get alerts: {e}")
    
    # Test getting alerts by type
    try:
        response = requests.get(f"{BASE_URL}/alerts/type/Health")
        print(f"GET /alerts/type/Health: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('data', []))} health alerts")
    except Exception as e:
        print(f"Failed to get alerts by type: {e}")
    
    # Test creating new alert
    try:
        new_alert = {
            "cattleId": "cattle1",
            "type": "Location",
            "message": "Cattle moved to restricted area",
            "timestamp": datetime.now().isoformat() + "Z"
        }
        response = requests.post(f"{BASE_URL}/alerts", json=new_alert)
        print(f"POST /alerts: {response.status_code}")
        if response.status_code == 200:
            print("✅ Successfully created new alert")
    except Exception as e:
        print(f"Failed to create alert: {e}")
    
    print("\n" + "="*50)
    print("TESTING DASHBOARD SUMMARY")
    print("="*50)
    
    # Test dashboard summary
    try:
        response = requests.get(f"{BASE_URL}/dashboard/summary")
        print(f"GET /dashboard/summary: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            summary = data.get('data', {})
            
            print("📊 Dashboard Summary:")
            print(f"  Cattle: {summary.get('cattle', {}).get('total', 0)} total")
            print(f"  Staff: {summary.get('staff', {}).get('total', 0)} total ({summary.get('staff', {}).get('online', 0)} online)")
            print(f"  Alerts: {summary.get('alerts', {}).get('total', 0)} total")
            
            print("\n  Cattle by Status:")
            for status, count in summary.get('cattle', {}).get('by_status', {}).items():
                print(f"    {status}: {count}")
            
            print("\n  Cattle by Location:")
            for location, count in summary.get('cattle', {}).get('by_location', {}).items():
                print(f"    {location}: {count}")
                
    except Exception as e:
        print(f"Failed to get dashboard summary: {e}")
    
    print("\n" + "="*50)
    print("🎉 API Testing Complete!")
    print("="*50)
    print("\nAPI Documentation available at: http://localhost:8000/docs")
    print("Alternative docs at: http://localhost:8000/redoc")

if __name__ == "__main__":
    test_cattle_monitor_api()
