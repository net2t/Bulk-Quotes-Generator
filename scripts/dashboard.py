#!/usr/bin/env python3
"""
Enhanced Web Dashboard for Bulk Quotes Image Generator
- 16 design templates
- Better UI organization
- Watermark blend mode and sizing controls
- Avatar position control
- New filename format: <Category> - <Quote> - <Author> - <DD-MM-YYYY_HHMM>
"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
import os
import json
import sys
from pathlib import Path
from datetime import datetime
from PIL import Image
import uuid
import time

# Add scripts directory to path if needed
script_dir = Path(__file__).parent
if script_dir.name != 'scripts':
    scripts_path = script_dir / 'scripts'
    if scripts_path.exists():
        sys.path.insert(0, str(scripts_path))

from sheet_reader import SheetReader
from image_generator import QuoteImageGenerator  # Will use enhanced version
from google_drive_uploader import DriveUploader

app = Flask(__name__)

# Initialize components
sheet_reader = SheetReader()
image_gen = QuoteImageGenerator()
drive_uploader = DriveUploader()

JOB_PROGRESS: dict[str, dict] = {}

def load_config():
    try:
        config_path = Path('references') / 'config.json'
        if config_path.exists():
            return json.loads(config_path.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {}

CONFIG = load_config()

# Enhanced Dashboard HTML Template
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bulk Quotes Image Generator - Enhanced</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        :root {
            --ui-font: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
            --bg: radial-gradient(1200px 800px at 18% 12%, rgba(20, 184, 166, 0.20), transparent 60%),
                  radial-gradient(900px 700px at 82% 18%, rgba(249, 115, 22, 0.18), transparent 62%),
                  linear-gradient(135deg, #070A10 0%, #0A1220 45%, #060812 100%);
            --text: rgba(244, 247, 255, 0.94);
            --muted: rgba(244, 247, 255, 0.70);
            --panel: rgba(255, 255, 255, 0.06);
            --panel-2: rgba(255, 255, 255, 0.075);
            --border: rgba(255, 255, 255, 0.12);
            --shadow: 0 20px 60px rgba(0, 0, 0, 0.55);
            --accent: rgba(20, 184, 166, 0.92);
            --accent-soft: rgba(20, 184, 166, 0.14);
            --accent-2: rgba(249, 115, 22, 0.92);
            --accent-2-soft: rgba(249, 115, 22, 0.14);
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
            max-width: 1400px;
            margin: 0 auto;
            border-radius: 24px;
            padding: 28px;
            background: var(--panel);
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
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
            background:
                repeating-linear-gradient(135deg,
                    rgba(255,255,255,0.04) 0px,
                    rgba(255,255,255,0.04) 1px,
                    transparent 1px,
                    transparent 14px
                ),
                radial-gradient(800px 500px at 18% 0%, rgba(20,184,166,0.22), transparent 60%),
                radial-gradient(900px 600px at 85% 22%, rgba(249,115,22,0.18), transparent 62%);
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
            font-size: 2.4em;
            letter-spacing: 0.2px;
            text-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
        }
        
        .subtitle {
            text-align: center;
            color: var(--muted);
            margin-bottom: 22px;
            font-size: 1.1em;
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
            padding: 8px 12px;
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
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 20px;
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
            font-size: 13px;
        }
        
        select, button, input, textarea {
            padding: 12px 14px;
            border: 1px solid var(--border);
            border-radius: 12px;
            font-size: 14px;
            transition: all 180ms ease;
            background: var(--panel-2);
            color: var(--text);
            font-family: inherit;
        }

        select option {
            color: #111827;
        }
        
        select:focus, input:focus, textarea:focus {
            outline: none;
            border-color: var(--accent);
            box-shadow: 0 0 0 4px var(--accent-soft);
        }
        
        .section-title {
            font-size: 16px;
            font-weight: 700;
            margin: 24px 0 14px;
            color: var(--text);
            position: relative;
            z-index: 1;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .style-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
            position: relative;
            z-index: 1;
        }
        
        .style-card {
            padding: 18px 12px;
            border: 2px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
            text-align: center;
            cursor: pointer;
            transition: all 200ms ease;
            background: rgba(255, 255, 255, 0.04);
            position: relative;
            overflow: hidden;
        }
        
        .style-card:hover {
            border-color: var(--accent);
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
            background: rgba(255, 255, 255, 0.06);
        }
        
        .style-card.selected {
            border-color: var(--accent);
            background: linear-gradient(135deg, rgba(20, 184, 166, 0.18), rgba(249, 115, 22, 0.10));
            box-shadow: 0 14px 35px rgba(20, 184, 166, 0.18);
            transform: translateY(-2px);
        }
        
        .style-icon {
            font-size: 2.2em;
            margin-bottom: 8px;
            display: block;
        }
        
        .style-name {
            font-weight: 650;
            color: rgba(241, 245, 255, 0.92);
            font-size: 12px;
            line-height: 1.3;
        }
        
        .quote-display {
            background: var(--panel);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 18px;
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
            margin-bottom: 12px;
        }

        .avatar {
            width: 48px;
            height: 48px;
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
            padding: 8px 12px;
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

        .quote-heading {
            text-align: right;
            color: rgba(241, 245, 255, 0.88);
            font-weight: 800;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-top: -6px;
            margin-bottom: 10px;
        }

        .progress-wrap {
            margin-top: 14px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border);
            border-radius: 999px;
            height: 12px;
            overflow: hidden;
            display: none;
        }

        .progress-bar {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, rgba(20, 184, 166, 0.95), rgba(249, 115, 22, 0.92));
            transition: width 250ms ease;
        }

        .progress-text {
            margin-top: 10px;
            font-size: 12px;
            color: var(--muted);
            display: none;
        }
        
        .btn-generate {
            width: 100%;
            padding: 18px;
            background: linear-gradient(135deg, rgba(20, 184, 166, 0.92) 0%, rgba(249, 115, 22, 0.90) 100%);
            color: white;
            border: none;
            border-radius: 14px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
            z-index: 1;
        }
        
        .btn-generate:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 18px 45px rgba(0, 210, 255, 0.18);
        }
        
        .btn-generate:disabled {
            background: #555;
            cursor: not-allowed;
            opacity: 0.6;
        }
        
        .result {
            margin-top: 20px;
            padding: 20px;
            background: rgba(46, 213, 115, 0.10);
            border-radius: 14px;
            display: none;
            border: 1px solid rgba(46, 213, 115, 0.25);
            position: relative;
            z-index: 1;
        }
        
        .result.show {
            display: block;
            animation: slideIn 400ms ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .result a {
            color: rgba(0, 210, 255, 0.95);
            text-decoration: none;
            font-weight: 600;
        }
        
        .loading {
            text-align: center;
            padding: 30px;
            display: none;
            position: relative;
            z-index: 1;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-top: 4px solid rgba(0, 210, 255, 0.9);
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .settings-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 18px;
            position: relative;
            z-index: 1;
        }

        .settings-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
            padding: 16px;
        }

        .settings-card h3 {
            font-size: 14px;
            margin-bottom: 12px;
            color: rgba(241, 245, 255, 0.9);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .hint {
            font-size: 11px;
            color: var(--muted);
            margin-top: 8px;
            line-height: 1.4;
        }

        .new-badge {
            background: linear-gradient(135deg, #FF6B9D, #C471ED);
            color: white;
            font-size: 10px;
            padding: 3px 8px;
            border-radius: 999px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .category-label {
            font-size: 11px;
            color: var(--muted);
            margin-top: 16px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 700;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="topbar">
            <div class="badge">✨ Bulk Quotes Generator v2.0</div>
            <div class="badge" id="sheet-status">🔌 Connecting...</div>
        </div>
        
        <h1>🎨 Bulk Quotes Image Generator</h1>
        <p class="subtitle">16 Professional Design Templates • Smart Filename Format • Google Drive Integration</p>
        
        <div class="controls">
            <div class="control-group">
                <label for="topic">📚 Topic</label>
                <select id="topic" onchange="loadQuotes()">
                    <option value="">Choose topic...</option>
                </select>
            </div>
            <div class="control-group">
                <label for="quote-select">💬 Quote</label>
                <select id="quote-select">
                    <option value="">Choose quote...</option>
                </select>
            </div>
            <div class="control-group">
                <label for="font-select">🔤 Font</label>
                <select id="font-select">
                    <option value="">Default</option>
                </select>
            </div>
        </div>
        
        <div class="quote-display" id="quote-display">
            <div class="quote-header">
                <div style="display:flex; gap:12px; align-items:center;">
                    <div class="avatar">
                        <img id="quote-icon" alt="Quote" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 24 24'%3E%3Cpath fill='%2300d2ff' d='M7 17h3l2-4V7H6v6h3l-2 4Zm10 0h3l2-4V7h-6v6h3l-2 4Z'/%3E%3C/svg%3E"/>
                    </div>
                    <div class="avatar">
                        <img id="author-avatar" alt="Author" src="" />
                    </div>
                </div>
                <div class="pill" id="meta-pill">Select a quote</div>
            </div>
            <p class="quote-text" id="current-quote">Select a topic and quote to get started...</p>
            <div class="quote-heading" id="quote-heading"></div>
            <p class="quote-author" id="current-author"></p>
        </div>
        
        <div class="section-title">
            🎨 Design Templates
            <span class="new-badge">NEW</span>
        </div>
        
        <div class="category-label">🎨 Styles</div>
        <div class="style-grid">
            <div class="style-card selected" data-style="elegant" onclick="selectStyle('elegant')">
                <div class="style-icon">✨</div>
                <div class="style-name">Elegant</div>
            </div>
            <div class="style-card" data-style="modern" onclick="selectStyle('modern')">
                <div class="style-icon">🔷</div>
                <div class="style-name">Modern</div>
            </div>
            <div class="style-card" data-style="neon" onclick="selectStyle('neon')">
                <div class="style-icon">🧿</div>
                <div class="style-name">Neon</div>
            </div>
            <div class="style-card" data-style="vintage" onclick="selectStyle('vintage')">
                <div class="style-icon">📜</div>
                <div class="style-name">Vintage</div>
            </div>
            <div class="style-card" data-style="minimalist_dark" onclick="selectStyle('minimalist_dark')">
                <div class="style-icon">🌑</div>
                <div class="style-name">Minimalist Dark</div>
            </div>
            <div class="style-card" data-style="creative_split" onclick="selectStyle('creative_split')">
                <div class="style-icon">🎭</div>
                <div class="style-name">Creative Split</div>
            </div>
            <div class="style-card" data-style="geometric" onclick="selectStyle('geometric')">
                <div class="style-icon">🔺</div>
                <div class="style-name">Geometric</div>
            </div>
            <div class="style-card" data-style="artistic" onclick="selectStyle('artistic')">
                <div class="style-icon">🎨</div>
                <div class="style-name">Artistic</div>
            </div>
        </div>
        
        <div class="settings-grid">
            <div class="settings-card">
                <h3>📝 Quote Font Size</h3>
                <input id="quote-font-size" type="number" min="20" max="120" value="52" />
                <div class="hint">Increase/decrease quote text size</div>
            </div>

            <div class="settings-card">
                <h3>👤 Author Size</h3>
                <input id="author-font-size" type="number" min="14" max="80" value="30" />
                <div class="hint">Increase/decrease author text size</div>
            </div>

            <div class="settings-card">
                <h3>🫧 Watermark Opacity</h3>
                <input id="watermark-opacity" type="number" min="0" max="1" step="0.05" value="0.70" />
                <div class="hint">0 = hidden, 1 = solid</div>
            </div>

            <div class="settings-card">
                <h3>🖼️ Watermark Size (%)</h3>
                <input id="watermark-size" type="number" min="5" max="40" step="1" value="15" />
                <div class="hint">15 = recommended</div>
            </div>

            <div class="settings-card">
                <h3>🎚️ Blend Mode</h3>
                <select id="watermark-blend">
                    <option value="normal" selected>Normal</option>
                    <option value="multiply">Multiply</option>
                    <option value="screen">Screen</option>
                    <option value="overlay">Overlay</option>
                </select>
                <div class="hint">Try Multiply or Screen if watermark looks missing</div>
            </div>
            
            <div class="settings-card">
                <h3>👤 Avatar Position</h3>
                <select id="avatar-position">
                    <option value="top-left" selected>Top Left</option>
                    <option value="top-right">Top Right</option>
                    <option value="bottom-left">Bottom Left</option>
                    <option value="bottom-right">Bottom Right</option>
                </select>
                <div class="hint">Author image will always be circular</div>
            </div>
            
            <div class="settings-card">
                <h3>📦 Bulk Generator</h3>
                <input id="bulk-count" type="number" min="1" max="200" value="10" />
                <button class="btn-generate" style="padding: 10px; font-size: 13px; margin-top: 10px;" onclick="generateBulk()" id="bulk-btn" disabled>
                    🚀 Generate Bulk
                </button>
            </div>

            <div class="settings-card">
                <h3>☁️ Upload to Google Drive</h3>
                <select id="upload-drive">
                    <option value="off" selected>Off</option>
                    <option value="on">On</option>
                </select>
                <div class="hint">Uploads PNG to Drive and returns share link</div>
            </div>
        </div>
        
        <div style="margin-top: 20px; position: relative; z-index: 1;">
            <button class="btn-generate" id="generate-btn" onclick="generateImage()" disabled>
                🎨 Generate Quote Image
            </button>
            <div class="hint" style="text-align: center; margin-top: 10px;">
                Image will be saved with format: &lt;Category&gt; - &lt;Quote&gt; - &lt;Author&gt; - &lt;DD-MM-YYYY_HHMM&gt;.png
            </div>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Creating your masterpiece with the selected design...</p>
            <div class="progress-wrap" id="progress-wrap"><div class="progress-bar" id="progress-bar"></div></div>
            <div class="progress-text" id="progress-text"></div>
        </div>
        
        <div class="result" id="result">
            <h3 id="result-title">✅ Success</h3>
            <p id="result-message"></p>
        </div>
    </div>
    
    <script>
        let selectedStyle = 'elegant';
        let allQuotes = {};
        let currentQuote = null;
        
        window.onload = function() {
            fetch('/api/topics')
                .then(r => r.json())
                .then(data => {
                    const status = document.getElementById('sheet-status');
                    status.textContent = data.topics && data.topics.length ? '✅ Sheet Connected' : '⚠️ Sheet Error';
                    const select = document.getElementById('topic');
                    data.topics.forEach(topic => {
                        const option = document.createElement('option');
                        option.value = topic;
                        option.textContent = topic;
                        select.appendChild(option);
                    });
                });

            fetch('/api/fonts')
                .then(r => r.json())
                .then(data => {
                    const fonts = (data && data.fonts) ? data.fonts : [];
                    const select = document.getElementById('font-select');
                    if (!select) return;
                    fonts.forEach(name => {
                        const opt = document.createElement('option');
                        opt.value = name;
                        opt.textContent = name;
                        select.appendChild(opt);
                    });
                })
                .catch(() => {});
        };

        
        function loadQuotes() {
            const topic = document.getElementById('topic').value;
            if (!topic) return;
            Promise.all([
                fetch(`/api/quotes/${topic}`).then(r => r.json()),
                fetch(`/api/remaining/${topic}`).then(r => r.json()).catch(() => ({ topic_total: 0, authors: {} }))
            ]).then(([qData, remData]) => {
                allQuotes = qData.quotes;
                const select = document.getElementById('quote-select');
                select.innerHTML = '<option value="">Choose quote...</option>';

                const remainingByAuthor = (remData && remData.authors) ? remData.authors : {};
                const remainingTotal = (remData && typeof remData.topic_total === 'number') ? remData.topic_total : 0;

                allQuotes.forEach((quote, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    const a = (quote.author || 'Unknown').toString();
                    const c = remainingByAuthor[a] || 0;
                    option.textContent = `${a} (${c})`;
                    select.appendChild(option);
                });
                select.onchange = function() {
                    const idx = this.value;
                    if (idx !== '') {
                        currentQuote = allQuotes[idx];
                        document.getElementById('current-quote').textContent = `"${currentQuote.quote}"`;
                        document.getElementById('current-author').textContent = `— ${currentQuote.author}`;
                        document.getElementById('quote-heading').textContent = (currentQuote.category || '').toString();
                        const a = (currentQuote.author || 'Unknown').toString();
                        const remaining = remainingByAuthor[a] || 0;
                        document.getElementById('meta-pill').textContent = `Remaining: ${remaining} (Topic remaining: ${remainingTotal})`;
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
            if (!currentQuote) return;

            const opacityRaw = document.getElementById('watermark-opacity').value;
            const watermark_opacity = Math.max(0, Math.min(1, parseFloat(opacityRaw || '0.7')));

            const qfsRaw = document.getElementById('quote-font-size').value;
            const quote_font_size = parseInt(qfsRaw || '52', 10);

            const afsRaw = document.getElementById('author-font-size').value;
            const author_font_size = parseInt(afsRaw || '30', 10);

            const wmsRaw = document.getElementById('watermark-size').value;
            const watermark_size_percent = Math.max(0.05, Math.min(0.40, (parseFloat(wmsRaw || '15') / 100.0)));

            const payload = {
                quote: currentQuote.quote,
                author: currentQuote.author,
                author_image: currentQuote.author_image || currentQuote.image || '',
                category: currentQuote.category || '',
                style: selectedStyle,
                font_name: document.getElementById('font-select').value || null,
                quote_font_size,
                author_font_size,
                watermark_size_percent,
                topic: document.getElementById('topic').value,
                row: currentQuote._row || null,
                watermark_opacity,
                watermark_blend: document.getElementById('watermark-blend').value,
                avatar_position: document.getElementById('avatar-position').value,
                upload_to_drive: (document.getElementById('upload-drive').value === 'on')
            };
            
            document.getElementById('loading').classList.add('show');
            document.getElementById('result').classList.remove('show');
            document.getElementById('generate-btn').disabled = true;
            
            startJob('single', payload)
                .then(jobId => pollJob(jobId, (data) => {
                    document.getElementById('loading').classList.remove('show');
                    document.getElementById('generate-btn').disabled = false;

                    if (!data.success) {
                        alert('Error: ' + (data.error || 'Unknown error'));
                        return;
                    }

                    const resultDiv = document.getElementById('result');
                    const title = document.getElementById('result-title');
                    const messageP = document.getElementById('result-message');

                    title.textContent = '✅ Image Generated Successfully';
                    const driveOn = (document.getElementById('upload-drive').value === 'on');
                    const driveHtml = data.drive_link
                        ? `☁️ <strong>Drive:</strong> <a href="${data.drive_link}" target="_blank">Open</a><br>`
                        : (driveOn ? `☁️ <strong>Drive:</strong> Failed (${(data.drive_error || 'no link')})<br>` : '');
                    messageP.innerHTML = `
                        📁 <strong>Saved to:</strong> ${data.image_path}<br>
                        🎨 <strong>Style:</strong> ${selectedStyle}<br>
                        ${driveHtml}
                        ${data.upload_result ? '📝 <strong>Sheet:</strong> ' + data.upload_result : ''}
                    `;
                    resultDiv.classList.add('show');
                }))
                .catch(err => {
                    document.getElementById('loading').classList.remove('show');
                    document.getElementById('generate-btn').disabled = false;
                    alert('Error: ' + err);
                });
        }
        
        function generateBulk() {
            const topic = document.getElementById('topic').value;
            if (!topic) {
                alert('Please select a topic first');
                return;
            }
            
            const count = parseInt(document.getElementById('bulk-count').value || '10', 10);
            const font_name = document.getElementById('font-select').value || null;
            const opacityRaw = document.getElementById('watermark-opacity').value;
            const watermark_opacity = Math.max(0, Math.min(1, parseFloat(opacityRaw || '0.7')));
            const watermark_blend = document.getElementById('watermark-blend').value;
            const avatar_position = document.getElementById('avatar-position').value;

            const qfsRaw = document.getElementById('quote-font-size').value;
            const quote_font_size = parseInt(qfsRaw || '52', 10);

            const afsRaw = document.getElementById('author-font-size').value;
            const author_font_size = parseInt(afsRaw || '30', 10);

            const wmsRaw = document.getElementById('watermark-size').value;
            const watermark_size_percent = Math.max(0.05, Math.min(0.40, (parseFloat(wmsRaw || '15') / 100.0)));

            const payload = {
                topic,
                count,
                style: selectedStyle,
                font_name,
                quote_font_size,
                author_font_size,
                watermark_size_percent,
                watermark_opacity,
                watermark_blend,
                avatar_position,
                upload_to_drive: (document.getElementById('upload-drive').value === 'on')
            };
            
            document.getElementById('loading').classList.add('show');
            document.getElementById('result').classList.remove('show');
            document.getElementById('generate-btn').disabled = true;
            document.getElementById('bulk-btn').disabled = true;
            
            startJob('bulk', payload)
                .then(jobId => pollJob(jobId, (data) => {
                    document.getElementById('loading').classList.remove('show');
                    document.getElementById('generate-btn').disabled = false;
                    document.getElementById('bulk-btn').disabled = false;

                    if (!data.success) {
                        alert('Error: ' + (data.error || 'Unknown error'));
                        return;
                    }

                    const resultDiv = document.getElementById('result');
                    const title = document.getElementById('result-title');
                    const messageP = document.getElementById('result-message');

                    title.textContent = `✅ ${data.generated_count} Images Generated!`;
                    const driveOn = (document.getElementById('upload-drive').value === 'on');
                    let driveHtml = '';
                    if (driveOn && data.drive_links && data.drive_links.length > 0) {
                        driveHtml = `☁️ <strong>Drive Links:</strong><br>`;
                        data.drive_links.forEach((link, i) => {
                            driveHtml += `<a href="${link}" target="_blank">Image ${i+1}</a><br>`;
                        });
                    }
                    
                    messageP.innerHTML = `
                        📁 <strong>Generated:</strong> ${data.generated_count} images<br>
                        📂 <strong>Folder:</strong> ${data.folder_name}<br>
                        🎨 <strong>Style:</strong> ${selectedStyle}<br>
                        ${driveHtml}
                        ${data.upload_result ? '📝 <strong>Sheet:</strong> ' + data.upload_result : ''}
                    `;
                    resultDiv.classList.add('show');
                }))
                .catch(err => {
                    document.getElementById('loading').classList.remove('show');
                    document.getElementById('generate-btn').disabled = false;
                    document.getElementById('bulk-btn').disabled = false;
                    alert('Error: ' + err);
                });
        }
        
        function startJob(type, payload) {
            return fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, ...payload })
            })
            .then(r => r.json())
            .then(data => data.job_id);
        }
        
        function pollJob(jobId, callback) {
            const checkJob = () => {
                fetch(`/api/job/${jobId}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.status === 'completed') {
                            callback(data);
                        } else if (data.status === 'failed') {
                            alert('Job failed: ' + (data.error || 'Unknown error'));
                        } else {
                            // Update progress
                            if (data.progress !== undefined) {
                                document.getElementById('progress-bar').style.width = `${Math.round(data.progress * 100)}%`;
                                document.getElementById('progress-wrap').style.display = 'block';
                                document.getElementById('progress-text').style.display = 'block';
                                document.getElementById('progress-text').textContent = data.message || `Processing... ${Math.round(data.progress * 100)}%`;
                            }
                            setTimeout(checkJob, 500);
                        }
                    })
                    .catch(err => {
                        console.error('Polling error:', err);
                        setTimeout(checkJob, 1000);
                    });
            };
            checkJob();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/topics')
def get_topics():
    try:
        topics = sheet_reader.get_topics()
        return jsonify({'topics': topics})
    except Exception as e:
        return jsonify({'error': str(e), 'topics': []})

@app.route('/api/quotes/<topic>')
def get_quotes(topic):
    try:
        quotes = sheet_reader.get_quotes(topic)
        return jsonify({'quotes': quotes})
    except Exception as e:
        return jsonify({'error': str(e), 'quotes': []})

@app.route('/api/remaining/<topic>')
def get_remaining(topic):
    try:
        remaining = sheet_reader.get_remaining_quotes(topic)
        return jsonify(remaining)
    except Exception as e:
        return jsonify({'error': str(e), 'topic_total': 0, 'authors': {}})

@app.route('/api/fonts')
def get_fonts():
    try:
        font_dir = Path('assets/fonts')
        if font_dir.exists():
            fonts = [f.stem for f in font_dir.glob('*.ttf') if f.stem.lower() != 'readme']
            return jsonify({'fonts': sorted(fonts)})
        return jsonify({'fonts': []})
    except Exception as e:
        return jsonify({'fonts': []})

@app.route('/api/generate', methods=['POST'])
def generate_image():
    data = request.get_json()
    job_id = str(uuid.uuid4())
    
    JOB_PROGRESS[job_id] = {
        'status': 'pending',
        'progress': 0,
        'message': 'Starting...'
    }
    
    # Start background job
    import threading
    thread = threading.Thread(target=process_generation_job, args=(job_id, data))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/api/job/<job_id>')
def get_job_status(job_id):
    job = JOB_PROGRESS.get(job_id, {'status': 'not_found'})
    return jsonify(job)

def process_generation_job(job_id, data):
    try:
        JOB_PROGRESS[job_id]['status'] = 'processing'
        JOB_PROGRESS[job_id]['progress'] = 0.05
        JOB_PROGRESS[job_id]['message'] = 'Loading quote data...'
        
        if data.get('type') == 'bulk':
            process_bulk_generation(job_id, data)
        else:
            process_single_generation(job_id, data)
            
    except Exception as e:
        JOB_PROGRESS[job_id]['status'] = 'failed'
        JOB_PROGRESS[job_id]['error'] = str(e)

def process_single_generation(job_id, data):
    quote = data.get('quote', '')
    author = data.get('author', '')
    category = data.get('category', '')
    style = data.get('style', 'elegant')
    font_name = data.get('font_name')
    quote_font_size = data.get('quote_font_size')
    author_font_size = data.get('author_font_size')
    watermark_size_percent = data.get('watermark_size_percent')
    watermark_opacity = data.get('watermark_opacity')
    watermark_blend = data.get('watermark_blend')
    avatar_position = data.get('avatar_position')
    author_image = data.get('author_image', '')
    upload_to_drive = data.get('upload_to_drive', False)
    
    JOB_PROGRESS[job_id]['progress'] = 0.25
    JOB_PROGRESS[job_id]['message'] = 'Rendering...'
    
    image_path = image_gen.generate(
        quote,
        author,
        style,
        category=category,
        author_image=str(author_image or ''),
        watermark_mode='corner',
        watermark_opacity=watermark_opacity,
        watermark_blend=str(watermark_blend or 'normal'),
        avatar_position=str(avatar_position or 'top-left'),
        font_name=str(font_name) if font_name else None,
        quote_font_size=int(quote_font_size) if quote_font_size is not None else None,
        author_font_size=int(author_font_size) if author_font_size is not None else None,
        watermark_size_percent=float(watermark_size_percent) if watermark_size_percent is not None else None,
        watermark_position='bottom-right'
    )

    filename = Path(image_path).name
    public_url = f"/generated/{filename}"
    absolute_url = f"{request.host_url.rstrip('/')}{public_url}"

    JOB_PROGRESS[job_id]['progress'] = 0.65
    JOB_PROGRESS[job_id]['message'] = 'Uploading to Drive...'

    drive_link = None
    drive_error = None
    if upload_to_drive:
        try:
            drive_link = drive_uploader.upload_image(image_path, data.get('topic'))
        except Exception as e:
            drive_error = str(e)

    JOB_PROGRESS[job_id]['progress'] = 0.85
    JOB_PROGRESS[job_id]['message'] = 'Updating sheet...'

    upload_result = None
    try:
        if data.get('topic') and data.get('row'):
            upload_result = sheet_reader.mark_as_generated(
                data.get('topic'), 
                data.get('row'), 
                str(absolute_url)
            )
    except Exception as e:
        upload_result = f"Error updating sheet: {e}"

    JOB_PROGRESS[job_id]['status'] = 'completed'
    JOB_PROGRESS[job_id]['progress'] = 1.0
    JOB_PROGRESS[job_id]['message'] = 'Complete!'
    JOB_PROGRESS[job_id].update({
        'success': True,
        'image_path': str(image_path),
        'public_url': public_url,
        'absolute_url': absolute_url,
        'drive_link': drive_link,
        'drive_error': drive_error,
        'upload_result': upload_result
    })

def process_bulk_generation(job_id, data):
    topic = data.get('topic', '')
    count = data.get('count', 10)
    style = data.get('style', 'elegant')
    font_name = data.get('font_name')
    quote_font_size = data.get('quote_font_size')
    author_font_size = data.get('author_font_size')
    watermark_size_percent = data.get('watermark_size_percent')
    watermark_opacity = data.get('watermark_opacity')
    watermark_blend = data.get('watermark_blend')
    avatar_position = data.get('avatar_position')
    upload_to_drive = data.get('upload_to_drive', False)

    JOB_PROGRESS[job_id]['progress'] = 0.10

    selected_quotes = sheet_reader.get_quotes(topic)[:count]
    total = len(selected_quotes)
    
    if total == 0:
        JOB_PROGRESS[job_id]['status'] = 'failed'
        JOB_PROGRESS[job_id]['error'] = 'No quotes found for this topic'
        return

    # Create output folder
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    folder_name = f"bulk_{topic}_{timestamp}"
    output_folder = Path('Generated_Images') / folder_name
    output_folder.mkdir(exist_ok=True)

    generated_paths = []
    drive_links = []

    for i, q in enumerate(selected_quotes, start=1):
        JOB_PROGRESS[job_id]['message'] = f'Generating {i}/{total}...'
        JOB_PROGRESS[job_id]['progress'] = 0.10 + (0.65 * (i / total))
        try:
            p = image_gen.generate(
                q.get('quote', ''),
                q.get('author', 'Unknown'),
                style,
                category=q.get('category', ''),
                author_image=str(q.get('author_image') or q.get('image') or ''),
                watermark_mode='corner',
                watermark_opacity=watermark_opacity,
                watermark_blend=str(watermark_blend or 'normal'),
                avatar_position=str(avatar_position or 'top-left'),
                font_name=str(font_name) if font_name else None,
                quote_font_size=int(quote_font_size) if quote_font_size is not None else None,
                author_font_size=int(author_font_size) if author_font_size is not None else None,
                watermark_size_percent=float(watermark_size_percent) if watermark_size_percent is not None else None,
                watermark_position='bottom-right'
            )
            
            # Move to bulk folder
            new_path = output_folder / Path(p).name
            Path(p).rename(new_path)
            generated_paths.append(str(new_path))
            
            # Upload to Drive if requested
            if upload_to_drive:
                try:
                    drive_link = drive_uploader.upload_image(str(new_path), topic)
                    if drive_link:
                        drive_links.append(drive_link)
                except Exception as e:
                    print(f"Drive upload failed for {new_path}: {e}")
            
        except Exception as e:
            print(f"Error generating image {i}: {e}")
    
    JOB_PROGRESS[job_id]['progress'] = 0.85
    JOB_PROGRESS[job_id]['message'] = 'Updating sheet...'

    # Mark quotes as generated
    try:
        for q in selected_quotes:
            if q.get('_row'):
                sheet_reader.mark_as_generated(topic, q.get('_row'), f"bulk_{folder_name}")
    except Exception as e:
        print(f"Error updating sheet: {e}")

    JOB_PROGRESS[job_id]['status'] = 'completed'
    JOB_PROGRESS[job_id]['progress'] = 1.0
    JOB_PROGRESS[job_id]['message'] = f'Complete! Generated {len(generated_paths)} images'
    JOB_PROGRESS[job_id].update({
        'success': True,
        'generated_count': len(generated_paths),
        'folder_name': folder_name,
        'drive_links': drive_links,
        'upload_result': f'Bulk generation completed for {len(generated_paths)} quotes'
    })

@app.route('/generated/<filename>')
def generated(filename):
    """Serve generated images"""
    return send_from_directory('Generated_Images', filename)

if __name__ == '__main__':
    # Create output directory
    Path('Generated_Images').mkdir(exist_ok=True)
    
    print("🚀 Starting Bulk Quotes Image Generator Dashboard")
    print("📊 Access at: http://localhost:5000")
    print("🎨 Features: 16 templates, smart filenames, Google Drive integration")
    
    app.run(debug=True, host='0.0.0.0', port=5000)