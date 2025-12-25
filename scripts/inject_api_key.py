#!/usr/bin/env python3
"""
Inject Google Maps API Key into Flutter web build

This script replaces the placeholder in index.html with the actual API key
from environment variables during the build/deployment process.

Usage:
    python scripts/inject_api_key.py

The script reads GOOGLE_PLACES_API_KEY from .env file and injects it into
the built index.html file.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
root_dir = Path(__file__).parent.parent
env_path = root_dir / ".env"

if not env_path.exists():
    print("❌ Error: .env file not found!")
    print(f"Expected location: {env_path}")
    sys.exit(1)

load_dotenv(env_path)

# Get API key
api_key = os.getenv("GOOGLE_PLACES_API_KEY")
if not api_key:
    print("❌ Error: GOOGLE_PLACES_API_KEY not found in .env file!")
    sys.exit(1)

# Path to index.html in build directory
index_html_path = root_dir / "frontend" / "build" / "web" / "index.html"

if not index_html_path.exists():
    print("❌ Error: Built index.html not found!")
    print(f"Expected location: {index_html_path}")
    print("\nPlease run 'flutter build web' first from the frontend directory.")
    sys.exit(1)

# Read the file
with open(index_html_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace placeholder with actual API key
if "GOOGLE_MAPS_API_KEY_PLACEHOLDER" not in content:
    print("⚠️  Warning: Placeholder not found in index.html")
    print("The API key may have already been injected or the file format changed.")
    sys.exit(1)

updated_content = content.replace("GOOGLE_MAPS_API_KEY_PLACEHOLDER", api_key)

# Write back
with open(index_html_path, "w", encoding="utf-8") as f:
    f.write(updated_content)

print("✅ Successfully injected Google Maps API key into index.html")
print(f"📁 File: {index_html_path}")
print("\n⚠️  IMPORTANT: Never commit the build/ directory to version control!")
