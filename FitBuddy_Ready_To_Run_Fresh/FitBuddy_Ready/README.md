# FitBuddy - reliable Windows starter

## Run it
1. Extract the ZIP.
2. Open the extracted `FitBuddy_Ready` folder.
3. Double-click `run_windows.bat`.
4. Wait for `Uvicorn running on http://127.0.0.1:8000`.
5. Open that URL in your browser. Keep the black terminal window open.

The app runs in demo mode without an API key. To enable Gemini, add your key to `.env` as `GOOGLE_API_KEY=...` and restart.

## Manual setup
In PowerShell opened in this folder:
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --reload
```
