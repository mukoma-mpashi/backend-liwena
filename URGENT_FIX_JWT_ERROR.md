# 🚨 URGENT: Fix Invalid JWT Signature Error

## Problem Identified ✅
Your deployment is failing with **"Invalid JWT Signature"** error. This means the Firebase service account key in your Render environment variables is malformed.

## Solution Steps

### Step 1: Update Environment Variable in Render

1. Go to your Render dashboard
2. Click on your `cattle-monitoring` service
3. Go to the **"Environment"** tab
4. Find the `FIREBASE_SERVICE_ACCOUNT_KEY` variable
5. **Delete the current value completely**
6. **Copy and paste the EXACT value below** (no extra spaces or line breaks):

```json
{"type":"service_account","project_id":"cattlemonitor-57c45","private_key_id":"f4ee97e0e5e1de14df721b1e24b7aef25b484e69","private_key":"-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCol1oGuf6Zvfe2\nv72T0rJ/4pPXiiTddlMUynn3oEr6tMXbZP6JFjBZPs8QFgjJJn08OzGuNEQbAKjq\nPZRfTAGGkldt7evyKVN8fOkhEGpSMqZyMj36E0YfmJXbV+znvo+9ulIZCpTTluSR\n2ZbmCY8AEWoyWvFUF0a0DBlmLbP77lKcocEEMicNL4z84K3Q/yeDwmj6X6lE8m9E\nu8j0ojsamgbwDqLD4zxg/3HB6lEBzfmtpaV4+Z/3EPPGcVcAVgeWPVddEJas4QeX\nHkok9TDhePACU4SAYhBO9ahpqUKWHm00qsY0Zi66no6O5JGsF4F10MXuXDDZPFVn\ndxZQrex7AgMBAAECggEAF194VIi9B+0te7wPGSszolreupnv13YxOXzYC6EWPrYI\n3OGeZOdbHPGsvPhZD84SvGLL1fDFZRBNMBWzzWxuT7etKv6PtgXNtGtlhLclDlqa\n9yezrkkKxpRIaQhCaLSOHV8d76knDe3pqAtzCgGsPiBWnpQ7czg7jfhEHdrbN44j\nxxa2GqEgRO48cvgeVpUonWe38aq2fRFYWsbC+FaA4Lmtx+TJByAuzNzAR/nnMeTa\nUKXsyrRYY+9Q1Pt3VYdhwPM20wfb0GMf5SykKJhYpA1sB9cB08u0zlWThrHDlb68\n0148ICOtB3xgUAbuRYOgudCa7wxAV9nG+SrNqxEAMQKBgQDnaCunGIXBxQaDMzfa\nMhUzQfG8eG7vp/cDMWfMCJYgtzAgLBzWrCc67uARQZNzXBEA/BaUUwFJd1QuNsDf\nrftVz50UkTtQ7yaXkJpwL5ljC/cbOXXxBHZ5YYorkN7l5s7Q9vb+shQyJaxUT/vW\nifKdqOlLdIMRJym8RyMmGvAVqwKBgQC6giuZZGBgK8vs70gU0FC/apl48wAb/E4o\nXthcKaF643KCSeirpp8mrcJ/DmMDnYAH5ikva2QmT4JB3nEE/7HWtakSe2Z6/bP3\nz1nC9dsy2zOah1PlN9Ba126Zr7wmH0u0u24Yop60VHpkdd0cBs1pWazIB7GSplMd\nu3NyuAkUcQKBgQCXP2QAxCtwmemGyWxBBikLJpfsur6vj5YIlTslhZsyaOlgrdRv\nj3fYshbr0HOim9NVVG8hpRsbPI5d4lWwHVRAIwGlVsNxQ85ylAYNO19C+KgbODRZ\nQrR444LetMKre29D75dCo3xFxo/bT6fn8qQL3kIVmmKsTG+f6tMTbdnsHwKBgFkl\ncOt/o+Uz6eQVNzHjpETqEfNSywGVZlI7i1T5/Ro87vXBl/m7yaR2N1n9qWwH8zNT\nWuo0fYkmRc9wIDtQcFN9PxP7ca9l5oiTToc2dpBnX9IDzyDnvao+ALpq2haqrMf1\nMpmJ2Su+mUW9ZHNJ+RLa7xApRUIgR+gVOghiWMyxAoGAeNXm7Cz2lB5NLJqF3Jgz\nq90PEAGTNAZfoLdzptHu8cLwMSpkgmcPVhV0TzhCW3Q+VVavrIHo8FQEMO4zOY6/\nabN+f9X5POiNHomL04wouHhUag8J8oQPf5Q6qdbzRhg/YWJiy+RlypdPn9hj6DDj\nxFh8kJ+P7jazIfyCHbFtFak=\n-----END PRIVATE KEY-----\n","client_email":"firebase-adminsdk-fbsvc@cattlemonitor-57c45.iam.gserviceaccount.com","client_id":"116538282148193548817","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40cattlemonitor-57c45.iam.gserviceaccount.com","universe_domain":"googleapis.com"}
```

### Step 2: Verify Environment Variables

Make sure you have these **EXACT** environment variables in Render:

1. **FIREBASE_DATABASE_URL**
   ```
   https://cattlemonitor-57c45-default-rtdb.firebaseio.com/
   ```

2. **FIREBASE_SERVICE_ACCOUNT_KEY**
   ```
   [The JSON string from Step 1 above]
   ```

### Step 3: Redeploy

1. After updating the environment variable, click **"Manual Deploy"** in Render
2. Wait for the deployment to complete
3. Check the logs for any errors

### Step 4: Test the Fix

Once deployed, test these URLs:

1. **Health Check**: `https://cattle-monitoring.onrender.com/health`
2. **Cattle Data**: `https://cattle-monitoring.onrender.com/cattle`
3. **Staff Data**: `https://cattle-monitoring.onrender.com/staff`
4. **Alerts**: `https://cattle-monitoring.onrender.com/alerts`

## What Was Wrong?

The Firebase service account key was likely:
- Split across multiple lines
- Had extra spaces or characters
- Was not properly formatted as a single-line JSON string

## Important Notes

⚠️ **Critical**: The JSON string must be on a **single line** with no line breaks or extra spaces
⚠️ **Copy carefully**: Select the entire JSON string starting with `{` and ending with `}`
⚠️ **No quotes**: Don't add extra quotes around the JSON string in the environment variable

## Verification

After fixing, you should see:
- ✅ All endpoints return 200 OK instead of 400 Bad Request
- ✅ Your Vue.js frontend can successfully fetch data
- ✅ Firebase connection established without JWT errors

## If It Still Doesn't Work

1. Check Render deployment logs for specific error messages
2. Verify the Firebase Realtime Database rules allow read/write access
3. Run the test script: `python test_deployed_api.py`

Your API should be working properly after this fix! 🚀
