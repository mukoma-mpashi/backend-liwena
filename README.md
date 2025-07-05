# Firebase Setup Instructions

## 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or select an existing project
3. Enable Firestore Database and/or Realtime Database as needed

## 2. Generate Service Account Key
1. Go to Project Settings > Service Accounts
2. Click "Generate new private key"
3. Save the JSON file as `firebase-service-account-key.json` in your project root
4. Keep this file secure and never commit it to version control

## 3. Update Environment Variables
Update the `.env` file with your Firebase project details:
```
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=firebase-service-account-key.json
FIREBASE_DATABASE_URL=https://your-project-id-default-rtdb.firebaseio.com/
```

## 4. Firestore Security Rules (Optional)
If using Firestore, update your security rules in the Firebase Console:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true; // For development only
    }
  }
}
```

## 5. Run the Application
```bash
uvicorn main:app --reload
```

## API Endpoints

### Firestore Operations
- `POST /firestore/{collection_name}/{document_id}` - Create document
- `GET /firestore/{collection_name}/{document_id}` - Get document
- `PUT /firestore/{collection_name}/{document_id}` - Update document
- `DELETE /firestore/{collection_name}/{document_id}` - Delete document
- `GET /firestore/{collection_name}` - Get all documents in collection

### Realtime Database Operations
- `POST /realtime/{path}` - Set data at path
- `GET /realtime/{path}` - Get data from path

### Example Usage
```bash
# Create a user document
curl -X POST "http://localhost:8000/firestore/users/user1" \
  -H "Content-Type: application/json" \
  -d '{"data": {"name": "John Doe", "email": "john@example.com", "age": 30}}'

# Get a user document
curl -X GET "http://localhost:8000/firestore/users/user1"

# Update a user document
curl -X PUT "http://localhost:8000/firestore/users/user1" \
  -H "Content-Type: application/json" \
  -d '{"data": {"name": "John Smith", "age": 31}}'

# Get all users
curl -X GET "http://localhost:8000/firestore/users"
```
