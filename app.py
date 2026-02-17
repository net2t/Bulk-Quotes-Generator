#!/usr/bin/env python3
"""
AI Quote Generator Pro - Backend
Bulk Social Media Content Generator with AI
Features:
- Hugging Face AI integration (text-to-prompt + image generation)
- Multiple storage providers (ImgBB, Cloudinary, Google Drive)
- 6 modern design styles
- Bulk processing with Google Sheets
- Custom logo/watermark support
"""

import os
import sys
import json
import uuid
import time
import base64
import zipfile
import requests
import threading
from pathlib import Path
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Image processing
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    PIL_OK = True
except ImportError:
    PIL_OK = False
    print("[ERROR] PIL not installed. Run: pip install pillow")

# Google Sheets
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    SHEETS_OK = True
except ImportError:
    SHEETS_OK = False
    print("[WARN] Google Sheets support not available. Install: pip install gspread oauth2client")

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "Generated_Images"
TEMP_DIR = BASE_DIR / "temp"
LOGOS_DIR = BASE_DIR / "Watermarks"

OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
LOGOS_DIR.mkdir(exist_ok=True)

# Job tracking
JOBS: Dict[str, dict] = {}

# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS / DEFAULTS
# ══════════════════════════════════════════════════════════════════════════════

def _load_json_settings() -> dict:
    try:
        cfg_path = BASE_DIR / "references" / "config.json"
        if cfg_path.exists():
            return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


SETTINGS = _load_json_settings()


def _get_setting(path: str, default=None):
    cur = SETTINGS
    for part in str(path or "").split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur.get(part)
    return cur if cur is not None else default


def _env(name: str, default=None):
    v = os.environ.get(name)
    if v is None or str(v).strip() == "":
        return default
    return v


def _get_sheet_url() -> Optional[str]:
    return _env("GOOGLE_SHEET_URL", _get_setting("google_sheets.sheet_url"))


def _get_hf_token() -> Optional[str]:
    return _env("HUGGINGFACE_API_TOKEN", _env("HF_API_TOKEN"))


def _get_storage_secret(provider: str) -> Optional[str]:
    p = str(provider or "").strip().lower()
    if p == "imgbb":
        return _env("IMGBB_API_KEY")
    if p == "cloudinary":
        return _env("CLOUDINARY_CREDENTIALS")
    if p == "gdrive":
        return _env("GOOGLE_DRIVE_CREDENTIALS_PATH", str(BASE_DIR / "credentials.json"))
    if p == "local":
        return ""
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  HUGGING FACE AI MODELS
# ══════════════════════════════════════════════════════════════════════════════

class HuggingFaceAPI:
    """Hugging Face API client for AI models"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {"Authorization": f"Bearer {api_token}"}
    
    def generate_image_prompt(self, quote: str, author: str, style: str, model: str) -> str:
        """Generate creative image prompt from quote using LLM"""
        
        prompt = f"""Based on this quote: "{quote}" by {author}
Design Style: {style}

Create a detailed image generation prompt that captures the essence and mood of this quote.
The prompt should describe visual elements, colors, atmosphere, and artistic style.
Keep it under 100 words, focus on visual descriptions only.

