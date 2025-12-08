# 🚀 StartSmart - Complete Deployment Guide for Admin

**Document Version:** 1.0  
**Last Updated:** December 8, 2025  
**Branch:** `danish_dev`  
**Repository:** https://github.com/Danish-Ahmed007/Start-Smart

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Architecture](#-architecture)
3. [Prerequisites](#-prerequisites)
4. [Required API Keys](#-required-api-keys)
5. [Deployment Option A: Render.com (Recommended)](#-deployment-option-a-rendercom-recommended)
6. [Deployment Option B: Alternative Platforms](#-deployment-option-b-alternative-platforms)
7. [Frontend Deployment on Vercel](#-frontend-deployment-on-vercel)
8. [Post-Deployment Configuration](#-post-deployment-configuration)
9. [Testing the Deployment](#-testing-the-deployment)
10. [Troubleshooting](#-troubleshooting)
11. [Maintenance & Updates](#-maintenance--updates)

---

## 📖 Overview

StartSmart is a location intelligence platform that helps entrepreneurs find optimal business locations in Karachi. The application consists of:

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Flutter Web | User interface with Google Maps |
| **Backend** | FastAPI (Python) | REST API & business logic |
| **Database** | PostgreSQL | Data storage |
| **AI Engine** | Groq LLM | Intelligent recommendations |

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Flutter Web   │────▶│   FastAPI       │────▶│   PostgreSQL    │
│   (Frontend)    │     │   (Backend)     │     │   (Database)    │
│                 │     │                 │     │                 │
│   Vercel        │     │   Render.com    │     │   Render DB     │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  External APIs  │
                        │  - Google Maps  │
                        │  - Groq LLM     │
                        └─────────────────┘
```

---

## ✅ Prerequisites

Before starting deployment, ensure you have:

- [ ] GitHub account with admin access to the repository
- [ ] Render.com account (free tier available)
- [ ] Vercel account (free tier available)
- [ ] Google Cloud account (for API keys)
- [ ] Groq account (for LLM API key)

---

## 🔑 Required API Keys

You will need **3 API keys** before deployment:

### 1. Google Maps JavaScript API Key

**Purpose:** Display maps in the frontend

**How to get:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project named "StartSmart"
3. Navigate to **APIs & Services** → **Library**
4. Search and enable: **"Maps JavaScript API"**
5. Go to **APIs & Services** → **Credentials**
6. Click **"+ CREATE CREDENTIALS"** → **"API key"**
7. Copy the API key
8. **(Recommended)** Click on the key → **"Application restrictions"** → **"HTTP referrers"**
   - Add your Vercel domain: `https://your-app.vercel.app/*`

### 2. Google Places API Key

**Purpose:** Fetch business data for analysis

**How to get:**
1. In the same Google Cloud project
2. Go to **APIs & Services** → **Library**
3. Search and enable: **"Places API"**
4. You can use the same API key as Maps, OR create a separate one
5. **(Recommended)** Restrict to server IPs only for security

### 3. Groq API Key

**Purpose:** AI-powered location recommendations

**How to get:**
1. Go to [Groq Console](https://console.groq.com/)
2. Sign up or log in (free tier available)
3. Navigate to **API Keys**
4. Click **"Create API Key"**
5. Copy the key (starts with `gsk_`)

---

## 🎯 Deployment Option A: Render.com (Recommended)

Render.com provides free hosting for both backend and database.

### Step 1: Create Render.com Account

1. Go to [render.com](https://render.com)
2. Click **"Get Started for Free"**
3. **Sign up with GitHub** (important - this links your repos)
4. Authorize Render to access your GitHub account

### Step 2: Deploy Using Blueprint (Automatic)

The repository includes a `render.yaml` file that automates deployment.

1. Log into Render Dashboard
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub account if not already connected
4. Select repository: **"Start-Smart"**
5. Select branch: **"danish_dev"**
6. Render will detect `render.yaml` and show:
   - Web Service: `startsmart-api`
   - Database: `startsmart-db`
7. Click **"Apply"**

### Step 3: Set Environment Variables

**⚠️ CRITICAL: You must set these manually!**

1. After deployment starts, go to your **Web Service** (`startsmart-api`)
2. Click on **"Environment"** tab
3. Add the following environment variables:

| Key | Value | Type |
|-----|-------|------|
| `GOOGLE_PLACES_API_KEY` | Your Google Places API key | Secret |
| `GROQ_API_KEY` | Your Groq API key (starts with `gsk_`) | Secret |

4. Click **"Save Changes"**
5. The service will automatically redeploy

### Step 4: Wait for Deployment

- Database creation: ~2-5 minutes
- Backend deployment: ~5-10 minutes
- First deploy may take longer as dependencies are installed

### Step 5: Verify Backend Deployment

1. Find your backend URL in Render Dashboard (e.g., `https://startsmart-api.onrender.com`)
2. Test the health endpoint:
   ```
   https://startsmart-api.onrender.com/api/v1/health
   ```
3. Expected response:
   ```json
   {
     "status": "healthy",
     "timestamp": "2025-12-08T...",
     "database": "connected"
   }
   ```

4. Test API documentation:
   ```
   https://startsmart-api.onrender.com/docs
   ```

**✅ Backend is now deployed!**

---

## 🌐 Frontend Deployment on Vercel

### Step 1: Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Click **"Start Deploying"**
3. **Sign up with GitHub**
4. Authorize Vercel to access your repositories

### Step 2: Prepare Frontend for Production

Before deploying, you need to update the frontend to use the production backend URL.

#### Option A: Update Code Directly (Recommended)

1. Open file: `frontend/lib/utils/constants.dart`
2. Find line 7: `const bool kIsProduction = false;`
3. Change to: `const bool kIsProduction = true;`
4. Find line 16: `static const String _productionUrl = ...`
5. Update with your Render URL:
   ```dart
   static const String _productionUrl = 'https://startsmart-api.onrender.com/api/v1';
   ```
6. Commit and push changes

#### Option B: Build Locally and Deploy

If you can't modify the code:

```bash
# Clone the repository
git clone https://github.com/Danish-Ahmed007/Start-Smart.git
cd Start-Smart/frontend

# Edit constants.dart as described above

# Build for web
flutter build web --release

# The build output is in: frontend/build/web/
```

### Step 3: Create Frontend Environment File

Create a file `frontend/web/env.js` with your Google Maps API key:

```javascript
const ENV_CONFIG = {
  GOOGLE_MAPS_API_KEY: 'AIzaSy_YOUR_ACTUAL_GOOGLE_MAPS_KEY_HERE'
};
```

**⚠️ This file is gitignored for security. You must create it manually or during build.**

### Step 4: Deploy to Vercel

#### Method 1: Vercel Dashboard (Easiest)

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository: **Start-Smart**
3. Configure the project:
   - **Framework Preset:** Other
   - **Root Directory:** `frontend`
   - **Build Command:** `flutter build web --release`
   - **Output Directory:** `build/web`
4. Click **"Deploy"**

**Note:** Vercel may not have Flutter SDK. See Method 2 if this fails.

#### Method 2: Deploy Pre-built Files (More Reliable)

1. Build locally:
   ```bash
   cd frontend
   flutter build web --release
   ```

2. Create `env.js` in `build/web/`:
   ```javascript
   const ENV_CONFIG = {
     GOOGLE_MAPS_API_KEY: 'YOUR_GOOGLE_MAPS_API_KEY'
   };
   ```

3. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

4. Deploy:
   ```bash
   cd build/web
   vercel --prod
   ```

5. Follow the prompts to link to your Vercel account

### Step 5: Verify Frontend Deployment

1. Open your Vercel URL (e.g., `https://startsmart.vercel.app`)
2. You should see the StartSmart landing page
3. Click "AI-Powered Analysis"
4. Verify the map loads correctly
5. Try analyzing a location

**✅ Frontend is now deployed!**

---

## ⚙️ Post-Deployment Configuration

### Update CORS Settings (If Needed)

If you get CORS errors, update the backend CORS settings:

1. Open `backend/api/main.py`
2. Find the CORS middleware configuration
3. Add your Vercel domain to `allow_origins`:
   ```python
   allow_origins=[
       "http://localhost:*",
       "https://startsmart.vercel.app",  # Add your domain
       "https://*.vercel.app",
   ]
   ```
4. Commit and push - Render will auto-redeploy

### Restrict API Keys (Security)

1. **Google Maps API Key:**
   - Go to Google Cloud Console → Credentials
   - Click on your API key
   - Under "Application restrictions", select "HTTP referrers"
   - Add: `https://your-vercel-app.vercel.app/*`

2. **Google Places API Key:**
   - Restrict to your Render backend IP if possible
   - Or restrict to "API restrictions" → "Places API" only

---

## 🧪 Testing the Deployment

### Backend Tests

```bash
# Health check
curl https://startsmart-api.onrender.com/api/v1/health

# Test neighborhoods endpoint
curl https://startsmart-api.onrender.com/api/v1/neighborhoods

# Test recommendation (replace with actual coordinates)
curl "https://startsmart-api.onrender.com/api/v1/recommendation_fast?lat=24.8093&lon=67.0311&radius=500"
```

### Frontend Tests

1. Open the Vercel URL
2. Click "AI-Powered Analysis"
3. Verify:
   - [ ] Map loads correctly
   - [ ] Can search for business type (Gym/Cafe)
   - [ ] Can select location on map
   - [ ] Can change radius
   - [ ] "Analyze" button works
   - [ ] Results display correctly

---

## 🔧 Troubleshooting

### Backend Issues

#### "Database connection failed"
- Check Render dashboard for database status
- Verify DATABASE_URL is set correctly (auto-set by Render Blueprint)
- Check database logs in Render dashboard

#### "Google Places API error"
- Verify `GOOGLE_PLACES_API_KEY` is set in environment variables
- Check Google Cloud Console for API quota/billing issues
- Ensure Places API is enabled

#### "Groq API error"
- Verify `GROQ_API_KEY` is set correctly
- Check Groq console for API limits
- App will fall back to "Fast Mode" if Groq is unavailable

#### Backend is slow (cold start)
- Free tier on Render spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- Upgrade to paid tier to avoid this

### Frontend Issues

#### Map not loading
- Check browser console for errors
- Verify `env.js` exists with correct API key
- Check Google Cloud Console for API key restrictions

#### "Network error" or "Failed to fetch"
- Verify backend is running (check health endpoint)
- Check CORS configuration
- Verify `kIsProduction = true` and correct backend URL

#### Blank page
- Check browser console for JavaScript errors
- Verify build was successful
- Try clearing browser cache

---

## 🔄 Maintenance & Updates

### Updating the Application

1. Push changes to `danish_dev` branch
2. Render will automatically redeploy backend
3. For frontend, redeploy to Vercel:
   ```bash
   cd frontend
   flutter build web --release
   cd build/web
   vercel --prod
   ```

### Monitoring

- **Render Dashboard:** View logs, metrics, and deployments
- **Vercel Dashboard:** View analytics and deployments
- **Google Cloud Console:** Monitor API usage and quotas

### Database Backups

Render provides automatic backups for databases. You can also:
```bash
# Manual backup (requires Render CLI)
render pg:backup startsmart-db
```

---

## 📊 Cost Summary

| Service | Free Tier Limits | Paid Tier (if needed) |
|---------|-----------------|----------------------|
| Render Backend | 750 hours/month, sleeps after 15min | $7/month for always-on |
| Render Database | 1GB storage, 97 hours/month | $7/month |
| Vercel Frontend | 100GB bandwidth, unlimited deploys | $20/month |
| Google Maps | $200 free credit/month | Pay per use |
| Groq | 14,400 requests/day | Pay per use |

**Total for free tier deployment: $0/month** (within limits)

---

## 📞 Support Contacts

- **Repository Issues:** https://github.com/Danish-Ahmed007/Start-Smart/issues
- **Render Support:** https://render.com/docs
- **Vercel Support:** https://vercel.com/docs
- **Google Cloud Support:** https://cloud.google.com/support

---

## ✅ Deployment Checklist

Use this checklist to ensure everything is set up correctly:

### Before Deployment
- [ ] Have Google Cloud account with billing enabled
- [ ] Have Groq account
- [ ] Have Render.com account connected to GitHub
- [ ] Have Vercel account connected to GitHub

### Backend Deployment (Render)
- [ ] Blueprint deployed successfully
- [ ] Database created and connected
- [ ] `GOOGLE_PLACES_API_KEY` set in environment
- [ ] `GROQ_API_KEY` set in environment
- [ ] Health endpoint returns "healthy"
- [ ] API docs accessible at /docs

### Frontend Deployment (Vercel)
- [ ] `kIsProduction = true` in constants.dart
- [ ] `_productionUrl` set to Render backend URL
- [ ] `env.js` created with Google Maps API key
- [ ] Deployed successfully to Vercel
- [ ] Map loads correctly
- [ ] Can perform analysis

### Post-Deployment
- [ ] CORS configured for Vercel domain
- [ ] API keys restricted for security
- [ ] Tested all main features
- [ ] Documented deployment URLs

---

## 🎉 Congratulations!

Your StartSmart application is now deployed and accessible worldwide!

**Your URLs:**
- Frontend: `https://your-app.vercel.app`
- Backend API: `https://startsmart-api.onrender.com`
- API Docs: `https://startsmart-api.onrender.com/docs`

---

*This guide was prepared for the StartSmart project deployment.*
*For any issues, please contact the development team or create a GitHub issue.*
