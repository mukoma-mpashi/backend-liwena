#!/usr/bin/env python3
"""
Comprehensive Geofencing Test Script
Tests the geofencing logic with various scenarios
"""

import sys
import os
sys.path.append('.')

from routers.geofence import check_cattle_geofence_status
from temp_firebase_service import temp_firebase_service as firebase_service
from shapely.geometry import Point, Polygon
import json
from datetime import datetime

def create_test_geofences():
    """Create sample geofences for testing"""
    print("🗺️ Creating test geofences...")
    
    # Test Geofence 1: Square around Lusaka, Zambia
    geofence1 = {
        "id": "test_geofence_1",
        "name": "Lusaka Grazing Area",
        "coordinates": [
            [28.2500, -15.4000],  # Southwest corner
            [28.3000, -15.4000],  # Southeast corner
            [28.3000, -15.3500],  # Northeast corner
            [28.2500, -15.3500],  # Northwest corner
            [28.2500, -15.4000]   # Close polygon
        ]
    }
    
    # Test Geofence 2: Smaller square for testing breaches
    geofence2 = {
        "id": "test_geofence_2", 
        "name": "Small Farm Area",
        "coordinates": [
            [28.2700, -15.3800],  # Southwest corner
            [28.2800, -15.3800],  # Southeast corner
            [28.2800, -15.3700],  # Northeast corner
            [28.2700, -15.3700],  # Northwest corner
            [28.2700, -15.3800]   # Close polygon
        ]
    }
    
    # Store geofences in Firebase
    result1 = firebase_service.create_document("geofences", "test_geofence_1", geofence1)
    result2 = firebase_service.create_document("geofences", "test_geofence_2", geofence2)
    
    if result1["success"] and result2["success"]:
        print("✅ Test geofences created successfully")
        return True
    else:
        print("❌ Failed to create test geofences")
        print(f"Geofence 1: {result1}")
        print(f"Geofence 2: {result2}")
        return False

def create_test_cattle_data():
    """Create sample cattle data for testing"""
    print("🐄 Creating test cattle data...")
    
    # Test Cattle 1: Inside both geofences
    cattle1_data = {
        "cattle_id": "test_cattle_001",
        "timestamp": datetime.now().isoformat(),
        "latitude": -15.3750,  # Inside both geofences
        "longitude": 28.2750,
        "gps_fix": True,
        "speed_kmh": 2.5,
        "heading": 45.0,
        "is_moving": True,
        "acceleration": {"x": 0.1, "y": 0.2, "z": 9.8},
        "behavior": {
            "current": "grazing",
            "previous": "walking",
            "duration_seconds": 300,
            "confidence": 0.85
        },
        "activity": {
            "total_active_time_seconds": 14400,
            "total_rest_time_seconds": 28800,
            "daily_steps": 1250,
            "daily_distance_km": 2.3
        }
    }
    
    # Test Cattle 2: Outside both geofences
    cattle2_data = {
        "cattle_id": "test_cattle_002",
        "timestamp": datetime.now().isoformat(),
        "latitude": -15.4500,  # Outside both geofences
        "longitude": 28.2000,
        "gps_fix": True,
        "speed_kmh": 8.5,
        "heading": 180.0,
        "is_moving": True,
        "acceleration": {"x": -0.2, "y": 0.1, "z": 9.7},
        "behavior": {
            "current": "walking",
            "previous": "grazing",
            "duration_seconds": 120,
            "confidence": 0.92
        },
        "activity": {
            "total_active_time_seconds": 18000,
            "total_rest_time_seconds": 25200,
            "daily_steps": 2100,
            "daily_distance_km": 4.1
        }
    }
    
    # Test Cattle 3: Inside large geofence, outside small one
    cattle3_data = {
        "cattle_id": "test_cattle_003",
        "timestamp": datetime.now().isoformat(),
        "latitude": -15.3600,  # Inside large, outside small
        "longitude": 28.2600,
        "gps_fix": True,
        "speed_kmh": 1.2,
        "heading": 90.0,
        "is_moving": False,
        "acceleration": {"x": 0.0, "y": 0.0, "z": 9.8},
        "behavior": {
            "current": "resting",
            "previous": "grazing",
            "duration_seconds": 1800,
            "confidence": 0.78
        },
        "activity": {
            "total_active_time_seconds": 12000,
            "total_rest_time_seconds": 31200,
            "daily_steps": 850,
            "daily_distance_km": 1.8
        }
    }
    
    # Store cattle data in Firebase
    result1 = firebase_service.set_realtime_data("cattle_live_data/test_cattle_001", cattle1_data)
    result2 = firebase_service.set_realtime_data("cattle_live_data/test_cattle_002", cattle2_data)
    result3 = firebase_service.set_realtime_data("cattle_live_data/test_cattle_003", cattle3_data)
    
    if result1["success"] and result2["success"] and result3["success"]:
        print("✅ Test cattle data created successfully")
        return True
    else:
        print("❌ Failed to create test cattle data")
        return False

