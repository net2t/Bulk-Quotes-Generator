#!/usr/bin/env python3
"""
Enhanced Web Dashboard for Quote Image Generator
- 16 design templates
- Better UI organization
- Watermark mode selector with color-match option
- Avatar position control
"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
import os
import json
import sys
from pathlib import Path
from datetime import datetime
from PIL import Image

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
    <title>Quote Image Generator - Enhanced</title>
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
            <div class="badge">✨ Enhanced Quote Generator v2.0</div>
            <div class="badge" id="sheet-status">🔌 Connecting...</div>
        </div>
        
        <h1>🎨 Quote Image Generator</h1>
        <p class="subtitle">16 Professional Design Templates • Always Circular Author Images • Smart Watermarks</p>
        
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
                <label for="upload-target">📝 Sheet Write-back</label>
                <select id="upload-target">
                    <option value="none">Off</option>
                    <option value="sheet" selected>On</option>
                </select>
            </div>
            <div class="control-group">
                <label for="mode">🔧 Mode</label>
                <select id="mode" onchange="toggleMode()">
                    <option value="sheet" selected>Use Sheet</option>
                    <option value="manual">Manual Input</option>
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
            <p class="quote-author" id="current-author"></p>
        </div>
        
        <div class="section-title">
            🎨 Design Templates
            <span class="new-badge">NEW</span>
        </div>
        
        <div class="category-label">📱 Original Styles</div>
        <div class="style-grid">
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
        
        <div class="category-label">🆕 New Enhanced Styles</div>
        <div class="style-grid">
            <div class="style-card" data-style="gradient_sunset" onclick="selectStyle('gradient_sunset')">
                <div class="style-icon">🌅</div>
                <div class="style-name">Gradient Sunset</div>
            </div>
            <div class="style-card" data-style="professional" onclick="selectStyle('professional')">
                <div class="style-icon">💼</div>
                <div class="style-name">Professional</div>
            </div>
            <div class="style-card" data-style="vintage" onclick="selectStyle('vintage')">
                <div class="style-icon">📜</div>
                <div class="style-name">Vintage</div>
            </div>
            <div class="style-card" data-style="nature" onclick="selectStyle('nature')">
                <div class="style-icon">🌿</div>
                <div class="style-name">Nature</div>
            </div>
            <div class="style-card" data-style="ocean" onclick="selectStyle('ocean')">
                <div class="style-icon">🌊</div>
                <div class="style-name">Ocean</div>
            </div>
            <div class="style-card" data-style="cosmic" onclick="selectStyle('cosmic')">
                <div class="style-icon">🌌</div>
                <div class="style-name">Cosmic</div>
            </div>
            <div class="style-card" data-style="minimalist_dark" onclick="selectStyle('minimalist_dark')">
                <div class="style-icon">🌑</div>
                <div class="style-name">Dark Minimal</div>
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
                <h3>💧 Watermark Mode</h3>
                <select id="watermark-mode">
                    <option value="corner" selected>Corner</option>
                    <option value="stripe">Diagonal Stripe</option>
                    <option value="color-match">Color Match</option>
                    <option value="subtle">Subtle Center</option>
                </select>
                <div class="hint">Color Match adapts watermark to image colors</div>
            </div>

            <div class="settings-card">
                <h3>🫧 Watermark Opacity</h3>
                <input id="watermark-opacity" type="number" min="0" max="1" step="0.05" value="0.70" />
                <div class="hint">0 = hidden, 1 = solid</div>
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
        </div>
        
        <div style="margin-top: 20px; position: relative; z-index: 1;">
            <button class="btn-generate" id="generate-btn" onclick="generateImage()" disabled>
                🎨 Generate Quote Image
            </button>
            <div class="hint" style="text-align: center; margin-top: 10px;">
                Image will be saved to Generated_Images/ folder
            </div>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Creating your masterpiece with the selected design...</p>
        </div>
        
        <div class="result" id="result">
            <h3 id="result-title">✅ Success</h3>
            <p id="result-message"></p>
        </div>
    </div>
    
    <script>
        let selectedStyle = 'bright';
        let allQuotes = {};
        let currentQuote = null;
        let mode = 'sheet';
        
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
        };

        function toggleMode() {
            mode = document.getElementById('mode').value;
            const bulkBtn = document.getElementById('bulk-btn');
            if (mode === 'manual') {
                bulkBtn.disabled = true;
                document.getElementById('generate-btn').disabled = false;
            } else {
                document.getElementById('generate-btn').disabled = true;
            }
        }
        
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
            if (mode === 'sheet' && !currentQuote) return;

            const opacityRaw = document.getElementById('watermark-opacity').value;
            const watermark_opacity = Math.max(0, Math.min(1, parseFloat(opacityRaw || '0.7')));

            const payload = {
                quote: currentQuote.quote,
                author: currentQuote.author,
                author_image: currentQuote.author_image || currentQuote.image || '',
                style: selectedStyle,
                topic: document.getElementById('topic').value,
                row: currentQuote._row || null,
                upload_target: document.getElementById('upload-target').value,
                watermark_mode: document.getElementById('watermark-mode').value,
                watermark_opacity,
                watermark_blend: document.getElementById('watermark-blend').value,
                avatar_position: document.getElementById('avatar-position').value
            };
            
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

                title.textContent = '✅ Image Generated Successfully';
                messageP.innerHTML = `
                    📁 <strong>Saved to:</strong> ${data.image_path}<br>
                    🎨 <strong>Style:</strong> ${selectedStyle}<br>
                    ${data.upload_result ? '📤 <strong>Upload:</strong> ' + data.upload_result : ''}
                `;
                resultDiv.classList.add('show');
            })
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
            const upload_target = document.getElementById('upload-target').value;
            const watermark_mode = document.getElementById('watermark-mode').value;
            const opacityRaw = document.getElementById('watermark-opacity').value;
            const watermark_opacity = Math.max(0, Math.min(1, parseFloat(opacityRaw || '0.7')));
            const watermark_blend = document.getElementById('watermark-blend').value;
            const avatar_position = document.getElementById('avatar-position').value;
            
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
                    watermark_mode,
                    watermark_opacity,
                    watermark_blend,
                    avatar_position
                })
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('loading').classList.remove('show');
                
                if (!data.success) {
                    alert('Error: ' + data.error);
                    return;
                }
                
                const resultDiv = document.getElementById('result');
                const messageP = document.getElementById('result-message');
                messageP.innerHTML = `
                    📦 <strong>Bulk Generation Complete!</strong><br>
                    ✅ Generated: ${data.generated} images<br>
                    🎨 Style: ${selectedStyle}<br>
                    📁 Folder: Generated_Images/
                `;
                resultDiv.classList.add('show');
            })
            .catch(err => {
                document.getElementById('loading').classList.remove('show');
                alert('Error: ' + err);
            });
        }
    </script>
</body>
</html>
'''

@app.route('/generated/<filename>')
def generated(filename):
    """Serve generated images"""
    return send_from_directory('Generated_Images', filename)

@app.route('/')
def index():
    """Main dashboard"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/topics')
