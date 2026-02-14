#!/usr/bin/env python3
"""
QuoteMaster v2.0 — Unified Dashboard
Scrape → Review → Generate → Post

Drop this file into your Bulk-Quotes-Image-Generator root folder.
Then run:  python app.py
Open:      http://localhost:8000

What changed from old dashboard.py:
  • 4-stage pipeline  (Collect / Review / Generate / Post-placeholder)
  • Scraper built-in  (no more separate terminal)
  • Review stage      (approve/reject CSV quotes before pushing to Sheet)
  • Same scripts/     folder — nothing inside it was changed
"""

import os, sys, json, uuid, time, threading, csv, re
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

try:
    from googletrans import Translator
    _TRANSLATE_OK = True
except Exception:
    Translator = None
    _TRANSLATE_OK = False

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.resolve()
SCRIPTS_DIR = BASE_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# ── Lazy-import existing scripts (graceful if creds missing) ──────────────────
try:
    from sheet_reader import SheetReader
    SHEETS_OK = True
except Exception as e:
    print(f"[WARN] sheet_reader: {e}")
    SHEETS_OK = False
    SheetReader = None

try:
    from image_generator import QuoteImageGenerator
    IMAGE_GEN_OK = True
except Exception as e:
    print(f"[WARN] image_generator: {e}")
    IMAGE_GEN_OK = False
    QuoteImageGenerator = None

try:
    from google_drive_uploader import DriveUploader
    DRIVE_OK = True
except Exception:
    DRIVE_OK = False
    DriveUploader = None

try:
    from app_version import APP_VERSION
except Exception:
    APP_VERSION = "1.100.1.1"

APP_VERSION_UNIFIED = "2.0.0"

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates")
app.config["JSON_SORT_KEYS"] = False

# ── Singleton components ──────────────────────────────────────────────────────
_sheet = None
_gen   = None
_drive = None

def get_sheet() -> "SheetReader | None":
    global _sheet
    if _sheet is None and SHEETS_OK:
        try:
            _sheet = SheetReader()
            _sheet.connect()
        except Exception as e:
            print(f"[WARN] Sheet connect: {e}")
    return _sheet

def get_gen() -> "QuoteImageGenerator | None":
    global _gen
    if _gen is None and IMAGE_GEN_OK:
        try:
            _gen = QuoteImageGenerator(
                output_dir=str(BASE_DIR / "Generated_Images"),
                watermark_dir=str(BASE_DIR / "Watermarks"),
            )
        except Exception as e:
            print(f"[WARN] ImageGen init: {e}")
    return _gen

def get_drive() -> "DriveUploader | None":
    global _drive
    if _drive is None and DRIVE_OK:
        try:
            _drive = DriveUploader()
        except Exception:
            pass
    return _drive


def _sanitize_quote_author(quote: str, author: str) -> str:
    q = str(quote or '').strip()
    a = str(author or '').strip()
    if not q or not a:
        return q
    q_cmp = re.sub(r"\s+", " ", q).strip().lower()
    a_cmp = re.sub(r"\s+", " ", a).strip().lower()

    # Common patterns where author is appended at end of quote text
    patterns = [
        rf"{re.escape(a_cmp)}$",
        rf"[-—–]\s*{re.escape(a_cmp)}$",
        rf"\"\s*{re.escape(a_cmp)}$",
        rf"\"\s*[-—–]\s*{re.escape(a_cmp)}$",
    ]
    for p in patterns:
        if re.search(p, q_cmp, flags=re.IGNORECASE):
            q = re.sub(p, "", q, flags=re.IGNORECASE).rstrip(" \t\r\n\"-—–")
            break
    return q.strip()

# ── Job tracker ───────────────────────────────────────────────────────────────
JOBS: dict[str, dict] = {}

# ── Scrape state ──────────────────────────────────────────────────────────────
SCRAPE_LOG    = []
SCRAPE_ACTIVE = threading.Event()
EXPORT_DIR    = BASE_DIR / "Export"
EXPORT_DIR.mkdir(exist_ok=True)