def test_geofence_logic():
    """Test the geofencing logic with various scenarios"""
    print("\n" + "="*60)
    print("🧪 STARTING GEOFENCE LOGIC TESTS")
    print("="*60)
    
    test_cases = [
        {
            "cattle_id": "test_cattle_001",
            "description": "Cattle inside both geofences",
            "expected_breaches": 0
        },
        {
            "cattle_id": "test_cattle_002", 
            "description": "Cattle outside both geofences",
            "expected_breaches": 2
        },
        {
            "cattle_id": "test_cattle_003",
            "description": "Cattle inside large geofence, outside small one",
            "expected_breaches": 1
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 TEST {i}: {test_case['description']}")
        print("-" * 40)
        
        cattle_id = test_case["cattle_id"]
        expected_breaches = test_case["expected_breaches"]
        
        # Get cattle location from live data
        live_data_result = firebase_service.get_realtime_data(f"cattle_live_data/{cattle_id}")
        
        if not live_data_result["success"]:
            print(f"❌ Failed to get live data for {cattle_id}")
            continue
        
        cattle_data = live_data_result["data"]
        latitude = cattle_data["latitude"]
        longitude = cattle_data["longitude"]
        
        print(f"📍 Cattle Location: ({latitude:.6f}, {longitude:.6f})")
        
        # Test the geofence logic
        result = check_cattle_geofence_status(cattle_id, latitude, longitude)
        
        print(f"\n📊 GEOFENCE CHECK RESULTS:")
        print(f"   Success: {result.get('success')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Total Geofences: {result.get('total_geofences', 0)}")
        print(f"   Total Breaches: {result.get('total_breaches', 0)}")
        print(f"   Inside Geofences: {len(result.get('inside_geofences', []))}")
        print(f"   Outside Geofences: {len(result.get('outside_geofences', []))}")
        print(f"   Alerts Generated: {len(result.get('alerts', []))}")
        
        # Check if results match expectations
        actual_breaches = result.get('total_breaches', 0)
        if actual_breaches == expected_breaches:
            print(f"✅ TEST PASSED: Expected {expected_breaches} breaches, got {actual_breaches}")
        else:
            print(f"❌ TEST FAILED: Expected {expected_breaches} breaches, got {actual_breaches}")
        
        # Display detailed geofence information
        if result.get('inside_geofences'):
            print(f"\n   🟢 INSIDE GEOFENCES:")
            for gf in result['inside_geofences']:
                print(f"      - {gf['name']} (ID: {gf['id']})")
                print(f"        Distance to boundary: {gf['distance_to_boundary_km']} km")
        
        if result.get('outside_geofences'):
            print(f"\n   🔴 OUTSIDE GEOFENCES:")
            for gf in result['outside_geofences']:
                print(f"      - {gf['name']} (ID: {gf['id']})")
                print(f"        Distance from boundary: {gf['distance_to_boundary_km']} km")
        
        # Display alerts
        if result.get('alerts'):
            print(f"\n   🚨 ALERTS GENERATED:")
            for alert in result['alerts']:
                print(f"      - {alert['message']}")
                print(f"        Severity: {alert['severity']}")
                print(f"        Timestamp: {alert['timestamp']}")

def test_direct_coordinates():
    """Test geofencing with direct coordinates (no database dependency)"""
    print("\n" + "="*60)
    print("🎯 TESTING DIRECT COORDINATE CHECKING")
    print("="*60)
    
    # Test coordinates
    test_coordinates = [
        {"lat": -15.3750, "lng": 28.2750, "description": "Inside both geofences"},
        {"lat": -15.4500, "lng": 28.2000, "description": "Outside both geofences"},
        {"lat": -15.3600, "lng": 28.2600, "description": "Edge case - near boundary"},
        {"lat": -15.3750, "lng": 28.2750, "description": "Exact center of large geofence"}
    ]
    
    for i, coord in enumerate(test_coordinates, 1):
        print(f"\n🎯 COORDINATE TEST {i}: {coord['description']}")
        print(f"   Location: ({coord['lat']:.6f}, {coord['lng']:.6f})")
        
        result = check_cattle_geofence_status(f"test_coord_{i}", coord['lat'], coord['lng'])
        
        if result['success']:
            print(f"   ✅ Check successful")
            print(f"   Status: {result.get('status')}")
            print(f"   Breaches: {result.get('total_breaches', 0)}")
        else:
            print(f"   ❌ Check failed: {result.get('error')}")

def cleanup_test_data():
    """Clean up test data from Firebase"""
    print("\n🧹 Cleaning up test data...")
    
    # Delete test geofences
    firebase_service.delete_document("geofences", "test_geofence_1")
    firebase_service.delete_document("geofences", "test_geofence_2")
    
    # Delete test cattle data
    firebase_service.delete_realtime_data("cattle_live_data/test_cattle_001")
    firebase_service.delete_realtime_data("cattle_live_data/test_cattle_002")
    firebase_service.delete_realtime_data("cattle_live_data/test_cattle_003")
    
    print("✅ Test data cleanup completed")

def main():
    """Main test function"""
    print("🚀 GEOFENCING SYSTEM TEST SUITE")
    print("=" * 50)
    
    try:
        # Setup test data
        if not create_test_geofences():
            print("❌ Failed to create test geofences. Exiting.")
            return
        
        if not create_test_cattle_data():
            print("❌ Failed to create test cattle data. Exiting.")
            return
        
        # Run tests
        test_geofence_logic()
        test_direct_coordinates()
        
        # Cleanup
        cleanup_test_data()
        
        print("\n" + "="*60)
        print("🎉 GEOFENCING TESTS COMPLETED!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Critical error during testing: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Attempt cleanup even if tests failed
        try:
            cleanup_test_data()
        except:
            pass

if __name__ == "__main__":
    main()
