import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8001"
ADMIN_EMAIL = "admin@cattle.com"
ADMIN_PASSWORD = "admin123"
STAFF_EMAIL = "staff@cattle.com"
STAFF_PASSWORD = "staff123"
USER_EMAIL = "user@cattle.com"
USER_PASSWORD = "user123"

def print_response(response, description):
    print(f"\n=== {description} ===")
    print(f"Status Code: {response.status_code}")
    print("Response:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print("="*50)

def test_registration():
    # 1. Register Admin
    print("\nRegistering admin user...")
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "role": "admin"
        }
    )
    print_response(response, "Admin Registration")

    # 2. Register Staff
    print("\nRegistering staff user...")
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": STAFF_EMAIL,
            "password": STAFF_PASSWORD,
            "role": "staff"
        }
    )
    print_response(response, "Staff Registration")

    # 3. Register Regular User
    print("\nRegistering regular user...")
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD,
            "role": "user"
        }
    )
    print_response(response, "User Registration")

def test_protected_endpoints(token, user_type):
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test /auth/me endpoint
    print(f"\nTesting /auth/me with {user_type}...")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print_response(response, f"{user_type} - Get Current User")

    # 2. Test token verification
    print(f"\nTesting token verification with {user_type}...")
    response = requests.get(f"{BASE_URL}/auth/verify", headers=headers)
    print_response(response, f"{user_type} - Token Verification")

    # 3. Test cattle data access
    print(f"\nTesting cattle data access with {user_type}...")
    response = requests.get(f"{BASE_URL}/cattle", headers=headers)
    print_response(response, f"{user_type} - Cattle Data Access")

    # 4. Only test admin-specific endpoints for admin users
    if user_type == "admin":
        print("\nTesting admin-only endpoint...")
        response = requests.get(f"{BASE_URL}/auth/users", headers=headers)
        print_response(response, "Admin - List Users")

def main():
    print("🔑 Starting Authentication Test Suite")
    print("=====================================")
    
    # Step 1: Register users
    test_registration()

    print("\n⚠️ IMPORTANT: Now you need to sign in through Firebase Authentication")
    print("Use these credentials in your frontend Firebase auth:")
    print(f"Admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"Staff: {STAFF_EMAIL} / {STAFF_PASSWORD}")
    print(f"User: {USER_EMAIL} / {USER_PASSWORD}")
    
    # Instructions for getting tokens
    print("\n📝 To get the ID tokens:")
    print("1. Use the Firebase Authentication SDK in a web browser")
    print("2. Sign in with the credentials above")
    print("3. Get the ID token using: await firebase.auth().currentUser.getIdToken()")
    
    # Manual token input
    print("\n🔐 Enter the Firebase ID tokens to test protected endpoints:")
    admin_token = input("\nEnter Admin ID token: ").strip()
    if admin_token:
        test_protected_endpoints(admin_token, "admin")
    
    staff_token = input("\nEnter Staff ID token: ").strip()
    if staff_token:
        test_protected_endpoints(staff_token, "staff")
    
    user_token = input("\nEnter User ID token: ").strip()
    if user_token:
        test_protected_endpoints(user_token, "user")

if __name__ == "__main__":
    main()
