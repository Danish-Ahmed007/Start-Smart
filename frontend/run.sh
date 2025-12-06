#!/usr/bin/env bash
set -euo pipefail

# Simple helper to run the Flutter app inside flutter_application/
cd "$(dirname "$0")/../flutter_application" || exit 1

echo "Running flutter pub get..."
flutter pub get

echo "Starting flutter run... (press q to quit)"
flutter run
