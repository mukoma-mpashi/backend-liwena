# Deployment Guide for Render

This guide will help you deploy your FastAPI cattle monitoring backend to Render.

## Prerequisites

1. A Render account (free tier available)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. Firebase service account key
4. Firebase Realtime Database URL

## Step 1: Prepare Your Repository

1. Make sure all files are committed and pushed to your Git repository
2. Ensure sensitive files are in `.gitignore` (Firebase keys, .env files)

## Step 2: Set Up Firebase Service Account for Deployment

1. Go to your Firebase Console
2. Navigate to Project Settings → Service accounts
3. Click "Generate new private key"
4. Copy the entire JSON content (you'll need this for environment variables)

## Step 3: Deploy to Render

### Option A: Using Render Dashboard (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your Git repository
4. Configure the service:
   - **Name**: `cattle-monitor-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or paid for better performance)

### Option B: Using render.yaml (Infrastructure as Code)

1. The `render.yaml` file is already included in your repository
2. Render will automatically detect and use this configuration

## Step 4: Set Environment Variables

In your Render service dashboard, go to "Environment" and add:

### Required Environment Variables:

```
FIREBASE_DATABASE_URL=https://your-project-id-default-rtdb.firebaseio.com/
FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"your-project-id",...}
```

**Important**: For `FIREBASE_SERVICE_ACCOUNT_KEY`, paste the entire JSON content from your Firebase service account key (the whole JSON object as a string).

### Optional Environment Variables:

```
PYTHON_VERSION=3.11.0
```

## Step 5: Deploy

1. Click "Deploy" in your Render dashboard
2. Monitor the build logs
3. Once deployed, you'll get a URL like: `https://your-service-name.onrender.com`

## Step 6: Test Your Deployment

1. Visit your deployed URL
2. Check the API documentation at: `https://your-service-name.onrender.com/docs`
3. Test the health endpoint: `https://your-service-name.onrender.com/health`

## API Endpoints

Your deployed API will have these endpoints:

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /docs` - API documentation
- `GET /cattle` - Get all cattle
- `POST /cattle` - Create cattle
- `GET /staff` - Get all staff
- `POST /staff` - Create staff
- `GET /alerts` - Get all alerts
- `POST /alerts` - Create alert
- `GET /dashboard/summary` - Dashboard summary

## Troubleshooting

### Common Issues:

1. **Build fails**: Check your `requirements.txt` for correct dependencies
2. **Firebase connection fails**: Verify your environment variables are set correctly
3. **Service won't start**: Check the logs in Render dashboard
4. **CORS issues**: Update CORS settings in `main.py` if needed

### Environment Variable Format:

Make sure your Firebase service account key is formatted as a single line JSON string:
```
{"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}
```

## Security Notes

- Never commit sensitive data to your repository
- Use environment variables for all credentials
- Consider using Render's secret management for sensitive data
- The free tier has limitations; consider upgrading for production use

## Monitoring

- Check Render dashboard for logs and metrics
- Set up monitoring for your Firebase database
- Monitor API response times and error rates

Your cattle monitoring API should now be live and accessible via your Render URL!
