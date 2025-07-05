"""
Test Firebase Realtime Database connection
"""

from firebase_service import firebase_service

def test_realtime_db_connection():
    print("🔥 Testing Firebase Realtime Database Connection...")
    
    # Test basic connection by setting and getting test data
    test_data = {"message": "Hello from Realtime Database!", "timestamp": "2025-07-05T00:00:00Z"}
    
    try:
        print("Attempting to write test data...")
        
        # Try to set test data
        result = firebase_service.set_realtime_data("test_connection", test_data)
        
        if result["success"]:
            print("✅ Successfully wrote test data to Realtime Database!")
            
            # Try to read the data back
            read_result = firebase_service.get_realtime_data("test_connection")
            
            if read_result["success"]:
                print("✅ Successfully read test data from Realtime Database!")
                print(f"Data: {read_result['data']}")
                
                # Clean up test data
                delete_result = firebase_service.delete_realtime_data("test_connection")
                if delete_result["success"]:
                    print("✅ Test data cleaned up successfully!")
                
                print("\n🎉 Realtime Database connection is working perfectly!")
                return True
            else:
                print(f"❌ Failed to read test data: {read_result.get('error', 'Unknown error')}")
                return False
        else:
            print("❌ Firebase Realtime Database connection failed:")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
            # Check for common errors
            error_msg = str(result.get('error', ''))
            if "Permission denied" in error_msg:
                print("\n🚨 PERMISSION DENIED!")
                print("Your Realtime Database security rules might be too restrictive.")
                print("For testing, you can temporarily set rules to allow all reads/writes:")
                print("Go to Firebase Console > Realtime Database > Rules")
                print("Set rules to: {\"rules\": {\".read\": true, \".write\": true}}")
            elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
                print("\n🚨 REALTIME DATABASE NOT CREATED!")
                print("Please create a Realtime Database:")
                print("1. Go to Firebase Console > Realtime Database")
                print("2. Click 'Create Database'")
                print("3. Choose 'Start in test mode'")
                print("4. Select a location")
            elif "URL" in error_msg or "databaseURL" in error_msg:
                print("\n🚨 DATABASE URL ISSUE!")
                print("Check your .env file and make sure FIREBASE_DATABASE_URL is correct.")
                print("It should be: https://cattlemonitor-57c45-default-rtdb.firebaseio.com/")
            
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed with exception: {e}")
        return False

def test_cattle_data_structure():
    print("\n📊 Testing Cattle Data Structure...")
    
    # Test creating a sample cattle record
    sample_cattle = {
        "id": "test_cattle_001",
        "type": "Holstein",
        "status": "Grazing",
        "location": "Test Field",
        "lastMovement": "2025-07-05T12:00:00Z",
        "position": {"x": 100.5, "y": 200.5}
    }
    
    try:
        # Test cattle document creation
        result = firebase_service.create_document("cattle", "test_cattle_001", sample_cattle)
        
        if result["success"]:
            print("✅ Successfully created test cattle record!")
            
            # Test reading the cattle record
            read_result = firebase_service.get_document("cattle", "test_cattle_001")
            
            if read_result["success"]:
                print("✅ Successfully read cattle record!")
                print(f"Cattle data: {read_result['data']}")
                
                # Test updating the cattle record
                update_data = {"status": "Resting", "location": "Barn"}
                update_result = firebase_service.update_document("cattle", "test_cattle_001", update_data)
                
                if update_result["success"]:
                    print("✅ Successfully updated cattle record!")
                    
                    # Test getting all cattle
                    collection_result = firebase_service.get_collection("cattle")
                    if collection_result["success"]:
                        print(f"✅ Successfully retrieved cattle collection! Found {len(collection_result['data'])} records")
                        
                        # Clean up test data
                        delete_result = firebase_service.delete_document("cattle", "test_cattle_001")
                        if delete_result["success"]:
                            print("✅ Test cattle record cleaned up!")
                            return True
                        
        print("❌ Failed to test cattle data structure")
        return False
        
    except Exception as e:
        print(f"❌ Cattle data structure test failed: {e}")
        return False

if __name__ == "__main__":
    print("🐄 Firebase Realtime Database Connection Test")
    print("=" * 50)
    
    # Test basic connection
    if test_realtime_db_connection():
        print("\n" + "=" * 50)
        # Test cattle data structure
        test_cattle_data_structure()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed!")
        print("Your Realtime Database is ready for the cattle monitoring system!")
        print("\nNext steps:")
        print("1. Run: python populate_database.py")
        print("2. Run: python test_cattle_monitor.py")
        print("3. Visit: http://localhost:8000/docs")
    else:
        print("\n❌ Please fix the connection issues before proceeding.")