# ── Goodreads categories ──────────────────────────────────────────────────────
CATEGORIES = [
    (1,  "Love",          "https://www.goodreads.com/quotes/tag/love"),
    (2,  "Life",          "https://www.goodreads.com/quotes/tag/life"),
    (3,  "Inspirational", "https://www.goodreads.com/quotes/tag/inspirational"),
    (4,  "Humor",         "https://www.goodreads.com/quotes/tag/humor"),
    (5,  "Philosophy",    "https://www.goodreads.com/quotes/tag/philosophy"),
    (6,  "God",           "https://www.goodreads.com/quotes/tag/god"),
    (7,  "Truth",         "https://www.goodreads.com/quotes/tag/truth"),
    (8,  "Wisdom",        "https://www.goodreads.com/quotes/tag/wisdom"),
    (9,  "Romance",       "https://www.goodreads.com/quotes/tag/romance"),
    (10, "Poetry",        "https://www.goodreads.com/quotes/tag/poetry"),
    (11, "Life Lessons",  "https://www.goodreads.com/quotes/tag/life-lessons"),
    (12, "Death",         "https://www.goodreads.com/quotes/tag/death"),
    (13, "Happiness",     "https://www.goodreads.com/quotes/tag/happiness"),
    (14, "Hope",          "https://www.goodreads.com/quotes/tag/hope"),
    (15, "Faith",         "https://www.goodreads.com/quotes/tag/faith"),
    (16, "Inspiration",   "https://www.goodreads.com/quotes/tag/inspiration"),
    (17, "Spirituality",  "https://www.goodreads.com/quotes/tag/spirituality"),
    (18, "Relationships", "https://www.goodreads.com/quotes/tag/relationships"),
    (19, "Motivational",  "https://www.goodreads.com/quotes/tag/motivational"),
    (20, "Religion",      "https://www.goodreads.com/quotes/tag/religion"),
    (21, "Writing",       "https://www.goodreads.com/quotes/tag/writing"),
    (22, "Success",       "https://www.goodreads.com/quotes/tag/success"),
    (23, "Travel",        "https://www.goodreads.com/quotes/tag/travel"),
    (24, "Motivation",    "https://www.goodreads.com/quotes/tag/motivation"),
    (25, "Time",          "https://www.goodreads.com/quotes/tag/time"),
]

CSV_HEADER = ["SNO","THUMB","CATEGORY","AUTHOR","QUOTE","TRANSLATE","TAGS","LIKES","IMAGE","TOTAL"]

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN PAGE
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    styles = [
        {"id":"elegant",          "label":"Elegant",       "icon":"✨"},
        {"id":"modern",           "label":"Modern",        "icon":"🔷"},
        {"id":"neon",             "label":"Neon",          "icon":"🧿"},
        {"id":"vintage",          "label":"Vintage",       "icon":"📜"},
        {"id":"minimalist_dark",  "label":"Dark Minimal",  "icon":"🌑"},
        {"id":"creative_split",   "label":"Split",         "icon":"🎭"},
        {"id":"geometric",        "label":"Geometric",     "icon":"🔺"},
        {"id":"artistic",         "label":"Artistic",      "icon":"🎨"},
        {"id":"gradient_sunset",  "label":"Sunset",        "icon":"🌅"},
        {"id":"nature",           "label":"Nature",        "icon":"🌿"},
        {"id":"ocean",            "label":"Ocean",         "icon":"🌊"},
        {"id":"cosmic",           "label":"Cosmic",        "icon":"🌌"},
    ]
    return render_template("index.html",
        app_version = APP_VERSION_UNIFIED,
        categories  = CATEGORIES,
        styles      = styles,
    )

# ══════════════════════════════════════════════════════════════════════════════
#  STATS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/stats")
def api_stats():
    gen_dir = BASE_DIR / "Generated_Images"
    imgs = len(list(gen_dir.glob("*.png"))) + len(list(gen_dir.glob("*.jpg"))) \
           if gen_dir.exists() else 0
    csv_count = len(list(EXPORT_DIR.glob("*.csv"))) if EXPORT_DIR.exists() else 0

    topics = []
    sr = get_sheet()
    if sr:
        try: topics = sr.get_all_topics()
        except Exception: pass

    return jsonify({
        "topics":    len(topics),
        "images":    imgs,
        "csvs":      csv_count,
        "sheets_ok": SHEETS_OK and bool(sr and sr.spreadsheet),
        "imggen_ok": IMAGE_GEN_OK,
        "version":   APP_VERSION_UNIFIED,
    })

