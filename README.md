# Bulk Quotes Generator

Generate quote images from a **single Google Sheet** using an interactive dashboard.

## Requirements

- Python 3.10+
- Google Service Account access to the Google Sheet

## Setup

1. **Clone the repo and open the folder**

2. **Add Google credentials**

Place your service account file here:

- `credentials.json`

3. **Share your Google Sheet with the service account email**

In Google Sheets → Share → add the service account email from `credentials.json`.

4. **Configure the sheet**

Open `references/config.json` and set:

- `google_sheets.sheet_url`: your Google Sheet URL
- `google_sheets.database_worksheet`: `Database`

Your header row must be:

`S#  LENGTH  CATEGORY  AUTHOR  QUOTE  TAGS  IMAGE  PREVIEW_LINK  STATUS`

Notes:
- `CATEGORY` is used as the **Topic** list.
- `AUTHOR` is read from column **D**.
- `IMAGE` is read from column **G** (used for the top-left avatar when available).
- `PREVIEW_LINK` (column **H**) will be written as a clickable **Preview Image** link.
- `STATUS` (column **I**) will be set to **Done/Skip**.

## Install dependencies

Run:

```bash
python scripts/setup_environment.py
```

## Run the Dashboard

Start the app:

```bash
python scripts/dashboard.py
```

Open:

- http://127.0.0.1:8000

## How to Use

1. Select a **Topic** (from `CATEGORY`)
2. Select an **Author** (dropdown)
3. Click **Preview** to see the preview image
4. Click **Generate** to create the final image
5. For bulk generation, set the count and click **Generate Bulk** (it will generate different quotes)

## Preview Link Output (Local)

When sheet write-back is enabled, the tool writes local preview links like:

- `http://127.0.0.1:8000/generated/...`
t
(These are meant for **local use** while the dashboard is running.)
