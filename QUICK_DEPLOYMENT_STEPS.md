# 🚀 StartSmart - Quick Deployment Steps for Submission

**Goal:** Deploy working app with auditable data storage for final submission  
**Time Required:** ~30-45 minutes  
**Date:** December 8, 2025

---

## ✅ Pre-Deployment Checklist

Before you start, gather these 3 API keys:

### 1. Google Places API Key (Required)
```
Your current key: [REDACTED_GOOGLE_PLACES_API_KEY]
Status: ✅ Already have it
```

### 2. Groq API Key (Required for AI features)
```
Your current key: [REDACTED_GROQ_API_KEY]
Status: ✅ Already have it
```

### 3. Google Maps JavaScript API Key (For frontend map display)
- If you don't have a separate one, you can use the same Places API key
- Or create a new one at: https://console.cloud.google.com/apis/credentials

---

## 📦 PART 1: Deploy Backend + Database (Render.com)

### Step 1: Sign Up on Render.com

1. Go to https://render.com
2. Click **"Get Started for Free"**
3. **Sign up with GitHub** (IMPORTANT - connects your repos)
4. Authorize Render to access your GitHub repositories

### Step 2: Deploy Using Blueprint (Automatic Setup)

Your project has a `render.yaml` file that automatically creates both backend AND database.

**Option A: If you see "Blueprint" option:**
1. In Render Dashboard, click **"New +"** → **"Blueprint"**
2. Select repository: **"Start-Smart"**
3. Select branch: **"danish_dev"**
4. Render will detect `render.yaml` and show:
   - ✅ Web Service: `startsmart-api`
   - ✅ PostgreSQL Database: `startsmart-db` (for auditable data!)
5. Click **"Apply"**

**Option B: If "Blueprint" is not visible (Manual Setup):**

Follow these steps instead:

#### 2a. Create PostgreSQL Database First

1. Click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name:** `startsmart-db`
   - **Database:** `startsmart_dev`
   - **User:** `    `
   - **Region:** Choose closest to you (e.g., Oregon)
   - **PostgreSQL Version:** 15 or latest
   - **Instance Type:** Select **Free** tier
3. Click **"Create Database"**
4. Wait ~2-5 minutes for database to be ready
5. **IMPORTANT:** Copy the **Internal Database URL** (starts with `postgresql://`)

#### 2b. Create Web Service (Backend)

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository:
   - Click **"Connect account"** if not connected
   - Search for **"Start-Smart"**
   - Click **"Connect"**
3. Configure the service:
   - **Name:** `startsmart-api`
   - **Region:** Same as database
   - **Branch:** `danish_dev`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Select **Free** tier
4. **Do NOT click "Create Web Service" yet!**

**This creates:**
- Backend API (Python/FastAPI)
- PostgreSQL database (stores all user interactions, recommendations, feedback)
- Automatic connection between them

### Step 3: Set Environment Variables (CRITICAL!)

**If you used Option A (Blueprint):**
After Blueprint deployment starts, go to your Web Service and add environment variables.

**If you used Option B (Manual):**
Before creating the web service, add environment variables:

1. Scroll down to **"Environment Variables"** section
2. Click **"Add Environment Variable"**
3. Add these THREE variables:

   **Variable 1:**
   ```
   Key: DATABASE_URL
   Value: [Paste the Internal Database URL you copied earlier]
   ```

   **Variable 2:**
   ```
   Key: GOOGLE_PLACES_API_KEY
   Value: [REDACTED_GOOGLE_PLACES_API_KEY]
   ```

   **Variable 3:**
   ```
   Key: GROQ_API_KEY
   Value: [REDACTED_GROQ_API_KEY]
   ```

4. Now click **"Create Web Service"**
5. Deployment will start automatically

### Step 4: Wait for Deployment

- Database: ~2-5 minutes ⏱️
- Backend: ~5-10 minutes ⏱️
- You'll see progress in the Render dashboard
- Status should change to "Live" with a green checkmark ✅

### Step 5: Get Your Backend URL

