# StartSmart Complete Deployment Guide

## 🎯 Overview

This guide will help you deploy the complete StartSmart MVP to production with:
- **Backend**: FastAPI on Vercel (Serverless)
- **Frontend**: Flutter Web on Vercel
- **Database**: PostgreSQL on Render (already configured)
- **Authentication**: Firebase Auth
- **APIs**: Google Places API, Groq LLM API

---

## 📋 Prerequisites

Before starting, ensure you have:

1. **Accounts**:
   - [GitHub](https://github.com) account
   - [Vercel](https://vercel.com) account (free tier works)
   - [Firebase](https://console.firebase.google.com) project (already set up)
   - [Render](https://render.com) account (for PostgreSQL - already configured)

2. **Tools Installed**:
   - Git
   - Node.js (for Vercel CLI)
   - Flutter SDK
   - Python 3.9+

3. **API Keys Ready**:
   - Google Places API Key
   - Groq API Key
   - Firebase config (already in your project)

---

## 🔐 Step 1: Gather Your Environment Variables

You'll need these environment variables for deployment. Create a file `env_backup.txt` (DO NOT commit this):

```env
# Database (Render PostgreSQL)
DATABASE_URL=postgresql://startsmart_user:YOUR_PASSWORD@YOUR_HOST/startsmart_db

# Google Places API
GOOGLE_PLACES_API_KEY=your_google_places_api_key

# Groq LLM API
GROQ_API_KEY=your_groq_api_key

# Optional
SKIP_DB_CHECK=true
ENVIRONMENT=production
```

### Finding Your Current Keys:

**Check your local `.env` file:**
```powershell
# In PowerShell
cd "D:\OneDrive - Higher Education Commission\Desktop\Real_start_smart\Start-Smart\backend"
Get-Content .env
```

**Or check Render Dashboard for DATABASE_URL:**
1. Go to https://dashboard.render.com
2. Click on your PostgreSQL database
3. Copy the "External Database URL"

---

## 📤 Step 2: Push Code to GitHub

### 2.1 Initialize/Update Git Repository

```powershell
# Navigate to project root
cd "D:\OneDrive - Higher Education Commission\Desktop\Real_start_smart\Start-Smart"

# Check git status
git status

# If not a git repo, initialize it:
git init
git remote add origin https://github.com/YOUR_USERNAME/Start-Smart.git
```

### 2.2 Create `.gitignore` (if not exists)

Ensure these are in your `.gitignore`:

```gitignore
# Environment files
.env
.env.local
.env.production
env_backup.txt

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Flutter
.dart_tool/
.packages
build/
*.iml

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Secrets
*.pem
*.key
secrets/
```

### 2.3 Commit and Push

```powershell
# Add all files
git add .

# Commit with message
git commit -m "Complete MVP with enhanced recommendations, Firebase auth, and data-backed insights"

# Push to main branch
git push -u origin main

# If main doesn't exist, create it:
git branch -M main
git push -u origin main
```

### 2.4 Verify on GitHub

1. Go to `https://github.com/YOUR_USERNAME/Start-Smart`
2. Verify all files are uploaded
3. Check that `.env` is NOT visible (should be gitignored)

---

## 🔧 Step 3: Deploy Backend to Vercel

### 3.1 Install Vercel CLI

```powershell
npm install -g vercel
```

### 3.2 Login to Vercel

```powershell
vercel login
```
- Choose "Continue with GitHub" for easiest setup
- Authorize in browser

### 3.3 Deploy Backend

```powershell
# Navigate to backend folder
cd "D:\OneDrive - Higher Education Commission\Desktop\Real_start_smart\Start-Smart\backend"

# Deploy to Vercel (first time - will ask questions)
vercel

# Answer the prompts:
# ? Set up and deploy? Y
# ? Which scope? (select your account)
# ? Link to existing project? N
# ? What's your project's name? startsmart-backend
# ? In which directory is your code located? ./
# ? Want to modify settings? N
```

### 3.4 Add Environment Variables to Vercel

**Option A: Via Vercel Dashboard (Recommended)**

1. Go to https://vercel.com/dashboard
2. Click on `startsmart-backend` project
3. Go to **Settings** → **Environment Variables**
4. Add each variable:

| Name | Value | Environment |
|------|-------|-------------|
| `DATABASE_URL` | `postgresql://...` | Production |
| `GOOGLE_PLACES_API_KEY` | `your_key` | Production |
| `GROQ_API_KEY` | `your_key` | Production |
| `SKIP_DB_CHECK` | `true` | Production |
| `ENVIRONMENT` | `production` | Production |

**Option B: Via CLI**

```powershell
vercel env add DATABASE_URL production
# Paste your database URL when prompted

vercel env add GOOGLE_PLACES_API_KEY production
# Paste your Google API key

vercel env add GROQ_API_KEY production
# Paste your Groq API key

vercel env add SKIP_DB_CHECK production
# Type: true

vercel env add ENVIRONMENT production
# Type: production
```

### 3.5 Deploy to Production

```powershell
# Deploy to production
vercel --prod
```

### 3.6 Verify Backend Deployment

```powershell
# Test the health endpoint
curl https://startsmart-backend.vercel.app/api/v1/health
```

Or open in browser: `https://YOUR-BACKEND-URL.vercel.app/api/v1/health`

Expected response:
```json
{"status": "healthy", "database": "connected"}
```

### 3.7 Note Your Backend URL

Your backend URL will be something like:
- `https://startsmart-backend.vercel.app`
- Or `https://startsmart-backend-xxxxx.vercel.app`

**Save this URL** - you'll need it for the frontend!

---

## 📱 Step 4: Update Frontend Configuration

### 4.1 Update Backend URL in Frontend

Edit `frontend/lib/utils/constants.dart`:

```dart
// Production URL (Vercel deployment)
// UPDATE THIS with your actual backend URL!
static const String _productionUrl =
    'https://YOUR-ACTUAL-BACKEND-URL.vercel.app/api/v1';
```

### 4.2 Verify Production Mode

In the same file, ensure:
```dart
const bool kIsProduction = true;
```

### 4.3 Verify Firebase Configuration

Check `frontend/lib/firebase_options.dart` has correct config.

Check `frontend/web/index.html` has Firebase SDK:
```html
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.0/firebase-auth-compat.js"></script>
```

---

## 🌐 Step 5: Deploy Frontend to Vercel

### 5.1 Build Flutter Web

```powershell
# Navigate to frontend
cd "D:\OneDrive - Higher Education Commission\Desktop\Real_start_smart\Start-Smart\frontend"

# Clean previous builds
flutter clean

# Get dependencies
flutter pub get

# Build for web (production)
flutter build web --release --web-renderer canvaskit
```

### 5.2 Deploy to Vercel

```powershell
# Make sure you're in the frontend folder
cd "D:\OneDrive - Higher Education Commission\Desktop\Real_start_smart\Start-Smart\frontend"

# Deploy to Vercel
vercel

# Answer prompts:
# ? Set up and deploy? Y
# ? Link to existing project? N
# ? What's your project's name? startsmart-frontend
# ? In which directory is your code located? ./
# ? Want to modify settings? Y
# ? Output directory? build/web
```

### 5.3 Deploy to Production

```powershell
vercel --prod
```

### 5.4 Note Your Frontend URL

Your frontend URL will be something like:
- `https://startsmart-frontend.vercel.app`

---

## 🔥 Step 6: Configure Firebase for Production

### 6.1 Add Production Domain to Firebase

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Go to **Authentication** → **Settings** → **Authorized domains**
4. Click **Add domain**
5. Add your Vercel frontend URL: `startsmart-frontend.vercel.app`

### 6.2 Update Firebase Hosting (Optional)

If you want to use Firebase Hosting instead of Vercel for frontend:

```powershell
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize
firebase init hosting

# Deploy
firebase deploy --only hosting
```

---

## 🗄️ Step 7: Verify Database Connection

### 7.1 Check Render PostgreSQL

1. Go to https://dashboard.render.com
2. Click on your PostgreSQL database
3. Verify it's running (green status)
4. Check **Connections** tab for active connections

### 7.2 Test Database from Backend

Visit: `https://YOUR-BACKEND-URL.vercel.app/api/v1/health`

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-12-18T..."
}
```

### 7.3 Seed Data (If Needed)

If your database is empty, you may need to run the seed scripts locally:

```powershell
# Activate virtual environment
cd "D:\OneDrive - Higher Education Commission\Desktop\Real_start_smart"
.\.venv\Scripts\Activate.ps1

# Navigate to backend
cd Start-Smart\backend

# Run seed script (connects to production DB via DATABASE_URL)
python scripts/seed_render_simple.py
```

---

## ✅ Step 8: Final Verification

### 8.1 Test Complete Flow

1. **Open Frontend**: `https://startsmart-frontend.vercel.app`

2. **Test Authentication**:
   - Click "Sign Up" or "Login"
   - Create a test account
   - Verify login works

3. **Test Recommendation Flow**:
   - Navigate to "Get Recommendation"
   - Select a location on the map (Clifton Block 2 or 5)
   - Choose a radius (100-300m)
   - Click "Analyze"
   - Verify results show:
     - Top 5 business categories with counts
     - Data-backed insights
     - Income data
     - Gym vs Cafe recommendation

4. **Test API Directly**:
   ```
   https://YOUR-BACKEND-URL.vercel.app/api/v1/recommendation_debug?lat=24.815&lon=67.028&radius=200
   ```

### 8.2 Checklist

- [ ] Backend deployed to Vercel
- [ ] Backend health endpoint returns "healthy"
- [ ] Environment variables configured in Vercel
- [ ] Frontend built with production URL
- [ ] Frontend deployed to Vercel
- [ ] Firebase domain authorized
- [ ] User can sign up/login
- [ ] Recommendations work with real data
- [ ] Database connected and returning data

---

## 🔄 Step 9: Set Up Automatic Deployments (Optional)

### 9.1 Connect GitHub to Vercel

1. Go to Vercel Dashboard
2. Click on your project
3. Go to **Settings** → **Git**
4. Click **Connect Git Repository**
5. Select your GitHub repo
6. Choose `main` branch
7. Enable **Auto-deploy on push**

Now every push to `main` will automatically deploy!

### 9.2 Environment Variables in Git (CI/CD)

For GitHub Actions, add secrets:
1. Go to GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Add each environment variable as a secret

---

## 🐛 Troubleshooting

### Backend Issues

**Error: "Module not found"**
```powershell
# Check requirements.txt has all dependencies
# Redeploy
vercel --prod --force
```

**Error: "Database connection failed"**
- Verify `DATABASE_URL` in Vercel environment variables
- Check Render PostgreSQL is running
- Verify IP allowlist on Render (should allow all: 0.0.0.0/0)

**Error: "API key invalid"**
- Verify GOOGLE_PLACES_API_KEY in Vercel
- Check Google Cloud Console for API restrictions

### Frontend Issues

**Error: "CORS blocked"**
- Backend should have CORS configured for your frontend domain
- Check `backend/api/main.py` has correct CORS settings

**Error: "Firebase auth failed"**
- Add Vercel domain to Firebase authorized domains
- Check Firebase config in `firebase_options.dart`

**Blank screen / Build errors**
```powershell
flutter clean
flutter pub get
flutter build web --release
```

### Database Issues

**Empty data**
```powershell
# Run seed script locally with production DATABASE_URL
$env:DATABASE_URL = "your_production_url"
python scripts/seed_render_simple.py
```

---

## 📊 Production URLs Summary

After deployment, your URLs will be:

| Service | URL |
|---------|-----|
| Frontend | `https://startsmart-frontend.vercel.app` |
| Backend API | `https://startsmart-backend.vercel.app/api/v1` |
| Health Check | `https://startsmart-backend.vercel.app/api/v1/health` |
| API Docs | `https://startsmart-backend.vercel.app/docs` |

---

## 🎉 Congratulations!

Your StartSmart MVP is now live! 

### What's Working:
- ✅ User authentication (Firebase)
- ✅ Location-based business analysis
- ✅ Real Google Places data extraction
- ✅ AI-powered recommendations (Groq LLM)
- ✅ Data-backed insights with actual counts
- ✅ Income/demographic analysis
- ✅ Gym vs Cafe suitability scoring

### Next Steps:
1. Share the frontend URL with testers
2. Monitor Vercel analytics for usage
3. Check Vercel logs for any errors
4. Collect user feedback for improvements

---

## 📞 Quick Commands Reference

```powershell
# --- GIT ---
git add .
git commit -m "your message"
git push origin main

# --- BACKEND DEPLOY ---
cd Start-Smart\backend
vercel --prod

# --- FRONTEND DEPLOY ---
cd Start-Smart\frontend
flutter build web --release
vercel --prod

# --- VIEW LOGS ---
vercel logs startsmart-backend
vercel logs startsmart-frontend

# --- ENVIRONMENT VARIABLES ---
vercel env ls
vercel env add VAR_NAME production
vercel env rm VAR_NAME production
```

---

*Last Updated: December 18, 2025*
