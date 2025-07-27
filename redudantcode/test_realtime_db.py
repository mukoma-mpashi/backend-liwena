import requests
import json

API_BASE_URL = "https://cattle-monitoring.onrender.com"  # Change to your deployed URL if needed

def pretty(resp):
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)

def test_get_cattle_locations():
    print("\n=== GET /cattle-locations ===")
    resp = requests.get(f"{API_BASE_URL}/cattle-locations")
    pretty(resp)
    assert resp.status_code == 200

if __name__ == "__main__":
    test_get_cattle_locations()