Image Prompt:"""
        
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 150,
                "temperature": 0.7,
                "top_p": 0.9,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "").strip()
                # Clean up the response
                generated_text = generated_text.replace("Image Prompt:", "").strip()
                return generated_text if generated_text else self._fallback_prompt(quote, style)
            
            return self._fallback_prompt(quote, style)
            
        except Exception as e:
            print(f"[WARN] Prompt generation failed: {e}")
            return self._fallback_prompt(quote, style)
    
    def _fallback_prompt(self, quote: str, style: str) -> str:
        """Fallback prompt if AI generation fails"""
        mood_map = {
            "gradient-blur": "soft gradient background with bokeh lights, dreamy atmosphere",
            "dark-minimal": "dark minimalist design, geometric shapes, clean lines, navy blue",
            "vibrant-pop": "vibrant pop art style, bold colors, pink and cyan, energetic",
            "bold-geo": "bold geometric shapes, angular design, orange teal yellow",
            "glassmorphism": "frosted glass effect, gradient orbs, modern blur",
            "abstract-art": "abstract artistic illustration, creative composition, vivid colors"
        }
        
        return f"{mood_map.get(style, 'beautiful background')}, high quality, professional design"
    
    def generate_image(self, prompt: str, model: str) -> Optional[bytes]:
        """Generate image from prompt using diffusion model"""
        
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "num_inference_steps": 30,
                "guidance_scale": 7.5
            }
        }
        
        try:
            response = requests.post(api_url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            print(f"[ERROR] Image generation failed: {e}")
            return None

# ══════════════════════════════════════════════════════════════════════════════
#  STORAGE PROVIDERS
# ══════════════════════════════════════════════════════════════════════════════

class StorageProvider:
    """Base class for storage providers"""
    
    def upload(self, image_path: str, filename: str) -> Optional[str]:
        raise NotImplementedError


class LocalStorage(StorageProvider):
    """No-op storage provider that keeps files locally and returns a local URL."""

    def __init__(self, base_url: str = "/Generated_Images"):
        self.base_url = base_url

    def upload(self, image_path: str, filename: str) -> Optional[str]:
        try:
            # File already exists at image_path; just expose via static route.
            return f"{self.base_url}/{os.path.basename(image_path)}"
        except Exception:
            return None


class ImgBBStorage(StorageProvider):
    """ImgBB image hosting"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def upload(self, image_path: str, filename: str) -> Optional[str]:
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            response = requests.post(
                'https://api.imgbb.com/1/upload',
                data={
                    'key': self.api_key,
                    'image': image_data,
                    'name': filename
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                return data['data']['url']
            
            return None
            
        except Exception as e:
            print(f"[ERROR] ImgBB upload failed: {e}")
            return None


class CloudinaryStorage(StorageProvider):
    """Cloudinary cloud storage"""
    
    def __init__(self, credentials: str):
        # Format: cloud_name:api_key:api_secret
        parts = credentials.split(':')
        if len(parts) != 3:
            raise ValueError("Cloudinary credentials format: cloud_name:api_key:api_secret")
        
        self.cloud_name, self.api_key, self.api_secret = parts
    
    def upload(self, image_path: str, filename: str) -> Optional[str]:
        try:
            import cloudinary
            import cloudinary.uploader
            
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            
            result = cloudinary.uploader.upload(
                image_path,
                public_id=filename.replace('.png', ''),
                folder='quotes'
            )
            
            return result['secure_url']
            
        except Exception as e:
            print(f"[ERROR] Cloudinary upload failed: {e}")
            return None


class GoogleDriveStorage(StorageProvider):
    """Google Drive storage"""
    
    def __init__(self, credentials_path: str):
        if not SHEETS_OK:
            raise RuntimeError("Google Sheets libraries not installed")
        
        self.credentials_path = credentials_path
    
    def upload(self, image_path: str, filename: str) -> Optional[str]:
        try:
            from pydrive.auth import GoogleAuth
            from pydrive.drive import GoogleDrive
            
            gauth = GoogleAuth()
            gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path,
                ['https://www.googleapis.com/auth/drive']
            )
            
            drive = GoogleDrive(gauth)
            
            file = drive.CreateFile({
                'title': filename,
                'parents': [{'id': 'root'}]
            })
            file.SetContentFile(image_path)
            file.Upload()
            
            # Make publicly accessible
            file.InsertPermission({
                'type': 'anyone',
                'value': 'anyone',
                'role': 'reader'
            })
            
            return file['alternateLink']
            
        except Exception as e:
            print(f"[ERROR] Google Drive upload failed: {e}")
            return None

# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN STYLES
# ══════════════════════════════════════════════════════════════════════════════

class QuoteImageGenerator:
    """Generate quote images with multiple design styles"""
    
    STYLES = {
        "gradient-blur": {
            "bg_colors": [(255, 180, 150), (200, 150, 255), (150, 200, 255)],
            "text_color": (255, 255, 255),
            "blur_radius": 20,
            "gradient": True
        },
        "dark-minimal": {
            "bg_colors": [(20, 30, 48), (30, 45, 70)],
            "text_color": (255, 255, 255),
            "blur_radius": 0,
            "gradient": True,
            "geometric": True
        },
        "vibrant-pop": {
            "bg_colors": [(255, 20, 147), (0, 191, 255), (255, 215, 0)],
            "text_color": (255, 255, 255),
            "blur_radius": 0,
            "gradient": False,
            "bold": True
        },
        "bold-geo": {
            "bg_colors": [(255, 127, 80), (64, 224, 208), (255, 215, 0)],
            "text_color": (40, 40, 40),
            "blur_radius": 0,
            "gradient": False,
            "geometric": True
        },
        "glassmorphism": {
            "bg_colors": [(135, 206, 250), (255, 182, 193), (221, 160, 221)],
            "text_color": (255, 255, 255),
            "blur_radius": 30,
            "gradient": True,
            "glass": True
        },
        "abstract-art": {
            "bg_colors": [(255, 99, 71), (30, 144, 255), (50, 205, 50)],
            "text_color": (255, 255, 255),
            "blur_radius": 5,
            "gradient": True,
            "artistic": True
        }
    }
    
    def __init__(self, width: int = 1080, height: int = 1080):
        if not PIL_OK:
            raise RuntimeError("PIL not available")
        
        self.width = width
        self.height = height
    
    def generate(self, 
                 quote: str,
                 author: str,
                 style: str,
                 ai_bg_image: Optional[bytes] = None,
                 logo_path: Optional[str] = None,
                 output_path: Optional[str] = None) -> str:
        """Generate quote image"""
        
        if style not in self.STYLES:
            style = "gradient-blur"
        
        style_config = self.STYLES[style]
        
        # Create base image
        if ai_bg_image:
            # Use AI-generated background
            try:
                bg = Image.open(BytesIO(ai_bg_image))
                bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
                bg = bg.convert('RGB')
            except:
                bg = self._create_gradient_background(style_config)
        else:
            bg = self._create_gradient_background(style_config)
        
        # Apply style effects
        if style_config.get('blur_radius', 0) > 0:
            bg = bg.filter(ImageFilter.GaussianBlur(style_config['blur_radius']))
        
        # Add overlay for text readability
        overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        if style_config.get('glass'):
            # Glassmorphism effect
            overlay_draw.rounded_rectangle(
                [(100, 200), (self.width - 100, self.height - 200)],
                radius=30,
                fill=(255, 255, 255, 30)
            )
        else:
            # Dark overlay for text contrast
            overlay_draw.rectangle(
                [(0, 0), (self.width, self.height)],
                fill=(0, 0, 0, 60)
            )
        
        bg = Image.alpha_composite(bg.convert('RGBA'), overlay).convert('RGB')
        
        # Draw text
        draw = ImageDraw.Draw(bg)
        
        # Load fonts
        try:
            quote_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            quote_font = ImageFont.load_default()
            author_font = ImageFont.load_default()
        
        # Draw quote
        quote_text = f'"{quote}"'
        quote_wrapped = self._wrap_text(quote_text, quote_font, self.width - 200)
        
        y_offset = self.height // 3
        for line in quote_wrapped:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            line_width = bbox[2] - bbox[0]
            x = (self.width - line_width) // 2
            
            # Text shadow
            draw.text((x + 2, y_offset + 2), line, font=quote_font, fill=(0, 0, 0, 128))
            # Main text
            draw.text((x, y_offset), line, font=quote_font, fill=style_config['text_color'])
            
            y_offset += bbox[3] - bbox[1] + 20
        
        # Draw author
        author_text = f"— {author}"
        author_bbox = draw.textbbox((0, 0), author_text, font=author_font)
        author_width = author_bbox[2] - author_bbox[0]
        author_x = (self.width - author_width) // 2
        author_y = y_offset + 40
        
        draw.text((author_x + 2, author_y + 2), author_text, font=author_font, fill=(0, 0, 0, 128))
        draw.text((author_x, author_y), author_text, font=author_font, fill=style_config['text_color'])
        
        # Add logo/watermark
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path)
                logo_size = min(self.width // 8, 150)
                logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # Position: bottom-right
                logo_x = self.width - logo_size - 40
                logo_y = self.height - logo_size - 40
                
                if logo.mode == 'RGBA':
                    bg.paste(logo, (logo_x, logo_y), logo)
                else:
                    bg.paste(logo, (logo_x, logo_y))
            except Exception as e:
                print(f"[WARN] Logo placement failed: {e}")
        
        # Save
        if not output_path:
            output_path = str(OUTPUT_DIR / f"quote_{uuid.uuid4().hex[:8]}.png")
        
        bg.save(output_path, 'PNG', quality=95, optimize=True)
        return output_path
    
    def _create_gradient_background(self, config: dict) -> Image.Image:
        """Create gradient background"""
        bg = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(bg)
        
        colors = config['bg_colors']
        
        if config.get('gradient'):
            # Smooth gradient
            for y in range(self.height):
                ratio = y / self.height
                if len(colors) == 2:
                    r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
                    g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
                    b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
                else:
                    idx = int(ratio * (len(colors) - 1))
                    local_ratio = (ratio * (len(colors) - 1)) - idx
                    next_idx = min(idx + 1, len(colors) - 1)
                    
                    r = int(colors[idx][0] * (1 - local_ratio) + colors[next_idx][0] * local_ratio)
                    g = int(colors[idx][1] * (1 - local_ratio) + colors[next_idx][1] * local_ratio)
                    b = int(colors[idx][2] * (1 - local_ratio) + colors[next_idx][2] * local_ratio)
                
                draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        else:
            # Solid or geometric
            draw.rectangle([(0, 0), (self.width, self.height)], fill=colors[0])
            
            if config.get('geometric'):
                # Add geometric shapes
                import random
                for _ in range(5):
                    color = random.choice(colors)
                    size = random.randint(100, 300)
                    x = random.randint(0, self.width - size)
                    y = random.randint(0, self.height - size)
                    draw.ellipse([(x, y), (x + size, y + size)], fill=color + (50,))
        
        return bg
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Wrap text to fit width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

# ══════════════════════════════════════════════════════════════════════════════
#  GOOGLE SHEETS INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

class GoogleSheetsReader:
    """Read quotes from Google Sheets"""
    
    EXPECTED_COLUMNS = [
        'S#', 'LENGTH', 'CATEGORY', 'AUTHOR', 'QUOTE', 'TAGS',
        'IMAGE', 'AI_PROMPT', 'DESIGN_STYLE', 'COLOR_SCHEME',
        'PREVIEW_LINK', 'STATUS', 'DIMENSIONS', 'GENERATED_AT'
    ]
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        if not SHEETS_OK:
            raise RuntimeError("Google Sheets libraries not installed")
        
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        self.client = gspread.authorize(creds)
    
    def read_quotes(self, sheet_url: str) -> List[Dict]:
        """Read all quotes from sheet"""
        try:
            sheet = self.client.open_by_url(sheet_url).sheet1
            records = sheet.get_all_records()
            
            quotes = []
            for i, record in enumerate(records, start=2):  # Start from row 2 (after header)
                if record.get('QUOTE'):
                    quotes.append({
                        'row': i,
                        'quote': str(record.get('QUOTE', '')).strip(),
                        'author': str(record.get('AUTHOR', 'Unknown')).strip(),
                        'category': str(record.get('CATEGORY', '')).strip(),
                        'tags': str(record.get('TAGS', '')).strip(),
                        'length': str(record.get('LENGTH', '')).strip(),
                    })
            
            return quotes
            
        except Exception as e:
            print(f"[ERROR] Failed to read sheet: {e}")
            return []
    
    def update_row(self, sheet_url: str, row: int, updates: Dict) -> bool:
        """Update specific columns in a row"""
        try:
            sheet = self.client.open_by_url(sheet_url).sheet1
            headers = sheet.row_values(1)
            
            for column, value in updates.items():
                if column in headers:
                    col_index = headers.index(column) + 1
                    sheet.update_cell(row, col_index, value)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to update row {row}: {e}")
            return False

# ══════════════════════════════════════════════════════════════════════════════
#  BULK PROCESSING
# ══════════════════════════════════════════════════════════════════════════════

def process_bulk_generation(job_id: str, payload: dict):
    """Background task for bulk generation"""
    
    job = JOBS[job_id]
    
    try:
        # Extract config
        sheet_url = payload['sheet_url']
        design_style = payload['design_style']
        storage_provider = payload['storage_provider']
        storage_api_key = payload['storage_api_key']
        hf_token = payload['hf_token']
        prompt_model = payload['prompt_model']
        image_model = payload['image_model']
        logo_base64 = payload.get('logo')
        watermark_file = payload.get('watermark_file')
        
        # Save logo if provided (overrides watermark selection)
        logo_path = None
        if logo_base64:
            logo_data = base64.b64decode(logo_base64.split(',')[1])
            logo_path = str(LOGOS_DIR / f"logo_{job_id}.png")
            with open(logo_path, 'wb') as f:
                f.write(logo_data)
        elif watermark_file:
            # Use selectable watermark from Watermarks folder
            candidate = (LOGOS_DIR / str(watermark_file)).resolve()
            try:
                if LOGOS_DIR.resolve() in candidate.parents and candidate.exists():
                    logo_path = str(candidate)
            except Exception:
                logo_path = None
        
        # Initialize components
        hf_api = HuggingFaceAPI(hf_token)
        generator = QuoteImageGenerator()
        
        # Storage
        if storage_provider == 'imgbb':
            storage = ImgBBStorage(storage_api_key)
        elif storage_provider == 'cloudinary':
            storage = CloudinaryStorage(storage_api_key)
        elif storage_provider == 'gdrive':
            storage = GoogleDriveStorage(storage_api_key)
        elif storage_provider == 'local':
            storage = LocalStorage()
        else:
            raise ValueError(f"Unknown storage provider: {storage_provider}")
        
        # Read quotes from sheet
        job['message'] = 'Reading quotes from Google Sheet...'
        job['progress'] = 10
        
        sheets_reader = GoogleSheetsReader() if SHEETS_OK else None
        if sheets_reader:
            quotes = sheets_reader.read_quotes(sheet_url)
        else:
            # Fallback: mock data for testing
            quotes = []
        
        if not quotes:
            raise ValueError("No quotes found in sheet")
        
        total_quotes = len(quotes)
        results = []
        processed = 0
        success = 0
        failed = 0
        
        # Process each quote
        for i, quote_data in enumerate(quotes):
            try:
                job['message'] = f"Processing quote {i + 1}/{total_quotes}..."
                job['progress'] = 10 + int((i / total_quotes) * 80)
                job['processed'] = processed
                job['success'] = success
                job['failed'] = failed
                
                quote = quote_data['quote']
                author = quote_data['author']
                row = quote_data['row']
                
                # Step 1: Generate AI prompt
                ai_prompt = hf_api.generate_image_prompt(quote, author, design_style, prompt_model)
                
                # Step 2: Generate background image
                bg_image_bytes = hf_api.generate_image(ai_prompt, image_model)
                
                # Step 3: Create quote image
                output_path = generator.generate(
                    quote=quote,
                    author=author,
                    style=design_style,
                    ai_bg_image=bg_image_bytes,
                    logo_path=logo_path
                )
                
                # Step 4: Upload to storage
                filename = f"quote_{row}_{uuid.uuid4().hex[:8]}.png"
                image_url = storage.upload(output_path, filename)
                
                if image_url:
                    # Update Google Sheet
                    if sheets_reader:
                        sheets_reader.update_row(sheet_url, row, {
                            'IMAGE': image_url,
                            'AI_PROMPT': ai_prompt,
                            'DESIGN_STYLE': design_style,
                            'PREVIEW_LINK': image_url,
                            'STATUS': 'Generated',
                            'DIMENSIONS': '1080x1080',
                            'GENERATED_AT': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                    
                    results.append({
                        'quote': quote,
                        'author': author,
                        'image_url': image_url,
                        'ai_prompt': ai_prompt,
                        'style': design_style,
                        'local_path': output_path
                    })
                    
                    success += 1
                else:
                    failed += 1
                
                processed += 1
                
                # Small delay to avoid rate limits
                time.sleep(1)
                
            except Exception as e:
                print(f"[ERROR] Failed to process quote {i + 1}: {e}")
                failed += 1
                processed += 1
        
        # Complete
        job['status'] = 'completed'
        job['progress'] = 100
        job['message'] = f'Completed! {success} success, {failed} failed'
        job['processed'] = processed
        job['success'] = success
        job['failed'] = failed
        job['results'] = results
        
    except Exception as e:
        job['status'] = 'failed'
        job['error'] = str(e)
        job['message'] = f'Error: {str(e)}'
        print(f"[ERROR] Bulk generation failed: {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  API ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return send_file('index.html')


@app.route('/api/settings')
def api_settings():
    """Return non-secret settings to drive UI selections."""
    try:
        watermarks = []
        try:
            for p in sorted(LOGOS_DIR.glob('*.png')):
                watermarks.append(p.name)
        except Exception:
            watermarks = []

        default_storage = str(_env('DEFAULT_STORAGE_PROVIDER', 'imgbb')).strip().lower()
        if default_storage not in ('imgbb', 'cloudinary', 'gdrive', 'local'):
            default_storage = 'imgbb'

        return jsonify({
            'ok': True,
            'data_source_options': ['google_sheets'],
            'default_data_source': 'google_sheets',
            'sheet_url_fixed': True,
            'storage_options': ['imgbb', 'cloudinary', 'gdrive', 'local'],
            'default_storage_provider': default_storage,
            'ai_options': ['huggingface'],
            'default_ai_provider': 'huggingface',
            'watermark_options': watermarks,
            'default_watermark': watermarks[0] if watermarks else None,
        })
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/Generated_Images/<path:filename>')
def serve_generated_images(filename: str):
    return send_from_directory(str(OUTPUT_DIR), filename)


@app.route('/Watermarks/<path:filename>')
def serve_watermarks(filename: str):
    return send_from_directory(str(LOGOS_DIR), filename)

@app.route('/api/bulk-generate', methods=['POST'])
def api_bulk_generate():
    """Start bulk generation job"""
    try:
        payload = request.get_json() or {}

        # Allow UI to omit values; fall back to settings/env.
        sheet_url = payload.get('sheet_url') or _get_sheet_url()
        design_style = payload.get('design_style')
        storage_provider = payload.get('storage_provider')
        storage_api_key = payload.get('storage_api_key') or _get_storage_secret(storage_provider)
        hf_token = payload.get('hf_token') or _get_hf_token()

        # Validate
        if not sheet_url:
            return jsonify({'success': False, 'error': 'Missing sheet_url (configure GOOGLE_SHEET_URL or references/config.json)'}), 400
        if not design_style:
            return jsonify({'success': False, 'error': 'Missing design_style'}), 400
        if not storage_provider:
            return jsonify({'success': False, 'error': 'Missing storage_provider'}), 400
        if storage_provider != 'local' and not storage_api_key:
            return jsonify({'success': False, 'error': f'Missing storage_api_key for provider: {storage_provider}'}), 400
        if not hf_token:
            return jsonify({'success': False, 'error': 'Missing hf_token (configure HUGGINGFACE_API_TOKEN or HF_API_TOKEN)'}), 400

        payload['sheet_url'] = sheet_url
        payload['storage_api_key'] = storage_api_key
        payload['hf_token'] = hf_token
        
        # Create job
        job_id = uuid.uuid4().hex
        JOBS[job_id] = {
            'status': 'running',
            'progress': 0,
            'message': 'Initializing...',
            'processed': 0,
            'success': 0,
            'failed': 0,
            'results': []
        }
        
        # Start background thread
        thread = threading.Thread(target=process_bulk_generation, args=(job_id, payload))
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'job_id': job_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/job-status/<job_id>')
def api_job_status(job_id):
    """Get job status"""
    job = JOBS.get(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job)

@app.route('/api/download-all', methods=['POST'])
def api_download_all():
    """Download all generated images as ZIP"""
    try:
        data = request.get_json()
        images = data.get('images', [])
        
        # Create ZIP
        zip_path = TEMP_DIR / f"quotes_{uuid.uuid4().hex[:8]}.zip"
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for img in images:
                local_path = img.get('local_path')
                if local_path and os.path.exists(local_path):
                    zipf.write(local_path, os.path.basename(local_path))
        
        return send_file(zip_path, as_attachment=True, download_name='quotes.zip')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("\n" + "="*70)
    print("  🎨 AI Quote Generator Pro - Bulk Social Media Content Creator")
    print("="*70)
    print("\n  ✨ Features:")
    print("     • 6 Modern Design Styles")
    print("     • Hugging Face AI Integration")
    print("     • Multiple Storage Providers (ImgBB, Cloudinary, Google Drive)")
    print("     • Bulk Processing with Google Sheets")
    print("     • Custom Logo Support")
    print("\n  🌐 Server: http://localhost:5000")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
