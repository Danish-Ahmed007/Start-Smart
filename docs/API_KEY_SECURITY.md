# Secure API Key Management for Production Deployment

## Overview

This document explains how StartSmart securely manages the Google Maps API key for production deployment without exposing it in version control.

## Problem

- **Issue**: API keys should never be committed to Git
- **Challenge**: Flutter web requires the Google Maps API key in `index.html` to load the Maps JavaScript library
- **Solution**: Use placeholder replacement during build time

## Implementation

### 1. Development Environment

For local development, use the actual API key temporarily:

```bash
# In frontend/web/index.html (for development only)
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_DEV_KEY&libraries=places"></script>
```

**⚠️ NEVER commit this file with the actual key!**

### 2. Version Control

In Git, the `index.html` file contains a placeholder:

```html
<!-- frontend/web/index.html -->
<script src="https://maps.googleapis.com/maps/api/js?key=GOOGLE_MAPS_API_KEY_PLACEHOLDER&libraries=places"></script>
```

This placeholder is safe to commit.

### 3. Build Process

When building for production:

```powershell
# Windows
.\scripts\build_frontend.ps1

# Linux/Mac
./scripts/build_frontend.sh
```

This script:
1. Runs `flutter build web --release`
2. Reads the API key from `.env` file
3. Replaces `GOOGLE_MAPS_API_KEY_PLACEHOLDER` with the actual key in `build/web/index.html`
4. The build output is ready for deployment

### 4. Manual Build (Alternative)

If you prefer manual steps:

```powershell
# Step 1: Build Flutter app
cd frontend
flutter build web --release

# Step 2: Inject API key
cd ..
python scripts/inject_api_key.py
```

## Backend API Proxy (Additional Security Layer)

We've also implemented a backend proxy for Google Maps API calls:

### Endpoints

```
GET /api/v1/maps/geocode
GET /api/v1/maps/places/nearbysearch
GET /api/v1/maps/places/details
```

### Usage Example

Instead of calling Google Maps API directly from Flutter:

```dart
// ❌ Old way (exposes API key)
final response = await http.get(
  'https://maps.googleapis.com/maps/api/geocode/json?address=$address&key=$apiKey'
);

// ✅ New way (secure)
final response = await http.get(
  'http://your-backend.com/api/v1/maps/geocode?address=$address'
);
```

## Deployment Checklist

### Frontend Deployment

- [ ] Build using `build_frontend.ps1` or `build_frontend.sh`
- [ ] Verify API key is injected in `frontend/build/web/index.html`
- [ ] Deploy `frontend/build/web/` directory to hosting (Netlify, Vercel, Firebase, etc.)
- [ ] **Never commit the `build/` directory**

### Backend Deployment

- [ ] Ensure `.env` file exists on server with `GOOGLE_PLACES_API_KEY`
- [ ] Backend API is accessible from frontend domain
- [ ] CORS is configured correctly

### Google Cloud Console

- [ ] Add domain restrictions to your API key
- [ ] Add HTTP referrer restrictions
- [ ] Set up API quotas and billing alerts

## Security Best Practices

1. **API Key Restrictions**
   - In Google Cloud Console, restrict the API key to:
     - Specific domains (your production domain)
     - Specific APIs (Maps JavaScript API, Places API, Geocoding API)

2. **Environment Separation**
   - Use different API keys for development and production
   - Never use production keys in development

3. **Git Ignore**
   - `.env` files are in `.gitignore`
   - `frontend/build/` is in `.gitignore`
   - Never force-add these files

4. **Backend Proxy**
   - Use backend proxy endpoints when possible
   - Implement rate limiting on proxy endpoints
   - Log and monitor API usage

## File Structure

```
Start-Smart/
├── .env                          # Contains GOOGLE_PLACES_API_KEY (gitignored)
├── .gitignore                    # Ensures .env and build/ are not committed
├── frontend/
│   ├── web/
│   │   └── index.html           # Contains placeholder in Git
│   └── build/                   # Build output (gitignored)
│       └── web/
│           └── index.html       # Contains actual key after build
├── backend/
│   └── api/
│       └── routers/
│           └── maps_proxy.py    # Proxy endpoints for API calls
└── scripts/
    ├── inject_api_key.py        # Injects API key during build
    ├── build_frontend.ps1       # Windows build script
    └── build_frontend.sh        # Linux/Mac build script
```

## Troubleshooting

### "API key not configured" error

- Check `.env` file exists in project root
- Verify `GOOGLE_PLACES_API_KEY=your_key_here` is in `.env`
- Restart backend server after .env changes

### Maps not loading in production

- Verify API key was injected (check deployed `index.html`)
- Check browser console for API key errors
- Verify domain is allowed in Google Cloud Console

### Build script fails

- Ensure Python is installed
- Install dependencies: `pip install python-dotenv`
- Verify `.env` file exists
- Check Flutter is installed: `flutter --version`

## For CI/CD Pipelines

Add the API key as a secret in your CI/CD platform:

### GitHub Actions

```yaml
- name: Inject API Key
  env:
    GOOGLE_PLACES_API_KEY: ${{ secrets.GOOGLE_MAPS_API_KEY }}
  run: |
    echo "GOOGLE_PLACES_API_KEY=$GOOGLE_PLACES_API_KEY" > .env
    python scripts/inject_api_key.py
```

### GitLab CI

```yaml
deploy:
  script:
    - echo "GOOGLE_PLACES_API_KEY=$GOOGLE_MAPS_API_KEY" > .env
    - python scripts/inject_api_key.py
```

## Summary

✅ **What's Safe to Commit:**
- `frontend/web/index.html` (with placeholder)
- All scripts
- `.env.example` (template without real keys)

❌ **What Should NEVER be Committed:**
- `.env` file
- `frontend/build/` directory
- Any file with actual API keys

🔒 **Additional Security:**
- Use backend proxy for API calls when possible
- Implement domain restrictions in Google Cloud Console
- Monitor API usage and set up alerts