# ══════════════════════════════════════════════════════════════════════════════
#  STAGE 1 — SCRAPER
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/scrape/start", methods=["POST"])
def api_scrape_start():
    if SCRAPE_ACTIVE.is_set():
        return jsonify({"ok": False, "error": "Scrape already running"}), 409

    data       = request.get_json() or {}
    cat_ids    = [int(x) for x in (data.get("categories") or [])]
    page_limit = int(data.get("page_limit") or 1)
    selected   = [c for c in CATEGORIES if c[0] in cat_ids] if cat_ids else CATEGORIES

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status":"running","progress":0.0,"message":"Starting…","result":None}

    def _run():
        SCRAPE_ACTIVE.set()
        SCRAPE_LOG.clear()
        grand_total = 0
        total = len(selected)

        try:
            import requests as req_lib, random as rlib, time as tlib
            from bs4 import BeautifulSoup

            UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
            seen: set[str] = set()
            session = req_lib.Session()

            def _clean(t):
                if not t: return ""
                t = re.split(r'\s*[-—]+\s*', t, 1)[0]
                for a, b in [
                    ("\u201c", '"'),
                    ("\u201d", '"'),
                    ("\u2018", "'"),
                    ("\u2019", "'"),
                ]:
                    t = t.replace(a, b)
                t = t.encode('ascii','ignore').decode().strip().strip('"\'')
                return ' '.join(t.split())

            def _auth(t):
                if not t: return "Unknown"
                t = re.sub(r'[=,\.\-]+',' ', t.strip())
                return ' '.join(t.split()) or "Unknown"

            for i, (num, name, url) in enumerate(selected):
                JOBS[job_id]["message"]  = f"Scraping: {name} ({i+1}/{total})"
                JOBS[job_id]["progress"] = i / total
                cat_added = 0
                csv_path  = EXPORT_DIR / f"{name}.csv"

                existing: set[str] = set()
                last_sno = 0
                if csv_path.exists():
                    with open(csv_path, newline='', encoding='utf-8') as f:
                        for row in csv.DictReader(f):
                            q = (row.get("QUOTE") or "").strip().lower()
                            if q: existing.add(q)
                            try: last_sno = max(last_sno, int(row.get("SNO") or 0))
                            except Exception: pass

                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if f.tell() == 0:
                        writer.writerow(CSV_HEADER)

                    cur, pages = url, 0
                    while cur and (page_limit == 0 or pages < page_limit):
                        tlib.sleep(rlib.uniform(1.2, 2.6))
                        try:
                            r = session.get(cur, headers={"User-Agent": UA}, timeout=30)
                            r.raise_for_status()
                        except Exception as e:
                            SCRAPE_LOG.append({"type":"warn","msg":f"{name} pg{pages+1}: {e}"})
                            break

                        soup = BeautifulSoup(r.text, "lxml")
                        for div in soup.find_all("div", class_="quote"):
                            try:
                                qt = div.find("div", class_="quoteText")
                                if not qt: continue
                                q = _clean(qt.get_text(strip=True))
                                if not q or len(q) < 50: continue
                                key = q.lower()
                                if key in existing or key in seen: continue
                                a_sp  = div.find("span", class_="authorOrTitle")
                                auth  = _auth(a_sp.get_text(strip=True) if a_sp else "")
                                td    = div.find("div", class_="greyText")
                                tags  = (td.get_text(strip=True) if td else "").replace("tags:","").strip()
                                ii    = div.find("img")
                                img   = ii.get("src","") if ii else ""
                                ld    = div.find("div", class_="right")
                                likes = 0
                                if ld:
                                    lt = ld.get_text(strip=True)
                                    if "likes" in lt:
                                        ln = lt.split("likes")[0].strip().replace(",","")
                                        likes = int(ln) if ln.isdigit() else 0
                                existing.add(key); seen.add(key)
                                last_sno += 1; cat_added += 1; grand_total += 1
                                writer.writerow([last_sno,"",name,auth,q,"",tags,likes,img,len(q)])
                            except Exception: continue

                        pages += 1
                        nxt = soup.find("a", class_="next_page")
                        cur = f"https://www.goodreads.com{nxt['href']}" if nxt else None

                SCRAPE_LOG.append({"type":"ok","msg":f"✅ {name}: {cat_added} new quotes"})

            JOBS[job_id].update({"status":"done","progress":1.0,
                "message":f"Done — {grand_total} quotes saved",
                "result":{"total": grand_total}})
        except Exception as e:
            JOBS[job_id].update({"status":"error","message":str(e),"result":None})
        finally:
            SCRAPE_ACTIVE.clear()

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"ok": True, "job_id": job_id})


