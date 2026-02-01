---
name: quote-image-generator
description: Create beautiful quote images from Google Sheets data with multiple design styles, watermarks, and automatic Google Drive upload. Use when the user wants to (1) Generate quote images from their quotes database, (2) Create social media graphics with different design styles, (3) Batch process quotes with watermarks, (4) Upload images to Google Drive automatically, or (5) Build a visual dashboard for quote image generation.
---

# Quote Image Generator

## Overview

This skill creates professional quote images from a Google Sheets database with multiple design styles, watermark support, and automatic Google Drive upload through an interactive web dashboard.

## Directory Structure

The skill expects this structure in the user's project folder:
```
E:\New Gits\QUOTES/
├── Export/              # CSV files with quotes by topic
├── credentials.json     # Google Service Account credentials
├── Watermarks/          # Transparent PNG watermark files
└── Generated_Images/    # Output folder for created images
```

## Core Capabilities

### 1. Web Dashboard Interface
- Interactive HTML dashboard at http://localhost:8000
- Topic selection dropdown (from Google Sheets)
- Quote browsing and preview
- Design style selector
- One-click image generation
- Direct Google Drive link display

### 2. Image Generation Engine
- Five design styles: Minimal, Bright, Elegant, Bold, Modern
- Smart text wrapping and sizing
- Automatic watermark overlay
- High-quality output (1080x1080 default)
- Custom color palettes per topic

### 3. Google Integration
- Read quotes from Google Sheets via service account
- Upload to organized Drive folders (by topic)
- Return shareable Drive links
- Batch processing support

## Workflow

### Step 1: Environment Setup

Run the setup script to prepare the environment:
```bash
python scripts/setup_environment.py
```

This will:
- Check for credentials.json
- Create Watermarks and Generated_Images folders
- Install required packages
- Validate Google Sheets connection

### Step 2: Launch Dashboard

Start the web interface:
```bash
python scripts/dashboard.py
```

Opens browser to http://localhost:8000 with the interactive dashboard.

### Step 3: Generate Images

From the dashboard:
1. Select Topic - Choose from dropdown (auto-populated from sheets)
2. Browse Quotes - View all quotes for selected topic
3. Choose Style - Pick from 5 design templates
4. Generate - Click button to create image
5. Upload - Image auto-uploads to Google Drive
6. Share - Drive link displayed instantly

### Step 4: Batch Processing (Optional)

For bulk generation:
```bash
python scripts/batch_generator.py --topic "Motivation" --style "Bright" --count 10
```

## Design Styles

### Minimal
- Clean white/light background
- Simple sans-serif typography
- Subtle accent colors
- Professional appearance
- Best for: Corporate, Professional, Life quotes

### Bright
- Vibrant gradient backgrounds
- Bold contrasting colors
- High energy feel
- Eye-catching design
- Best for: Motivation, Inspiration, Success

### Elegant
- Soft pastel palettes
- Serif fonts
- Decorative borders
- Sophisticated look
- Best for: Love, Poetry, Philosophy

### Bold
- Strong solid color blocks
- Heavy typography
- Maximum impact
- Modern geometric shapes
- Best for: Humor, Truth, Time quotes

### Modern
- Minimalist geometric design
- Contemporary fonts
- Negative space usage
- Tech-forward aesthetic
- Best for: Wisdom, Writing, Travel

## Configuration

Edit references/config.json to customize settings.

## Scripts Reference

### dashboard.py
Main Flask web server providing the UI. Handles all user interactions and orchestrates other components.

### image_generator.py
Core image creation using Pillow (PIL).

### google_drive_uploader.py
Google Drive API integration for uploads.

### sheet_reader.py
Google Sheets data access and caching.

### batch_generator.py
Batch processing utility with CLI support.

### setup_environment.py
Initial setup and validation helper.

## Troubleshooting

See references/troubleshooting.md for common issues and solutions.
