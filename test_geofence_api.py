import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"  # Change to your deployed URL if needed

def pretty(resp):
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)

def test_geofence_and_alerts():
    print("\n=== 1. Create Geofence ===")
    geofence = {
        "name": "Test Field",
        "coordinates": [
            [0, 0], [0, 10], [10, 10], [10, 0], [0, 0]
        ]
    }
    resp = requests.post(f"{API_BASE_URL}/geofences", json=geofence)
    pretty(resp)
    assert resp.status_code == 200
    geofence_id = resp.json()["data"]["id"] if "data" in resp.json() and resp.json()["data"] else None

    print("\n=== 2. Cattle Location INSIDE geofence (should NOT alert) ===")
    cattle_loc = {
        "cattle_id": "cattle1",
        "location": [5, 5],
        "timestamp": datetime.utcnow().isoformat()
    }
    resp = requests.post(f"{API_BASE_URL}/cattle-location", json=cattle_loc)
    pretty(resp)
    assert resp.status_code == 200
    assert resp.json().get("inside_geofence") is True

    print("\n=== 3. Cattle Location OUTSIDE geofence (should alert) ===")
    cattle_loc = {
        "cattle_id": "cattle1",
        "location": [20, 20],
        "timestamp": datetime.utcnow().isoformat()
    }
    resp = requests.post(f"{API_BASE_URL}/cattle-location", json=cattle_loc)
    pretty(resp)
    assert resp.status_code == 200
    assert resp.json().get("inside_geofence") is False

    print("\n=== 4. Fetch Alerts (should see geofence alert) ===")
    resp = requests.get(f"{API_BASE_URL}/alerts")
    pretty(resp)
    assert resp.status_code == 200
    found = any(a.get("type") == "Geofence" and a.get("cattleId") == "cattle1" for a in resp.json().get("data", []))
    print("Geofence alert found?", found)

if __name__ == "__main__":
    test_geofence_and_alerts()
