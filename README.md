# Bulk Quotes Generator (Final)

This is the final version of the project.

It includes:
- Web Dashboard (Collect → Review → Generate → Post)
- Bulk quote image generation
- Google Sheets integration (reads your **Database** tab)
- Optional AI prompt/background support
- Social posting placeholders (for future)

## 1) Install (one time)

1. Install Python 3.10+ (recommended)
2. Open a terminal in the project folder
3. Install requirements:

```bash
pip install -r requirements.txt
```

## 2) Google setup (one time)

1. Put your Google service account file here:

- `credentials.json` (project root)

2. Share your Google Sheet with the **service account email** (inside `credentials.json`).

## 3) Configure the Sheet URL

Set the sheet URL using an environment variable.

### PowerShell (recommended)

```powershell
$env:GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/XXXX/edit"
```

### CMD

```cmd
set GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/XXXX/edit
```

## 4) Run the dashboard

Run:

```bash
python app.py
```

Open:
- http://localhost:8000

## 5) Smoke test

Run:

```bash
python tests/test_setup.py
```

Notes:
- If Sheets connection fails, it usually means your `credentials.json` is wrong OR you did not share the sheet with the service account.
- Image generation test should still work.

## Project structure

- `app.py` (main web app)
- `templates/index.html` (dashboard UI)
- `scripts/` (core logic)
- `assets/` (fonts + backgrounds)
- `Watermarks/` (your watermark PNG files)
- `Generated_Images/` (output)
- `tests/` (smoke tests)
