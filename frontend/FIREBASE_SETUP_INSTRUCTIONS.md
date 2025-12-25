# Firebase Setup Instructions for Start-Smart

## 🚀 Quick Setup Guide

This guide will help you configure Firebase for the Start-Smart Flutter app to enable user authentication and analytics tracking.

---

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"**
3. Name it: `start-smart-mvp` (or your choice)
4. Disable Google Analytics (optional) → Click **Create Project**
5. Wait for project creation → Click **Continue**

---

## Step 2: Register Web App

1. In Firebase Console, click the **Web icon** (</>) on the project overview page
2. Register app with nickname: `start-smart-web`
3. Check ✅ **"Also set up Firebase Hosting"** (optional)
4. Click **Register app**
5. **COPY the firebaseConfig object** - you'll need this!

Example config you'll receive:
```javascript
const firebaseConfig = {
  apiKey: "AIzaSyC...",
  authDomain: "start-smart-mvp.firebaseapp.com",
  projectId: "start-smart-mvp",
  storageBucket: "start-smart-mvp.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123def456"
};
```

---

## Step 3: Update firebase_options.dart

Open `lib/firebase_options.dart` and replace the placeholder values:

```dart
static const FirebaseOptions web = FirebaseOptions(
  apiKey: 'YOUR_API_KEY',           // ← Replace with your apiKey
  appId: 'YOUR_APP_ID',             // ← Replace with your appId  
  messagingSenderId: 'YOUR_SENDER_ID', // ← Replace with messagingSenderId
  projectId: 'YOUR_PROJECT_ID',     // ← Replace with projectId
  authDomain: 'YOUR_AUTH_DOMAIN',   // ← Replace with authDomain
  storageBucket: 'YOUR_STORAGE_BUCKET', // ← Replace with storageBucket
);
```

---

## Step 4: Enable Authentication Providers

1. In Firebase Console → **Build** → **Authentication**
2. Click **Get started**
3. Enable these sign-in providers:

### 4a. Email/Password
- Click **Email/Password** → Toggle **Enable** → **Save**

### 4b. Google Sign-In
- Click **Google** → Toggle **Enable**
- Set **Project support email** (your email)
- Click **Save**

### 4c. Anonymous (Guest)
- Click **Anonymous** → Toggle **Enable** → **Save**

---

## Step 5: Create Firestore Database

1. Firebase Console → **Build** → **Firestore Database**
2. Click **Create database**
3. Select **Start in test mode** (for development)
4. Choose location closest to you (e.g., `us-central1`)
5. Click **Enable**

---

## Step 6: Set Firestore Security Rules

1. In Firestore → **Rules** tab
2. Replace with these rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Analytics events - anyone authenticated can write
    match /analytics_events/{document} {
      allow create: if request.auth != null;
      allow read: if request.auth != null;
    }
    
    // User feedback - authenticated users can create
    match /user_feedback/{document} {
      allow create: if request.auth != null;
      allow read: if request.auth != null;
    }
    
    // Sessions - authenticated users can manage their sessions
    match /sessions/{document} {
      allow create, update: if request.auth != null;
      allow read: if request.auth != null;
    }
  }
}
```

3. Click **Publish**

---

## Step 7: Configure Google Sign-In for Web

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Firebase project
3. Go to **APIs & Services** → **Credentials**
4. Find **Web client (auto created by Google Service)**
5. Click to edit it
6. Under **Authorized JavaScript origins**, add:
   - `http://localhost:5000` (for local testing)
   - `https://your-domain.vercel.app` (for production)

7. Under **Authorized redirect URIs**, add:
   - `http://localhost:5000/__/auth/handler`
   - `https://your-domain.vercel.app/__/auth/handler`
8. **Save**

---

## Step 8: Run the App

```bash
cd Start-Smart/frontend
flutter pub get
flutter run -d chrome
```

---

## 📊 Verifying Analytics Events

After running the app and performing some actions, check Firestore for data:

1. Firebase Console → **Firestore Database**
2. You should see collections:
   - `users` - User profiles
   - `analytics_events` - All tracked events
   - `user_feedback` - Feedback submissions
   - `sessions` - User sessions

---

## 🔍 Querying Metrics for Assignment 4

### In Firebase Console:

1. Go to Firestore → Select `analytics_events` collection
2. Use filters to find specific events

### Using Python (for reports):

```python
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Get all events from last 7 days
import datetime
week_ago = datetime.datetime.now() - datetime.timedelta(days=7)

# Count analysis completions
completions = db.collection('analytics_events').where('eventType', '==', 'analysis_completed').where('timestamp', '>=', week_ago).stream()
completion_count = len(list(completions))

# Count feedback given
feedback = db.collection('user_feedback').where('timestamp', '>=', week_ago).stream()
feedback_count = len(list(feedback))

# Calculate feedback rate
if completion_count > 0:
    feedback_rate = (feedback_count / completion_count) * 100
    print(f"Feedback Rate: {feedback_rate:.1f}%")
```

---

## 📈 Key Metrics for BML Cycle

| Metric | Firestore Query |
|--------|----------------|
| **Total Users** | Count of `users` collection |
| **Active Sessions** | Count of `sessions` in last 24h |
| **Analysis Started** | `analytics_events` where `eventType == 'analysis_started'` |
| **Analysis Completed** | `analytics_events` where `eventType == 'analysis_completed'` |
| **Completion Rate** | `completed / started * 100` |
| **Positive Feedback** | `user_feedback` where `feedbackType == 'positive'` |
| **Negative Feedback** | `user_feedback` where `feedbackType == 'negative'` |
| **Feedback Rate** | `(positive + negative) / completed * 100` |
| **AI Mode Usage** | `analytics_events` where `mode == 'AI'` |
| **Fast Mode Usage** | `analytics_events` where `mode == 'Fast'` |

---

## ⚠️ Troubleshooting

### "Configuration not found" error
- Make sure `firebase_options.dart` has correct values
- Run `flutter clean` then `flutter pub get`

### Google Sign-In not working
- Check authorized domains in Google Cloud Console
- Ensure redirect URIs are correctly configured

### Firestore permission denied
- Check security rules are published
- Ensure user is authenticated before accessing data

### Web build not working
- Make sure `web/index.html` has Firebase SDK scripts
- Check browser console for errors

---

## 🎯 Next Steps After Setup

1. **Test all auth flows**: Google, Email, Guest
2. **Perform some analyses** to generate data
3. **Check Firestore** for events
4. **Export data** for Assignment 4 report

---

## 📱 For Production Deployment (Vercel)

1. Build the Flutter web app:
```bash
flutter build web --release
```

2. The `build/web` folder contains the deployable files

3. Deploy to Vercel:
```bash
cd build/web
vercel --prod
```

4. Update Google Cloud Console with your production URL in authorized domains

---

## Questions?

If you encounter issues, check:
1. Flutter web build logs
2. Browser developer console (F12)
3. Firebase Console → Authentication → Usage
4. Firestore → Data tab

Good luck with Assignment 4! 🎉