@app.route("/api/scrape/log")
def api_scrape_log():
    return jsonify({"log": list(SCRAPE_LOG), "running": SCRAPE_ACTIVE.is_set()})

# ══════════════════════════════════════════════════════════════════════════════
#  STAGE 2 — REVIEW  (local CSV files)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/review/categories")
def api_review_cats():
    cats = []
    if EXPORT_DIR.exists():
        for f in sorted(EXPORT_DIR.glob("*.csv")):
            count = 0
            try:
                with open(f, newline='', encoding='utf-8') as fh:
                    count = max(0, sum(1 for _ in fh) - 1)
            except Exception:
                pass
            cats.append({"name": f.stem, "count": count})
    return jsonify({"categories": cats})


@app.route("/api/review/quotes")
def api_review_quotes():
    cat    = request.args.get("cat","")
    offset = int(request.args.get("offset", 0))
    limit  = int(request.args.get("limit",  40))

    f = EXPORT_DIR / f"{cat}.csv"
    if not f.exists():
        return jsonify({"quotes":[], "total":0})

    rows = []
    try:
        with open(f, newline='', encoding='utf-8') as fh:
            rows = list(csv.DictReader(fh))
    except Exception:
        pass

    page   = rows[offset: offset + limit]
    quotes = [{"quote":r.get("QUOTE",""), "translate":r.get("TRANSLATE",""), "author":r.get("AUTHOR",""),
               "category":r.get("CATEGORY",""), "tags":r.get("TAGS",""),
               "image":r.get("IMAGE",""), "length":r.get("TOTAL",""),
               "likes":r.get("LIKES","")} for r in page]
    return jsonify({"quotes": quotes, "total": len(rows)})


@app.route("/api/review/push", methods=["POST"])
def api_review_push():
    """Push approved quotes into Google Sheets Database tab."""
    data   = request.get_json() or {}
    quotes = data.get("quotes", [])
    if not quotes:
        return jsonify({"ok": False, "error": "No quotes provided"})

    sr = get_sheet()
    if not sr or not sr.spreadsheet:
        return jsonify({"ok": False, "error": "Not connected to Google Sheets. Check credentials.json"})

    try:
        ws = sr.spreadsheet.worksheet("Database")
        existing_keys = set(
            str(r.get("QUOTE","")).strip().lower()
            for r in ws.get_all_records()
        )

        to_add, skipped = [], 0
        for q in quotes:
            key = str(q.get("quote","")).strip().lower()
            if not key or key in existing_keys:
                skipped += 1
                continue
            existing_keys.add(key)
            to_add.append([
                "", len(q.get("quote","")),
                q.get("category",""), q.get("author",""),
                q.get("quote",""),    q.get("translate",""),
                q.get("tags",""),     q.get("image",""),
                "", "", "", "", "Pending", "", ""
            ])

        if to_add:
            ws.append_rows(to_add, value_input_option="USER_ENTERED")

        return jsonify({"ok": True, "pushed": len(to_add), "skipped": skipped})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ══════════════════════════════════════════════════════════════════════════════
