# Frontend (wrapper)

This folder is a lightweight wrapper that points to the real Flutter app located at `flutter_application/`.

Purpose:
- Provide a top-level `frontend/` entry similar to the repo's `backend/` folder without moving files.
- Make it convenient to run the Flutter app from a single place.

How to run the app (from repo root):

```bash
cd frontend
./run.sh
```

What the script does:
- Runs `flutter pub get` and `flutter run` inside `flutter_application/`.

Notes:
- No code was copied. The canonical Flutter project remains in `flutter_application/`.
- If you want the folder renamed or a full move instead, run `git mv flutter_application frontend` and update references.