1. In Render dashboard, click on **startsmart-api**
2. At the top, you'll see the URL: `https://startsmart-api-XXXX.onrender.com`
3. **COPY THIS URL** - you'll need it for frontend

### Step 6: Test Backend

Open in browser:
```
https://your-backend-url.onrender.com/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2025-12-08T...",
  "version": "1.0.0",
  "service": "startsmart-api"
}
```

✅ **Backend is LIVE with database connected!**

---

## 🌐 PART 2: Deploy Frontend (Vercel)

### Step 1: Update Frontend Configuration

You need to tell the frontend to use your live backend URL.

1. Open file: `frontend/lib/utils/constants.dart`
2. Find line 6:
   ```dart
   const bool kIsProduction = false;
   ```
   Change to:
   ```dart
   const bool kIsProduction = true;
   ```

3. Find line 16:
   ```dart
   static const String _productionUrl = 'https://startsmart-api.onrender.com/api/v1';
   ```
   Replace with YOUR Render URL:
   ```dart
   static const String _productionUrl = 'https://your-actual-backend-url.onrender.com/api/v1';
   ```

4. Save the file
5. Commit and push to GitHub:
   ```bash
   git add frontend/lib/utils/constants.dart
   git commit -m "Configure for production deployment"
   git push origin danish_dev
   ```

### Step 2: Build Flutter Web App

```bash
cd "D:\OneDrive - Higher Education Commission\Desktop\Real_start_smart\Start-Smart\frontend"
flutter build web --release
```

This creates optimized files in `frontend/build/web/`

### Step 3: Create Environment File for Google Maps

Create a new file: `frontend/build/web/env.js`

```javascript
const ENV_CONFIG = {
  GOOGLE_MAPS_API_KEY: '[REDACTED_GOOGLE_PLACES_API_KEY]'
};
```

### Step 4: Deploy to Vercel

#### Option A: Using Vercel CLI (Recommended - Fast)

1. Install Vercel CLI globally:
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```
   Follow the email verification

3. Deploy:
   ```bash
   cd "D:\OneDrive - Higher Education Commission\Desktop\Real_start_smart\Start-Smart\frontend\build\web"
   vercel --prod
   ```

4. Follow prompts:
   - Link to existing project? **No**
   - Project name: **startsmart** (or your choice)
   - Directory: **. (current directory)**

#### Option B: Using Vercel Dashboard

1. Go to https://vercel.com/new
2. Sign up with GitHub
3. Click **"Add New Project"**
4. Import **"Start-Smart"** repository
5. Configure:
   - Framework: **Other**
   - Root Directory: `frontend`
   - Build Command: `flutter build web --release`
   - Output Directory: `build/web`
6. Add Environment Variables:
   - `GOOGLE_MAPS_API_KEY`: `[REDACTED_GOOGLE_PLACES_API_KEY]`
7. Click **"Deploy"**

**Note:** Vercel may not have Flutter SDK. Use Option A if deployment fails.

### Step 5: Get Your Frontend URL

After deployment completes:
- Vercel shows your live URL: `https://startsmart-XXXX.vercel.app`
- **COPY THIS URL** - this is your submission link!

### Step 6: Test Frontend

1. Open your Vercel URL
2. You should see the StartSmart landing page
3. Click **"AI-Powered Analysis"** button
4. Map should load showing Clifton, Karachi
5. Click on map to select location
6. Click **"Analyze"** - should show recommendations

✅ **Frontend is LIVE and connected to backend!**

---

## 🔧 PART 3: Update CORS (If Map Doesn't Load)

If you get "CORS error" or blank page:

### Backend Update:

1. Open `backend/api/main.py`
2. Find line ~30 with `allow_origins=`
3. Add your Vercel URL:
   ```python
   allow_origins=[
       "http://localhost:*",
       "https://startsmart-XXXX.vercel.app",  # Your actual URL
       "https://*.vercel.app",
   ]
   ```
4. Commit and push - Render auto-redeploys

---

## 📊 PART 4: Verify Data Storage (For Auditable Requirement)