#  STAGE 3 — GENERATE  (uses existing scripts unchanged)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/topics")
def api_topics():
    sr, topics = get_sheet(), []
    if sr:
        try: topics = sr.get_all_topics()
        except Exception: pass
    return jsonify({"topics": topics})


@app.route("/api/quotes/<topic>")
def api_quotes(topic):
    sr, quotes = get_sheet(), []
    if sr:
        try: quotes = sr.get_quotes_by_topic(topic)
        except Exception: pass
    return jsonify({"quotes": quotes})


@app.route("/api/translate", methods=["POST"])
def api_translate():
    data = request.get_json() or {}
    text = str(data.get("text") or "")
    src = str(data.get("src") or "en")
    dest = str(data.get("dest") or "ur")
    row = data.get("row")

    if not text.strip():
        return jsonify({"ok": False, "error": "Empty text"}), 400
    if not _TRANSLATE_OK:
        return jsonify({"ok": False, "error": "Translation not available. Install requirements."}), 503

    try:
        t = Translator()
        res = t.translate(text, src=src, dest=dest)
        translated = str(getattr(res, 'text', '') or '')

        saved = False
        save_error = None
        if row not in (None, ""):
            sr = get_sheet()
            if not sr or not sr.spreadsheet:
                save_error = "Not connected to Google Sheets"
            else:
                try:
                    saved = bool(sr.write_translation(int(row), translated))
                    if not saved:
                        save_error = "Sheet write failed"
                except Exception as e:
                    saved = False
                    save_error = str(e)

        return jsonify({"ok": True, "translated": translated, "saved": saved, "save_error": save_error})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/remaining/<topic>")
def api_remaining(topic):
    sr = get_sheet()
    if sr:
        try: return jsonify(sr.get_remaining_counts(topic))
        except Exception: pass
    return jsonify({"topic_total": 0, "authors": {}})


@app.route("/api/fonts")
def api_fonts():
    g = get_gen()
    fonts = []
    if g:
        try: fonts = g.get_available_fonts()
        except Exception: pass
    return jsonify({"fonts": fonts})


@app.route("/api/job/start", methods=["POST"])
def api_job_start():
    data    = request.get_json() or {}
    kind    = str(data.get("kind","")).strip().lower()
    payload = data.get("payload") or {}
    job_id  = uuid.uuid4().hex
    JOBS[job_id] = {"status":"running","progress":0.0,"message":"Queued","result":None}

    try:
        if kind == "single":
            JOBS[job_id]["message"]  = "Rendering image…"
            JOBS[job_id]["progress"] = 0.10
            result = _single(payload, job_id)
        elif kind == "bulk":
            JOBS[job_id]["message"]  = "Preparing bulk…"
            JOBS[job_id]["progress"] = 0.05
            result = _bulk(payload, job_id)
        else:
            raise ValueError(f"Unknown job kind: {kind}")
        JOBS[job_id].update({"status":"done","progress":1.0,"message":"Done","result":result})
    except Exception as e:
        JOBS[job_id].update({"status":"error","message":str(e),"result":None})

    return jsonify({"job_id": job_id})


@app.route("/api/job/status/<job_id>")
def api_job_status(job_id):
    s = JOBS.get(job_id)
    if not s:
        return jsonify({"status":"error","error":"Unknown job"}), 404
    return jsonify(s)


