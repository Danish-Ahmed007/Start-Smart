#!/bin/bash
# Build and Deploy Script for StartSmart Frontend
# This script builds the Flutter web app and injects the API key

set -e  # Exit on error

echo "🚀 Starting StartSmart Frontend Build Process..."

# Navigate to frontend directory
cd "$(dirname "$0")/../frontend"

echo ""
echo "📦 Step 1: Building Flutter web app..."
flutter build web --release

echo ""
echo "🔑 Step 2: Injecting Google Maps API key..."
cd ..
python scripts/inject_api_key.py

echo ""
echo "✅ Build complete!"
echo "📁 Build output: frontend/build/web/"
echo ""
echo "🌐 To deploy:"
echo "   - Upload frontend/build/web/ to your hosting provider"
echo "   - Make sure backend is deployed with correct .env configuration"
echo ""
echo "⚠️  Remember: Never commit the build/ directory!"