def get_topics():
    """Get all topics"""
    if sheet_reader.connect():
        topics = sheet_reader.get_all_topics()
        return jsonify({'topics': topics})
    return jsonify({'topics': []})

@app.route('/api/quotes/<topic>')
def get_quotes(topic):
    """Get quotes for topic"""
    quotes = sheet_reader.get_quotes_by_topic(topic)
    return jsonify({'quotes': quotes})

@app.route('/api/remaining/<topic>')
def get_remaining(topic):
    """Get remaining (not Done) counts for a topic and authors"""
    if not sheet_reader.spreadsheet:
        sheet_reader.connect()
    counts = sheet_reader.get_remaining_counts(topic)
    return jsonify(counts)

@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate single image"""
    data = request.json
    quote = data.get('quote')
    author = data.get('author')
    style = data.get('style', 'minimal')
    author_image = data.get('author_image', '')
    topic = data.get('topic', '')
    row = data.get('row')
    upload_target = data.get('upload_target', 'none')
    watermark_mode = data.get('watermark_mode', 'corner')
    watermark_opacity = data.get('watermark_opacity')
    watermark_blend = data.get('watermark_blend', 'normal')
    avatar_position = data.get('avatar_position', 'top-left')
    
    try:
        # Generate image with enhanced options
        try:
            watermark_opacity = float(watermark_opacity) if watermark_opacity is not None else None
        except Exception:
            watermark_opacity = None

        image_path = image_gen.generate(
            quote,
            author,
            style,
            author_image=str(data.get('author_image') or ''),
            watermark_mode=str(watermark_mode or 'corner'),
            watermark_opacity=watermark_opacity,
            watermark_blend=str(watermark_blend or 'normal'),
            avatar_position=str(avatar_position or 'top-left')
        )

        filename = Path(image_path).name
        public_url = f"/generated/{filename}"
        absolute_url = f"{request.host_url.rstrip('/')}{public_url}"
        
        upload_result = "Saved locally"
        
        if upload_target == 'sheet':
            try:
                write_value = absolute_url
                if topic and row:
                    ok = sheet_reader.write_back(str(topic), int(row), str(write_value))
                    try:
                        with Image.open(image_path) as im:
                            dimensions = f"{im.width}x{im.height}"
                    except Exception:
                        dimensions = ""
                    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    sheet_reader.write_generation_meta(int(row), dimensions, ts)
                    upload_result = "✅ Written to sheet" if ok else "❌ Sheet write failed"
                else:
                    upload_result = "Missing topic/row"
            except Exception as e:
                upload_result = f"Sheet error: {e}"
        
        return jsonify({
            'success': True,
            'image_path': image_path,
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
    """Bulk generation"""
    data = request.json
    topic = data.get('topic')
    style = data.get('style', 'minimal')
    count = int(data.get('count', 10) or 10)
    upload_target = data.get('upload_target', 'none')
    watermark_mode = data.get('watermark_mode', 'corner')
    watermark_opacity = data.get('watermark_opacity')
    watermark_blend = data.get('watermark_blend', 'normal')
    avatar_position = data.get('avatar_position', 'top-left')
    
    if not topic:
        return jsonify({'success': False, 'error': 'Topic required'})
    if count < 1:
        return jsonify({'success': False, 'error': 'Count must be >= 1'})
    
    try:
        if not sheet_reader.spreadsheet:
            if not sheet_reader.connect():
                return jsonify({'success': False, 'error': 'Failed to connect to sheets'})
        
        quotes = sheet_reader.get_quotes_by_topic(topic)
        if not quotes:
            return jsonify({'success': False, 'error': f'No quotes for topic: {topic}'})
        
        import random
        if count >= len(quotes):
            random.shuffle(quotes)
            selected_quotes = quotes
        else:
            selected_quotes = random.sample(quotes, count)
        
        generated_paths = []
        generated_urls = []
        
        try:
            watermark_opacity = float(watermark_opacity) if watermark_opacity is not None else None
        except Exception:
            watermark_opacity = None

        for q in selected_quotes:
            try:
                p = image_gen.generate(
                    q.get('quote', ''),
                    q.get('author', 'Unknown'),
                    style,
                    author_image=str(q.get('author_image') or q.get('image') or ''),
                    watermark_mode=str(watermark_mode or 'corner'),
                    watermark_opacity=watermark_opacity,
                    watermark_blend=str(watermark_blend or 'normal'),
                    avatar_position=str(avatar_position or 'top-left')
                )
                generated_paths.append(p)
                fn = Path(p).name
                pu = f"/generated/{fn}"
                au = f"{request.host_url.rstrip('/')}{pu}"
                generated_urls.append(au)
            except Exception as e:
                print(f"Error generating: {e}")
                continue

        if upload_target == 'sheet' and generated_paths:
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
                print(f"Sheet write error: {e}")
        
        return jsonify({'success': True, 'generated': len(generated_paths)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Enhanced Quote Image Generator Dashboard v2.0")
    print("="*60)
    print("\n✨ Features:")
    print("   • 16 Professional Design Templates")
    print("   • Always Circular Author Images")
    print("   • Smart Watermark Modes (Corner/Stripe/Color-Match/Subtle)")
    print("   • Avatar Position Control")
    print("\n📱 Open your browser:")
    print("   http://localhost:8000\n")

    debug = str(os.getenv('DASHBOARD_DEBUG', '')).strip().lower() in ('1', 'true', 'yes', 'on')
    app.run(host='0.0.0.0', port=8000, debug=debug, use_reloader=False)