def _single(data: dict, job_id: str) -> dict:
    g = get_gen()
    if not g: raise RuntimeError("Image generator not available — check Pillow install")

    JOBS[job_id]["progress"] = 0.25
    JOBS[job_id]["message"]  = "Rendering…"

    language = str(data.get("language") or "en").strip().lower()
    font_en = data.get("font_name_en") or data.get("font_name") or None
    font_ur = data.get("font_name_ur") or data.get("font_name") or None
    font_name = font_ur if language in ("ur", "urdu") else font_en

    quote_src = data.get("quote", "")
    if language in ("ur", "urdu"):
        quote_src = data.get("translate") or data.get("quote", "")

    quote_src = _sanitize_quote_author(quote_src, str(data.get("author", "")))

    path = g.generate(
        quote             = quote_src,
        author            = data.get("author",""),
        style             = data.get("style","elegant"),
        category          = data.get("category",""),
        author_image      = str(data.get("author_image") or ""),
        watermark_mode    = "corner",
        watermark_opacity = float(data.get("watermark_opacity") or 0.7),
        watermark_blend   = str(data.get("watermark_blend") or "normal"),
        avatar_position   = str(data.get("avatar_position") or "top-left"),
        font_name         = font_name,
        quote_font_size   = int(data.get("quote_font_size") or 52),
        author_font_size  = int(data.get("author_font_size") or 30),
        watermark_size_percent = float(data.get("watermark_size_percent") or 0.15),
        watermark_position= "bottom-right",
        background_mode   = str(data.get("background_mode") or "none"),
        ai_model          = data.get("ai_model") or None,
        hf_api_key        = data.get("hf_api_key") or None,
        language          = language,
    )

    JOBS[job_id]["progress"] = 0.65
    JOBS[job_id]["message"]  = "Writing to Sheet…"

    sr = get_sheet()
    upload_result = "Saved locally"
    row   = data.get("row")
    topic = data.get("topic","")
    if sr and row and topic:
        try:
            abs_url = f"http://localhost:8000/generated/{Path(path).name}"
            ok = sr.write_back(str(topic), int(row), abs_url)
            with __import__("PIL").Image.open(path) as im:
                dims = f"{im.width}x{im.height}"
            sr.write_generation_meta(int(row), dims, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            upload_result = "✅ Written to Sheet" if ok else "⚠️ Sheet write failed"
        except Exception as e:
            upload_result = f"Sheet error: {e}"

    drive_link = None
    drive_error = None
    if bool(data.get("upload_to_drive")):
        JOBS[job_id]["progress"] = 0.82
        JOBS[job_id]["message"]  = "Uploading to Google Drive…"
        du = get_drive()
        if not du:
            drive_error = "Drive uploader not available"
        else:
            try:
                drive_link = du.upload_image(path, topic=topic or None)
                if not drive_link:
                    drive_error = "Drive upload returned no link"
            except Exception as e:
                drive_error = str(e)

    JOBS[job_id]["progress"] = 0.90
    return {
        "success":       True,
        "image_path":    path,
        "public_url":    f"/generated/{Path(path).name}",
        "upload_result": upload_result,
        "drive_link":    drive_link,
        "drive_error":   drive_error,
    }


def _bulk(data: dict, job_id: str) -> dict:
    g  = get_gen()
    sr = get_sheet()
    if not g: raise RuntimeError("Image generator not available")

    topic  = data.get("topic","")
    count  = int(data.get("count") or 5)
    quotes = sr.get_quotes_by_topic(topic) if sr else []

    import random
    selected = random.sample(quotes, min(count, len(quotes))) if quotes else []
    total    = max(1, len(selected))
    done     = 0

    language = str(data.get("language") or "en").strip().lower()
    font_en = data.get("font_name_en") or data.get("font_name") or None
    font_ur = data.get("font_name_ur") or data.get("font_name") or None
    font_name = font_ur if language in ("ur", "urdu") else font_en

    for q in selected:
        JOBS[job_id]["message"]  = f"Generating {done+1}/{total}…"
        JOBS[job_id]["progress"] = 0.10 + 0.80 * (done / total)
        try:
            quote_src = q.get("quote", "")
            if language in ("ur", "urdu"):
                quote_src = q.get("translate") or q.get("quote", "")
            quote_src = _sanitize_quote_author(quote_src, str(q.get("author", "")))

            path = g.generate(
                quote             = quote_src,
                author            = q.get("author",""),
                style             = data.get("style","elegant"),
                category          = q.get("category",""),
                author_image      = str(q.get("author_image") or q.get("image") or ""),
                watermark_mode    = "corner",
                watermark_opacity = float(data.get("watermark_opacity") or 0.7),
                watermark_blend   = str(data.get("watermark_blend") or "normal"),
                avatar_position   = str(data.get("avatar_position") or "top-left"),
                font_name         = font_name,
                quote_font_size   = int(data.get("quote_font_size") or 52),
                author_font_size  = int(data.get("author_font_size") or 30),
                watermark_size_percent = float(data.get("watermark_size_percent") or 0.15),
                watermark_position= "bottom-right",
                background_mode   = str(data.get("background_mode") or "none"),
                ai_model          = data.get("ai_model") or None,
                hf_api_key        = data.get("hf_api_key") or None,
                language          = language,
            )
            if sr and q.get("_row") and topic:
                abs_url = f"http://localhost:8000/generated/{Path(path).name}"
                sr.write_back(topic, int(q["_row"]), abs_url)
                with __import__("PIL").Image.open(path) as im:
                    dims = f"{im.width}x{im.height}"
                sr.write_generation_meta(int(q["_row"]), dims, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as e:
            print(f"[WARN] bulk gen: {e}")
        done += 1

    return {"success": True, "generated": done}


@app.route("/api/drive/upload", methods=["POST"])
def api_drive_upload():
    data = request.get_json() or {}
    filenames = data.get("filenames") or []
    topic = str(data.get("topic") or "").strip() or None
    if isinstance(filenames, str):
        filenames = [filenames]
    filenames = [str(x) for x in filenames if str(x).strip()]
    if not filenames:
        return jsonify({"ok": False, "error": "No filenames provided"}), 400

    du = get_drive()
    if not du:
        return jsonify({"ok": False, "error": "Drive uploader not available"}), 503

    out = []
    for fn in filenames:
        p = (BASE_DIR / "Generated_Images" / fn).resolve()
        if not p.exists():
            out.append({"filename": fn, "ok": False, "error": "File not found"})
            continue
        try:
            link = du.upload_image(str(p), topic=topic)
            if link:
                out.append({"filename": fn, "ok": True, "link": link})
            else:
                out.append({"filename": fn, "ok": False, "error": "No link returned"})
        except Exception as e:
            out.append({"filename": fn, "ok": False, "error": str(e)})

    return jsonify({"ok": True, "results": out})

# ══════════════════════════════════════════════════════════════════════════════
#  STAGE 4 — POST  (placeholder)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/post/platforms")
def api_post_platforms():
    return jsonify({"platforms": [
        {"id":"instagram","label":"Instagram",  "icon":"📸","connected":False},
        {"id":"facebook", "label":"Facebook",   "icon":"👥","connected":False},
        {"id":"twitter",  "label":"X / Twitter","icon":"🐦","connected":False},
        {"id":"pinterest","label":"Pinterest",  "icon":"📌","connected":False},
    ]})


@app.route("/api/post/queue")
def api_post_queue():
    gen_dir = BASE_DIR / "Generated_Images"
    images  = []
    if gen_dir.exists():
        files = sorted(
            list(gen_dir.glob("*.png")) + list(gen_dir.glob("*.jpg")),
            key=lambda x: x.stat().st_mtime, reverse=True
        )
        for f in files[:24]:
            images.append({"filename": f.name, "url": f"/generated/{f.name}",
                           "size": f.stat().st_size, "posted": False})
    return jsonify({"images": images})


# ══════════════════════════════════════════════════════════════════════════════
#  STATIC
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/generated/<filename>")
def serve_generated(filename):
    return send_from_directory(BASE_DIR / "Generated_Images", filename)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    (BASE_DIR / "Generated_Images").mkdir(exist_ok=True)
    (BASE_DIR / "Export").mkdir(exist_ok=True)
    (BASE_DIR / "templates").mkdir(exist_ok=True)

    print("\n" + "═"*62)
    print(f"  🎑  QuoteMaster  v{APP_VERSION_UNIFIED}")
    print("═"*62)
    print("  📥  Collect  →  ✅  Review  →  🖼  Generate  →  📤  Post")
    print(f"\n  🌐  http://localhost:8000\n")
    debug = os.getenv("DASHBOARD_DEBUG","").strip().lower() in ("1","true","yes")
    app.run(host="0.0.0.0", port=8000, debug=debug, use_reloader=False)