Your PostgreSQL database stores all this data:

### Check Database in Render:

1. Go to Render Dashboard → **startsmart-db**
2. Click **"Connect"** → Copy connection command
3. Open terminal and connect:
   ```bash
   psql postgresql://startsmart_user:XXXX@XXXX.oregon-postgres.render.com/startsmart_db
   ```

4. Check tables:
   ```sql
   \dt  -- List all tables
   SELECT * FROM micro_grids LIMIT 5;  -- Sample grid data
   SELECT * FROM businesses LIMIT 5;   -- Sample business data
   ```

### Data Being Stored:

| Table | Purpose | Auditable |
|-------|---------|-----------|
| `micro_grids` | 1,687 grid cells in Clifton | ✅ Yes |
| `businesses` | 260 real businesses (77 gyms, 183 cafes) | ✅ Yes |
| `recommendations` | User queries and AI responses | ✅ Yes |
| `user_feedback` | User ratings and comments | ✅ Yes |

**All API calls, recommendations, and user interactions are logged in PostgreSQL!**

---

## 📝 Final Submission Package

### URLs to Submit:

```
Live Application: https://your-app.vercel.app
Backend API: https://your-backend.onrender.com
API Documentation: https://your-backend.onrender.com/docs
```

### Features to Demonstrate:

1. **AI-Powered Analysis:**
   - Click "AI-Powered Analysis" on landing page
   - Select location on map
   - Toggle between "Fast" and "AI Powered" modes
   - Show detailed recommendations with reasoning

2. **Auditable Data:**
   - Show database connection in Render
   - Demonstrate stored business data
   - Show recommendation history

3. **Real Google Data:**
   - All 260 businesses are real from Google Places API
   - No synthetic/fake data
   - 100m high-resolution micro-grids

---

## 🆘 Quick Troubleshooting

### Backend not starting?
```bash
# Check logs in Render Dashboard
# Verify environment variables are set
# Check DATABASE_URL is auto-configured
```

### Frontend blank page?
```bash
# Check browser console (F12)
# Verify env.js exists with API key
# Check CORS settings in backend
```

### Map not loading?
```bash
# Verify GOOGLE_MAPS_API_KEY in env.js
# Check Google Cloud Console for API restrictions
# Enable "Maps JavaScript API" in Google Cloud
```

### API calls failing?
```bash
# Check backend is "Live" in Render
# Test health endpoint in browser
# Verify kIsProduction = true in constants.dart
```

---

## ⏱️ Deployment Timeline

| Step | Time | Status |
|------|------|--------|
| Get API keys | 5 min | ✅ Already have |
| Deploy backend (Render) | 10 min | ⏳ To do |
| Configure environment vars | 2 min | ⏳ To do |
| Build Flutter web | 5 min | ⏳ To do |
| Deploy frontend (Vercel) | 5 min | ⏳ To do |
| Test & verify | 10 min | ⏳ To do |
| **Total** | **~30-40 min** | |

---

## 🎯 Next Steps

1. [ ] Deploy backend on Render (Part 1)
2. [ ] Get backend URL and test it
3. [ ] Update frontend constants.dart with production URL
4. [ ] Build Flutter web app
5. [ ] Deploy to Vercel (Part 2)
6. [ ] Test live application
7. [ ] Verify data storage
8. [ ] Submit URLs

---

## 💡 Pro Tips

1. **Free Tier Limits:**
   - Render backend sleeps after 15 min inactivity (first request slow)
   - Keep it warm by pinging health endpoint every 10 minutes
   - Or upgrade to paid tier ($7/month) for always-on

2. **Database Backups:**
   - Render provides automatic backups
   - Download manual backup before submission

3. **Monitoring:**
   - Check Render logs for errors
   - Monitor Vercel analytics for usage
   - Track Google API quota in Cloud Console

---

**Ready to deploy? Start with PART 1! 🚀**

If you encounter any issues during deployment, check the troubleshooting section or refer to the full `ADMIN_DEPLOYMENT_GUIDE.md`.

Good luck with your submission! 🎓
