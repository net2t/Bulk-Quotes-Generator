#!/usr/bin/env python3
"""
Web Dashboard for Quote Image Generator
Main Flask application
"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
import os
import json
from pathlib import Path
from datetime import datetime
from PIL import Image
from sheet_reader import SheetReader
from image_generator import QuoteImageGenerator
from google_drive_uploader import DriveUploader

app = Flask(__name__)

# Initialize components
sheet_reader = SheetReader()
image_gen = QuoteImageGenerator()
drive_uploader = DriveUploader()

def load_config():
    try:
        config_path = Path('references') / 'config.json'
        if config_path.exists():
            return json.loads(config_path.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {}

CONFIG = load_config()

# Dashboard HTML Template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quote Image Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        :root {
            --ui-font: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";

            /* Theme variables */
            --bg: radial-gradient(1200px 800px at 20% 10%, rgba(0, 210, 255, 0.25), transparent 60%),
                  radial-gradient(900px 700px at 80% 20%, rgba(196, 113, 237, 0.25), transparent 60%),
                  radial-gradient(1200px 900px at 50% 90%, rgba(255, 107, 157, 0.18), transparent 60%),
                  linear-gradient(135deg, #090a1a 0%, #0b1026 40%, #070816 100%);
            --text: rgba(230, 236, 255, 0.95);
            --muted: rgba(230, 236, 255, 0.72);
            --panel: rgba(255, 255, 255, 0.06);
            --panel-2: rgba(255, 255, 255, 0.07);
            --border: rgba(255, 255, 255, 0.12);
            --shadow: 0 20px 60px rgba(0, 0, 0, 0.55);
            --accent: rgba(0, 210, 255, 0.85);
            --accent-soft: rgba(0, 210, 255, 0.12);
            --accent-2: rgba(196, 113, 237, 0.65);
        }

        body {
            font-family: var(--ui-font);
            background: var(--bg);
            min-height: 100vh;
            padding: 22px;
            color: var(--text);
            overflow-x: hidden;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            border-radius: 24px;
            padding: 28px;
            background: var(--panel);
            border: 1px solid var(--border);
            box-shadow:
                var(--shadow),
                0 0 0 1px rgba(255, 255, 255, 0.04) inset;
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            position: relative;
            overflow: hidden;
            animation: enter 650ms cubic-bezier(.2,.8,.2,1);
        }

        .container:before {
            content: '';
            position: absolute;
            inset: -2px;
            background: radial-gradient(800px 500px at 20% 0%, rgba(0,210,255,0.25), transparent 60%),
                        radial-gradient(900px 600px at 80% 20%, rgba(196,113,237,0.18), transparent 62%);
            filter: blur(18px);
            opacity: 0.8;
            pointer-events: none;
        }

        @keyframes enter {
            from { transform: translateY(18px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        h1 {
            text-align: center;
            color: var(--text);
            margin-bottom: 8px;
            font-size: 2.2em;
            letter-spacing: 0.2px;
            text-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
        }
        .subtitle {
            text-align: center;
            color: var(--muted);
            margin-bottom: 22px;
        }

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 18px;
            position: relative;
            z-index: 1;
        }

        .badge {
            font-size: 12px;
            padding: 8px 10px;
            border-radius: 999px;
            background: var(--panel-2);
            border: 1px solid var(--border);
            color: var(--muted);
            display: inline-flex;
            gap: 8px;
            align-items: center;
        }
        .controls {
            display: grid;
            grid-template-columns: 1.2fr 1.2fr 0.6fr 0.8fr;
            gap: 14px;
            margin-bottom: 16px;
            position: relative;
            z-index: 1;
        }
        .control-group {
            display: flex;
            flex-direction: column;
        }
        label {
            margin-bottom: 8px;
            font-weight: 650;
            color: var(--text);
        }
        select, button, input {
            padding: 12px 14px;
            border: 1px solid var(--border);
            border-radius: 12px;
            font-size: 14px;
            transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease, background 180ms ease;
            background: var(--panel-2);
            color: var(--text);
        }

        select option {
            color: #111827;
        }
        select:focus, input:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 4px var(--accent-soft);
        }
        .style-selector {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 12px;
            margin-bottom: 18px;
            position: relative;
            z-index: 1;
        }
        .style-card {
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 16px;
            text-align: center;
            cursor: pointer;
            transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease, background 180ms ease;
            background: rgba(255, 255, 255, 0.05);
            position: relative;
            overflow: hidden;
        }
        .style-card:hover {
            border-color: var(--accent);
            transform: translateY(-4px);
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.35);
        }
        .style-card.selected {
            border-color: var(--accent);
            background: linear-gradient(135deg, rgba(0, 210, 255, 0.16), rgba(196, 113, 237, 0.12));
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.20);
        }
        .style-icon {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .style-name {
            font-weight: 600;
            color: rgba(241, 245, 255, 0.9);
        }
        .quote-display {
            background: var(--panel);
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 16px;
            min-height: 200px;
            border: 1px solid var(--border);
            position: relative;
            z-index: 1;
        }

        .quote-header {
            display: flex;
            gap: 12px;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }

        .avatar {
            width: 44px;
            height: 44px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.14);
            overflow: hidden;
            flex: 0 0 auto;
            box-shadow: 0 18px 40px rgba(0,0,0,0.35);
        }

        .avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        .pill {
            font-size: 12px;
            padding: 8px 10px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: rgba(230, 236, 255, 0.82);
        }
        .quote-text {
            font-size: 1.15em;
            line-height: 1.6;
            color: var(--text);
            margin-bottom: 12px;
            font-style: italic;
        }
        .quote-author {
            text-align: right;
            color: var(--muted);
            font-weight: 600;
        }
        .btn-generate {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, rgba(0, 210, 255, 0.85) 0%, rgba(196, 113, 237, 0.78) 100%);
            color: white;
            border: none;
            border-radius: 14px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-generate:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 45px rgba(0, 210, 255, 0.18);
        }
        .btn-generate:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background: rgba(46, 213, 115, 0.10);
            border-radius: 14px;
            display: none;
            border: 1px solid rgba(46, 213, 115, 0.25);
        }
        .result.show {
            display: block;
        }
        .result a {
            color: rgba(0, 210, 255, 0.95);
            text-decoration: none;
            font-weight: 600;
        }
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        .loading.show {
            display: block;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid rgba(0, 210, 255, 0.9);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        .row {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
            margin-top: 12px;
            position: relative;
            z-index: 1;
        }

        .bulk {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 16px;
            padding: 14px;
        }

        .bulk h3 {
            font-size: 14px;
            margin-bottom: 10px;
            color: rgba(241, 245, 255, 0.9);
        }

        .hint {
            font-size: 12px;
            color: var(--muted);
            margin-top: 8px;
        }

        /* Themes (reliable via variables) */
        body[data-theme="futuristic"] {
            --bg: radial-gradient(1200px 800px at 20% 10%, rgba(0, 210, 255, 0.25), transparent 60%),
                  radial-gradient(900px 700px at 80% 20%, rgba(196, 113, 237, 0.25), transparent 60%),
                  radial-gradient(1200px 900px at 50% 90%, rgba(255, 107, 157, 0.18), transparent 60%),
                  linear-gradient(135deg, #090a1a 0%, #0b1026 40%, #070816 100%);
            --text: rgba(230, 236, 255, 0.95);
            --muted: rgba(230, 236, 255, 0.72);
            --panel: rgba(255, 255, 255, 0.06);
            --panel-2: rgba(255, 255, 255, 0.07);
            --border: rgba(255, 255, 255, 0.12);
            --shadow: 0 20px 60px rgba(0, 0, 0, 0.55);
            --accent: rgba(0, 210, 255, 0.85);
            --accent-soft: rgba(0, 210, 255, 0.12);
            --accent-2: rgba(196, 113, 237, 0.65);
        }

        body[data-theme="minimal"] {
            --bg: linear-gradient(160deg, #ffffff 0%, #f6f7fb 55%, #eef2f7 100%);
            --text: rgba(15, 23, 42, 0.96);
            --muted: rgba(15, 23, 42, 0.70);
            --panel: rgba(255, 255, 255, 0.92);
            --panel-2: rgba(15, 23, 42, 0.04);
            --border: rgba(15, 23, 42, 0.14);
            --shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
            --accent: rgba(37, 99, 235, 0.92);
            --accent-soft: rgba(37, 99, 235, 0.12);
            --accent-2: rgba(16, 185, 129, 0.70);
        }

        body[data-theme="midnight"] {
            --bg: radial-gradient(circle at 15% 25%, rgba(59, 130, 246, 0.18), transparent 55%),
                  radial-gradient(circle at 75% 15%, rgba(168, 85, 247, 0.16), transparent 55%),
                  linear-gradient(135deg, #050615 0%, #070a1f 50%, #020313 100%);
            --text: rgba(238, 242, 255, 0.96);
            --muted: rgba(226, 232, 240, 0.72);
            --panel: rgba(255, 255, 255, 0.06);
            --panel-2: rgba(255, 255, 255, 0.07);
            --border: rgba(255, 255, 255, 0.12);
            --shadow: 0 24px 70px rgba(0, 0, 0, 0.6);
            --accent: rgba(59, 130, 246, 0.88);
            --accent-soft: rgba(59, 130, 246, 0.14);
            --accent-2: rgba(168, 85, 247, 0.64);
        }

        body[data-theme="aurora"] {
            --bg: radial-gradient(circle at 20% 15%, rgba(16, 185, 129, 0.22), transparent 55%),
                  radial-gradient(circle at 80% 25%, rgba(59, 130, 246, 0.20), transparent 55%),
                  radial-gradient(circle at 55% 85%, rgba(236, 72, 153, 0.16), transparent 60%),
                  linear-gradient(135deg, #050713 0%, #07112b 50%, #050713 100%);
            --text: rgba(241, 245, 255, 0.96);
            --muted: rgba(226, 232, 240, 0.72);
            --panel: rgba(255, 255, 255, 0.06);
            --panel-2: rgba(255, 255, 255, 0.07);
            --border: rgba(255, 255, 255, 0.12);
            --shadow: 0 24px 70px rgba(0, 0, 0, 0.58);
            --accent: rgba(16, 185, 129, 0.88);
            --accent-soft: rgba(16, 185, 129, 0.14);
            --accent-2: rgba(59, 130, 246, 0.70);
        }

        body[data-theme="slate"] {
            --bg: linear-gradient(135deg, #0b1220 0%, #0a1626 55%, #08101d 100%);
            --text: rgba(241, 245, 255, 0.94);
            --muted: rgba(203, 213, 225, 0.70);
            --panel: rgba(148, 163, 184, 0.08);
            --panel-2: rgba(148, 163, 184, 0.10);
            --border: rgba(148, 163, 184, 0.18);
            --shadow: 0 22px 64px rgba(0, 0, 0, 0.55);
            --accent: rgba(148, 163, 184, 0.9);
            --accent-soft: rgba(148, 163, 184, 0.14);
            --accent-2: rgba(34, 211, 238, 0.60);
        }

        /* Theme-specific dropdown option color for light theme */
        body[data-theme="minimal"] select option {
            color: #111827;
        }

        .footer-actions {
            margin-top: 16px;
            padding-top: 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.12);
            position: relative;
            z-index: 1;
        }

        .manual {
            margin-top: 14px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 16px;
            padding: 14px;
            position: relative;
            z-index: 1;
            display: none;
        }

        textarea {
            width: 100%;
            min-height: 110px;
            resize: vertical;
            padding: 12px 14px;
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.07);
            color: rgba(241, 245, 255, 0.95);
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="topbar">
            <div style="display:flex; gap:10px; align-items:center;">
                <div class="badge" id="theme-badge">⚡ Futuristic Dashboard</div>
                <select id="theme" onchange="applyTheme()" style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.14); border-radius: 999px; padding: 8px 10px; color: rgba(241,245,255,0.92); font-size: 12px;">
                    <option value="futuristic" selected>Futuristic</option>
                    <option value="minimal">Minimal Light</option>
                    <option value="midnight">Midnight</option>
                    <option value="aurora">Aurora</option>
                    <option value="slate">Slate</option>
                </select>
            </div>
            <div class="badge" id="sheet-status">🔌 Sheet: connecting…</div>
        </div>
        <h1>Quote Image Generator</h1>
        <p class="subtitle">Pick a topic, preview, then generate single or bulk images</p>
        <div class="controls">
            <div class="control-group">
                <label for="topic">📚 Select Topic</label>
                <select id="topic" onchange="loadQuotes()">
                    <option value="">Choose a topic...</option>
                </select>
            </div>
            <div class="control-group">
                <label for="quote-select">💬 Select Quote</label>
                <select id="quote-select">
                    <option value="">Choose a quote...</option>
                </select>
            </div>
            <div class="control-group">
                <label for="upload-target">🧾 Sheet Write-back</label>
                <select id="upload-target">
                    <option value="none">Off</option>
                    <option value="sheet" selected>On (Preview Link + Status)</option>
                </select>
            </div>

            <div class="control-group">
                <label for="watermark-mode">💧 Watermark</label>
                <select id="watermark-mode">
                    <option value="corner" selected>Corner</option>
                    <option value="stripe">Stripe</option>
                </select>
            </div>

            <div class="control-group">
                <label for="mode">🧩 Mode</label>
                <select id="mode" onchange="toggleMode()">
                    <option value="sheet" selected>Use Sheet</option>
                    <option value="manual">Manual Input</option>
                </select>
            </div>
        </div>
        <div class="quote-display" id="quote-display">
            <div class="quote-header">
                <div style="display:flex; gap:10px; align-items:center;">
                    <div class="avatar" title="Quote">
                        <img id="quote-icon" alt="Quote" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 24 24'%3E%3Cpath fill='%2300d2ff' d='M7 17h3l2-4V7H6v6h3l-2 4Zm10 0h3l2-4V7h-6v6h3l-2 4Z'/%3E%3C/svg%3E"/>
                    </div>
                    <div class="avatar" title="Author">
                        <img id="author-avatar" alt="Author" src="" />
                    </div>
                </div>
                <div class="pill" id="meta-pill">Length: —</div>
            </div>
            <p class="quote-text" id="current-quote">Select a topic and quote to get started...</p>
            <p class="quote-author" id="current-author"></p>
        </div>
        <div class="row" style="margin-top: 0;">
            <div class="bulk">
                <h3>🔤 Dashboard Font</h3>
                <label for="ui-font" style="margin-top:6px;">Font</label>
                <select id="ui-font" onchange="applyUIFont()">
                    <option value="Inter" selected>Inter</option>
                    <option value="Segoe UI">Segoe UI</option>
                    <option value="Poppins">Poppins</option>
                    <option value="JetBrains Mono">JetBrains Mono</option>
                    <option value="Georgia">Georgia</option>
                </select>
                <div class="hint">Changes dashboard font only (not generated image fonts).</div>
            </div>
            <div class="bulk">
                <h3>📦 Bulk Generator</h3>
                <label for="bulk-count" style="margin-top:6px;">Count</label>
                <input id="bulk-count" type="number" min="1" max="200" value="10" />
                <button class="btn-generate" style="padding: 12px; font-size: 14px; margin-top: 10px;" onclick="generateBulk()" id="bulk-btn" disabled>
                    🚀 Generate Bulk
                </button>
                <div class="hint">Bulk only works in Sheet mode.</div>
            </div>
        </div>

        <label style="margin: 14px 0 12px; display: block; position: relative; z-index: 1;">🎨 Choose Design Style</label>
        <div class="style-selector">
            <div class="style-card" data-style="minimal" onclick="selectStyle('minimal')">
                <div class="style-icon">⚪</div>
                <div class="style-name">Minimal</div>
            </div>
            <div class="style-card selected" data-style="bright" onclick="selectStyle('bright')">
                <div class="style-icon">🌈</div>
                <div class="style-name">Bright</div>
            </div>
            <div class="style-card" data-style="elegant" onclick="selectStyle('elegant')">
                <div class="style-icon">✨</div>
                <div class="style-name">Elegant</div>
            </div>
            <div class="style-card" data-style="bold" onclick="selectStyle('bold')">
                <div class="style-icon">⚡</div>
                <div class="style-name">Bold</div>
            </div>
            <div class="style-card" data-style="modern" onclick="selectStyle('modern')">
                <div class="style-icon">🔷</div>
                <div class="style-name">Modern</div>
            </div>
            <div class="style-card" data-style="neon" onclick="selectStyle('neon')">
                <div class="style-icon">🧿</div>
                <div class="style-name">Neon</div>
            </div>
        </div>

 

        <div class="manual" id="manual">
            <h3 style="font-size: 14px; margin-bottom: 10px; color: rgba(241,245,255,0.9);">✍ Manual Input</h3>
            <div class="row" style="grid-template-columns: 1.4fr 0.8fr 0.8fr;">
                <div>
                    <label for="manual-quote">Quote</label>
                    <textarea id="manual-quote" placeholder="Paste your quote here..."></textarea>
                </div>
                <div>
                    <label for="manual-author">Author</label>
                    <input id="manual-author" placeholder="Author name" />
                    <div style="height: 10px;"></div>
                    <label for="manual-image">Author Image URL (optional)</label>
                    <input id="manual-image" placeholder="https://..." />
                </div>
                <div>
                    <label for="manual-topic">Topic (optional)</label>
                    <input id="manual-topic" placeholder="Topic" />
                    <div class="hint">Manual mode ignores sheet and allows direct generation.</div>
                </div>
            </div>
        </div>

        <div class="footer-actions">
            <button class="btn-generate" id="generate-btn" onclick="generateImage()" disabled>
                🎨 Generate Image
            </button>
            <div class="hint">If upload target is “Write back to Sheet”, the link/path will be written to the configured column.</div>
        </div>
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="margin-top: 15px;">Creating your masterpiece...</p>
        </div>
        <div class="result" id="result">
            <h3 id="result-title">✅ Ready</h3>
            <p id="result-message"></p>
        </div>
    </div>
    <script>
        let selectedStyle = 'bright';
        let allQuotes = {};
        let currentQuote = null;
        let mode = 'sheet';
        // Load topics on page load
        window.onload = function() {
            document.body.setAttribute('data-theme', 'futuristic');
            loadUIFontOptions();
            fetch('/api/topics')
                .then(r => r.json())
                .then(data => {
                    const status = document.getElementById('sheet-status');
                    status.textContent = data.topics && data.topics.length ? '✅ Sheet: connected' : '⚠️ Sheet: check config';
                    const select = document.getElementById('topic');
                    data.topics.forEach(topic => {
                        const option = document.createElement('option');
                        option.value = topic;
                        option.textContent = topic;
                        select.appendChild(option);
                    });
                });
        };

        function loadUIFontOptions() {
            fetch('/api/fonts')
                .then(r => r.json())
                .then(data => {
                    if (!data || !Array.isArray(data.fonts)) return;

                    const select = document.getElementById('ui-font');
                    const builtIns = new Set(['Inter', 'Segoe UI', 'Poppins', 'JetBrains Mono', 'Georgia']);
                    const styleEl = document.createElement('style');
                    styleEl.id = 'dynamic-font-faces';
                    document.head.appendChild(styleEl);

                    data.fonts.forEach(f => {
                        if (!f || !f.family || !f.file) return;

                        if (![...select.options].some(o => o.value === f.family)) {
                            const opt = document.createElement('option');
                            opt.value = f.family;
                            opt.textContent = f.family + ' (Local)';
                            select.appendChild(opt);
                        }

                        if (!builtIns.has(f.family)) {
                            styleEl.textContent += `\n@font-face { font-family: "${f.family}"; src: url("/assets/fonts/${encodeURIComponent(f.file)}") format("truetype"); font-display: swap; }\n`;
                        }
                    });
                })
                .catch(() => {});
        }

        function applyUIFont() {
            const f = document.getElementById('ui-font').value;
            document.documentElement.style.setProperty('--ui-font', `${f}, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial`);
        }

        function applyTheme() {
            const t = document.getElementById('theme').value;
            document.body.setAttribute('data-theme', t);
            const badge = document.getElementById('theme-badge');
            badge.textContent = (t === 'minimal') ? '◻ Minimal Light' : (t === 'midnight') ? '🌙 Midnight' : (t === 'aurora') ? '🌈 Aurora' : (t === 'slate') ? '🪨 Slate' : '⚡ Futuristic Dashboard';
        }

        function toggleMode() {
            mode = document.getElementById('mode').value;
            const manual = document.getElementById('manual');
            const topic = document.getElementById('topic');
            const quoteSelect = document.getElementById('quote-select');
            const bulkBtn = document.getElementById('bulk-btn');
            if (mode === 'manual') {
                manual.style.display = 'block';
                topic.disabled = true;
                quoteSelect.disabled = true;
                bulkBtn.disabled = true;
                document.getElementById('generate-btn').disabled = false;
            } else {
                manual.style.display = 'none';
                topic.disabled = false;
                quoteSelect.disabled = false;
                // generate enabled only after selecting a quote
                document.getElementById('generate-btn').disabled = true;
            }
        }
        function loadQuotes() {
            const topic = document.getElementById('topic').value;
            if (!topic) return;
            fetch(`/api/quotes/${topic}`)
                .then(r => r.json())
                .then(data => {
                    allQuotes = data.quotes;
                    const select = document.getElementById('quote-select');
                    select.innerHTML = '<option value="">Choose a quote...</option>';
                    data.quotes.forEach((quote, index) => {
                        const option = document.createElement('option');
                        option.value = index;
                        const authorLabel = (quote.author || 'Unknown').toString();
                        option.textContent = authorLabel;
                        select.appendChild(option);
                    });
                    select.onchange = function() {
                        const idx = this.value;
                        if (idx !== '') {
                            currentQuote = allQuotes[idx];
                            document.getElementById('current-quote').textContent = `"${currentQuote.quote}"`;
                            document.getElementById('current-author').textContent = `— ${currentQuote.author}`;
                            document.getElementById('meta-pill').textContent = `Length: ${currentQuote.length ?? '—'}`;
                            const avatar = document.getElementById('author-avatar');
                            avatar.src = currentQuote.author_image || currentQuote.image || '';
                            document.getElementById('generate-btn').disabled = false;
                            document.getElementById('bulk-btn').disabled = false;
                        }
                    };
                });
        }
        function selectStyle(style) {
            selectedStyle = style;
            document.querySelectorAll('.style-card').forEach(card => {
                card.classList.remove('selected');
            });
            document.querySelector(`[data-style="${style}"]`).classList.add('selected');
        }
        function generateImage() {
            if (mode === 'sheet' && !currentQuote) return;

            let payload;
            if (mode === 'manual') {
                payload = {
                    quote: document.getElementById('manual-quote').value || '',
                    author: document.getElementById('manual-author').value || 'Unknown',
                    author_image: document.getElementById('manual-image').value || '',
                    style: selectedStyle,
                    topic: document.getElementById('manual-topic').value || null,
                };
            } else {
                payload = {
                    quote: currentQuote.quote,
                    author: currentQuote.author,
                    author_image: currentQuote.author_image || currentQuote.image || '',
                    style: selectedStyle,
                    topic: document.getElementById('topic').value,
                    row: currentQuote._row || null
                };
            }

            payload.upload_target = document.getElementById('upload-target').value;
            payload.watermark_mode = document.getElementById('watermark-mode').value;
            
            document.getElementById('loading').classList.add('show');
            document.getElementById('result').classList.remove('show');
            document.getElementById('generate-btn').disabled = true;
            
            fetch('/api/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('loading').classList.remove('show');
                document.getElementById('generate-btn').disabled = false;
                if (!data.success) {
                    alert('Error: ' + data.error);
                    return;
                }

                const resultDiv = document.getElementById('result');
                const title = document.getElementById('result-title');
                const messageP = document.getElementById('result-message');

                title.textContent = '✅ Image Generated';
                messageP.innerHTML = `📁 <strong>Saved to:</strong> ${data.image_path}`;
                resultDiv.classList.add('show');
            })
            .catch(err => {
                document.getElementById('loading').classList.remove('show');
                document.getElementById('generate-btn').disabled = false;
                alert('Error generating image: ' + err);
            });
        }
        function generateBulk() {
            const topic = document.getElementById('topic').value;
            if (!topic) return;
            const count = parseInt(document.getElementById('bulk-count').value || '10', 10);
            const upload_target = document.getElementById('upload-target').value;
            const watermark_mode = document.getElementById('watermark-mode').value;
            document.getElementById('loading').classList.add('show');
            document.getElementById('result').classList.remove('show');
            fetch('/api/generate_bulk', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    topic,
                    style: selectedStyle,
                    count,
                    upload_target,
                    watermark_mode
                })
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('loading').classList.remove('show');
                if (!data.success) {
                    alert('Bulk error: ' + data.error);
                    return;
                }
                const resultDiv = document.getElementById('result');
                const messageP = document.getElementById('result-message');
                messageP.innerHTML = `📦 <strong>Generated:</strong> ${data.generated} images<br>📁 <strong>Folder:</strong> Generated_Images/`;
                resultDiv.classList.add('show');
            })
            .catch(err => {
                document.getElementById('loading').classList.remove('show');
                alert('Bulk error: ' + err);
            });
        }
    </script>
</body>
</html>
'''

@app.route('/generated/<filename>')
def generated(filename):
    """Serve generated images for dashboard preview"""
    return send_from_directory('Generated_Images', filename)

@app.route('/assets/<path:filename>')
def assets(filename):
    """Serve static assets"""
    return send_from_directory('assets', filename)

@app.route('/api/fonts')
def get_fonts():
    """List available UI fonts from assets/fonts"""
    try:
        fonts_dir = Path('assets') / 'fonts'
        fonts = []
        if fonts_dir.exists():
            for p in sorted(fonts_dir.glob('*.ttf')):
                family = p.stem
                fonts.append({'family': family, 'file': p.name})
        return jsonify({'fonts': fonts})
    except Exception as e:
        return jsonify({'fonts': [], 'error': str(e)})

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/topics')
def get_topics():
    """Get all available topics"""
    if sheet_reader.connect():
        topics = sheet_reader.get_all_topics()
        return jsonify({'topics': topics})
    return jsonify({'topics': []})

@app.route('/api/quotes/<topic>')
def get_quotes(topic):
    """Get quotes for a specific topic"""
    quotes = sheet_reader.get_quotes_by_topic(topic)
    return jsonify({'quotes': quotes})

@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate a quote image"""
    data = request.json
    quote = data.get('quote')
    author = data.get('author')
    style = data.get('style', 'minimal')
    topic = data.get('topic')
    upload_target = data.get('upload_target', 'none')
    watermark_mode = data.get('watermark_mode', 'corner')
    row = data.get('row')
    
    try:
        # Generate image
        image_path = image_gen.generate(
            quote,
            author,
            style,
            author_image=str(data.get('author_image') or ''),
            watermark_mode=str(watermark_mode or 'corner')
        )

        filename = Path(image_path).name
        public_url = f"/generated/{filename}"
        absolute_url = f"{request.host_url.rstrip('/')}{public_url}"
        
        drive_link = None

        upload_result = "No upload"
        # Google Drive upload temporarily disabled (kept for future use)
        # if upload_target == 'drive':
        #     try:
        #         if not drive_uploader.service:
        #             drive_uploader.connect()
        #         drive_link = drive_uploader.upload_image(image_path, topic)
        #         upload_result = drive_link or "Uploaded"
        #     except Exception as e:
        #         upload_result = f"Drive upload failed: {e}"
        if upload_target == 'sheet':
            try:
                write_value = absolute_url
                if topic and row:
                    ok = sheet_reader.write_back(str(topic), int(row), str(write_value))
                    # Append metadata columns at end
                    try:
                        with Image.open(image_path) as im:
                            dimensions = f"{im.width}x{im.height}"
                    except Exception:
                        dimensions = ""
                    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    sheet_reader.write_generation_meta(int(row), dimensions, ts)

                    upload_result = "Wrote back to sheet" if ok else "Failed to write back"
                else:
                    upload_result = "Missing topic/row for write-back"
            except Exception as e:
                upload_result = f"Sheet write-back failed: {e}"
        
        return jsonify({
            'success': True,
            'image_path': image_path,
            'drive_link': drive_link,
            'public_url': public_url,
            'upload_target': upload_target,
            'upload_result': upload_result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/generate_bulk', methods=['POST'])
def generate_bulk():
    """Bulk generation for a topic"""
    data = request.json
    topic = data.get('topic')
    style = data.get('style', 'minimal')
    count = int(data.get('count', 10) or 10)
    upload_target = data.get('upload_target', 'none')
    watermark_mode = data.get('watermark_mode', 'corner')
    if not topic:
        return jsonify({'success': False, 'error': 'Topic required'})
    if count < 1:
        return jsonify({'success': False, 'error': 'Count must be >= 1'})
    try:
        if not sheet_reader.spreadsheet:
            if not sheet_reader.connect():
                return jsonify({'success': False, 'error': 'Failed to connect to Google Sheets'})
        quotes = sheet_reader.get_quotes_by_topic(topic)
        if not quotes:
            return jsonify({'success': False, 'error': f'No quotes found for topic: {topic}'})
        import random
        if count >= len(quotes):
            random.shuffle(quotes)
            selected_quotes = quotes
        else:
            selected_quotes = random.sample(quotes, count)
        generated_paths = []
        generated_urls = []
        for q in selected_quotes:
            try:
                p = image_gen.generate(
                    q.get('quote', ''),
                    q.get('author', 'Unknown'),
                    style,
                    author_image=str(q.get('author_image') or q.get('image') or ''),
                    watermark_mode=str(watermark_mode or 'corner')
                )
                generated_paths.append(p)
                fn = Path(p).name
                pu = f"/generated/{fn}"
                au = f"{request.host_url.rstrip('/')}{pu}"
                generated_urls.append(au)
            except Exception:
                continue

        # Google Drive upload temporarily disabled (kept for future use)
        # if upload_target == 'drive' and generated_paths:
        #     try:
        #         if not drive_uploader.service:
        #             drive_uploader.connect()
        #         for p in generated_paths:
        #             drive_uploader.upload_image(p, topic)
        #     except Exception as e:
        #         print(f"Drive upload failed: {e}")

        if upload_target == 'sheet' and generated_paths:
            # Write back only for rows we generated (best-effort)
            try:
                for i, (q, u) in enumerate(zip(selected_quotes, generated_urls)):
                    write_value = u
                    if q.get('_row'):
                        sheet_reader.write_back(str(topic), int(q.get('_row')), str(write_value))
                        try:
                            p = generated_paths[i]
                            with Image.open(p) as im:
                                dimensions = f"{im.width}x{im.height}"
                        except Exception:
                            dimensions = ""
                        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        sheet_reader.write_generation_meta(int(q.get('_row')), dimensions, ts)
            except Exception as e:
                print(f"Sheet write-back failed: {e}")
        return jsonify({'success': True, 'generated': len(generated_paths)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting Quote Image Generator Dashboard")
    print("="*50)
    print("\n📱 Open your browser and go to:")
    print("   http://localhost:8000\n")

    debug = str(os.getenv('DASHBOARD_DEBUG', '')).strip().lower() in ('1', 'true', 'yes', 'on')
    app.run(host='0.0.0.0', port=8000, debug=debug, use_reloader=False)
