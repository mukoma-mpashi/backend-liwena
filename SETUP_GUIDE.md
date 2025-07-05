# 🔥 Firebase Setup Guide for Cattle Monitor

## ⚠️ Important: Enable Firestore API

Your Firebase project needs to have Firestore enabled. Follow these steps:

### 1. Enable Firestore Database
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `cattlemonitor-57c45`
3. Click on "Firestore Database" in the left sidebar
4. Click "Create database"
5. Choose "Start in test mode" (for development)
6. Select a location for your database
7. Click "Done"

### 2. Alternative: Enable via API Console
You can also enable it directly via the API console:
- Visit: https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=cattlemonitor-57c45
- Click "Enable" button

### 3. Wait for Propagation
After enabling, wait 2-3 minutes for the changes to propagate through Google's systems.

## 🚀 Once Firestore is Enabled

1. **Populate the database:**
   ```bash
   python populate_database.py
   ```

2. **Test the API:**
   ```bash
   python test_cattle_monitor.py
   ```

3. **Access API Documentation:**
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## 📊 Available API Endpoints

### Cattle Management
- `GET /cattle` - Get all cattle
- `POST /cattle` - Create new cattle
- `GET /cattle/{cattle_id}` - Get specific cattle
- `PUT /cattle/{cattle_id}` - Update cattle
- `DELETE /cattle/{cattle_id}` - Delete cattle
- `GET /cattle/status/{status}` - Get cattle by status
- `GET /cattle/location/{location}` - Get cattle by location

### Staff Management
- `GET /staff` - Get all staff
- `POST /staff` - Create new staff
- `GET /staff/{staff_id}` - Get specific staff
- `PUT /staff/{staff_id}` - Update staff
- `DELETE /staff/{staff_id}` - Delete staff
- `GET /staff/status/{status}` - Get staff by status

### Alert Management
- `GET /alerts` - Get all alerts
- `POST /alerts` - Create new alert
- `GET /alerts/{alert_id}` - Get specific alert
- `PUT /alerts/{alert_id}` - Update alert
- `DELETE /alerts/{alert_id}` - Delete alert
- `GET /alerts/cattle/{cattle_id}` - Get alerts for specific cattle
- `GET /alerts/type/{type}` - Get alerts by type

### Dashboard
- `GET /dashboard/summary` - Get comprehensive dashboard data

## 🧪 Example API Usage

### Create a new cattle:
```bash
curl -X POST "http://localhost:8000/cattle" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "Holstein",
    "status": "Grazing",
    "location": "West Field",
    "lastMovement": "2025-07-04T12:00:00Z",
    "position": {"x": 100, "y": 200}
  }'
```

### Get all cattle:
```bash
curl -X GET "http://localhost:8000/cattle"
```

### Get cattle by status:
```bash
curl -X GET "http://localhost:8000/cattle/status/Grazing"
```

### Get dashboard summary:
```bash
curl -X GET "http://localhost:8000/dashboard/summary"
```

## 🔧 Troubleshooting

### If you get Firestore API errors:
1. Make sure Firestore is enabled in your Firebase Console
2. Wait 2-3 minutes after enabling
3. Check that your service account has the necessary permissions

### If you get authentication errors:
1. Make sure your `firebase-service-account-key.json` is in the project root
2. Check that the file path in `.env` is correct
3. Verify the service account has "Firebase Admin SDK Administrator" role

## 🎯 Next Steps

1. Enable Firestore in your Firebase Console
2. Run the population script
3. Test the API endpoints
4. Build your frontend to connect to these endpoints!

Your cattle monitoring system is ready to go! 🐄📊
