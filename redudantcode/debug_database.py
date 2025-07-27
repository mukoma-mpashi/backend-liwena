"""
Debug script to see what's in the Firebase Realtime Database
"""

from firebase_service import firebase_service

def debug_database():
    print("🔍 Debugging Firebase Realtime Database Contents...")
    
    collections = ["cattle", "staff", "alerts"]
    
    for collection in collections:
        print(f"\n📊 {collection.upper()} COLLECTION:")
        print("-" * 40)
        
        try:
            # Get raw data
            raw_result = firebase_service.get_realtime_data(collection)
            if raw_result["success"]:
                raw_data = raw_result["data"]
                print(f"Raw data type: {type(raw_data)}")
                print(f"Raw data: {raw_data}")
                
                if raw_data:
                    print(f"Number of items: {len(raw_data) if isinstance(raw_data, dict) else 'N/A'}")
                    
                    # Try to get as collection
                    collection_result = firebase_service.get_collection(collection)
                    if collection_result["success"]:
                        print(f"✅ Collection method worked: {len(collection_result['data'])} documents")
                        for doc in collection_result["data"][:2]:  # Show first 2
                            print(f"  - Document: {doc}")
                    else:
                        print(f"❌ Collection method failed: {collection_result.get('error', 'Unknown error')}")
                else:
                    print("Collection is empty")
            else:
                print(f"❌ Failed to get raw data: {raw_result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    debug_database()
