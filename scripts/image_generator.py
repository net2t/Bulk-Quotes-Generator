#!/usr/bin/env python3
"""
Enhanced Image Generator
Creates beautiful quote images with multiple design styles and templates
- Always uses circular author images
- Color-matched watermark modes
- 12+ design templates
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance
from pathlib import Path
import textwrap
import random
import io
import urllib.request
import math
import time
from colorsys import rgb_to_hls, hls_to_rgb

class QuoteImageGenerator:
    def __init__(self, output_dir="Generated_Images", watermark_dir="Watermarks"):
        self.output_dir = Path(output_dir)
        self.watermark_dir = Path(watermark_dir)
        self.output_dir.mkdir(exist_ok=True)

        self._font_regular_path = None
        self._font_bold_path = None
        self._fonts_map = {}
        self._selected_font_regular_path = None
        self._selected_font_bold_path = None
        self._init_custom_fonts()

        # Default image size
        self.width = 1080
        self.height = 1080

        self.quote_font_size = 52
        self.author_font_size = 30

        # Design styles - Enhanced with more options
        self.styles = {
            'elegant': self.elegant_style,
            'modern': self.modern_style,
            'neon': self.neon_style,
            'vintage': self.vintage_style,
            'minimalist_dark': self.minimalist_dark_style,
            'creative_split': self.creative_split_style,
            'geometric': self.geometric_style,
            'artistic': self.artistic_style,
        }

    def _init_custom_fonts(self):
        """Initialize custom fonts from assets/fonts directory"""
        fonts_dir = Path("assets") / "fonts"
        if not fonts_dir.exists():
            return
        ttf_files = sorted(list(fonts_dir.glob("*.ttf")))
        if not ttf_files:
            return

        self._fonts_map = {p.stem: p for p in ttf_files}

        bold_candidates = [p for p in ttf_files if "bold" in p.stem.lower()]
        self._font_regular_path = ttf_files[0]
        self._font_bold_path = bold_candidates[0] if bold_candidates else ttf_files[0]

        self._selected_font_regular_path = self._font_regular_path
        self._selected_font_bold_path = self._font_bold_path

    def get_available_fonts(self):
        """Return list of available font names from assets/fonts (stems)."""
        try:
            return sorted(list(self._fonts_map.keys()))
        except Exception:
            return []

    def set_font(self, font_name: str | None):
        """Select a font by file stem (from assets/fonts).

        If not found or empty, reverts to default custom font selection.
        """
        name = (font_name or '').strip()
        if not name:
            self._selected_font_regular_path = self._font_regular_path
            self._selected_font_bold_path = self._font_bold_path
            return

        p = self._fonts_map.get(name)
        if not p:
            self._selected_font_regular_path = self._font_regular_path
            self._selected_font_bold_path = self._font_bold_path
            return

        self._selected_font_regular_path = p
        self._selected_font_bold_path = p

    def get_font(self, size, bold=False):
        """Get a font, falling back to default if custom fonts unavailable"""
        try:
            if self._selected_font_regular_path:
                font_path = self._selected_font_bold_path if bold else self._selected_font_regular_path
                return ImageFont.truetype(str(font_path), size)
            if bold:
                return ImageFont.truetype("arial.ttf", size)
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()

    def extract_dominant_color(self, image):
        """Extract dominant color from image for color-matching"""
        try:
            img_small = image.resize((50, 50))
            pixels = list(img_small.getdata())
            
            # Get average color
            r_avg = sum(p[0] for p in pixels) // len(pixels)
            g_avg = sum(p[1] for p in pixels) // len(pixels)
            b_avg = sum(p[2] for p in pixels) // len(pixels)
            
            return (r_avg, g_avg, b_avg)
        except:
            return (100, 100, 100)

    def adjust_color_brightness(self, color, factor):
        """Adjust color brightness"""
        r, g, b = color
        h, l, s = rgb_to_hls(r/255, g/255, b/255)
        l = max(0, min(1, l * factor))
        r, g, b = hls_to_rgb(h, l, s)
        return (int(r*255), int(g*255), int(b*255))

    def add_avatar(self, image, author_image: str, opacity: float = 0.95, size_percent: float = 0.14, position: str = 'top-left'):
        """
        Add a circular author image with enhanced styling
        
        Args:
            image: Base image
            author_image: URL or path to author image
            opacity: Avatar opacity (0.0 - 1.0)
            size_percent: Size as percentage of image dimensions
            position: 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'
        """
        if not author_image:
            return image

        try:
            img = image.convert('RGBA')
            
            # Load avatar image
            if str(author_image).strip().lower().startswith('http'):
                with urllib.request.urlopen(str(author_image).strip(), timeout=6) as resp:
                    data = resp.read()
                avatar = Image.open(io.BytesIO(data)).convert('RGBA')
            else:
                avatar = Image.open(str(author_image)).convert('RGBA')

            # Calculate size
            max_size = int(min(self.width, self.height) * size_percent)
            avatar.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Make it square and crop to circle
            size = min(avatar.width, avatar.height)
            left = (avatar.width - size) // 2
            top = (avatar.height - size) // 2
            avatar = avatar.crop((left, top, left + size, top + size))

            # Create circular mask
            mask = Image.new('L', (size, size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, size, size), fill=255)

            # Apply opacity
            alpha = avatar.split()[3].point(lambda p: int(p * opacity))
            avatar.putalpha(alpha)

            # Add border for better visibility
            bordered = Image.new('RGBA', (size + 8, size + 8), (255, 255, 255, 0))
            border_draw = ImageDraw.Draw(bordered)
            border_draw.ellipse((0, 0, size + 8, size + 8), outline=(255, 255, 255, 200), width=4)
            
            # Add subtle shadow
            shadow = Image.new('RGBA', (size + 20, size + 20), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.ellipse((5, 5, size + 15, size + 15), fill=(0, 0, 0, 80))
            shadow = shadow.filter(ImageFilter.GaussianBlur(5))

            # Calculate position
            pad = 36
            if position == 'top-left':
                pos = (pad, pad)
            elif position == 'top-right':
                pos = (self.width - size - pad, pad)
            elif position == 'bottom-left':
                pos = (pad, self.height - size - pad)
            elif position == 'bottom-right':
                pos = (self.width - size - pad, self.height - size - pad)
            else:  # center
                pos = ((self.width - size) // 2, (self.height - size) // 2)

            # Paste shadow, border, and avatar
            img.paste(shadow, (pos[0] - 10, pos[1] - 10), shadow)
            img.paste(bordered, (pos[0] - 4, pos[1] - 4), bordered)
            img.paste(avatar, pos, mask)
            
            return img
        except Exception as e:
            print(f"Warning: Could not add avatar: {e}")
            return image

    def wrap_text(self, text, font, max_width):
        """Wrap text to fit within max_width"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            bbox = font.getbbox(test_line)
            if bbox[2] > max_width:
                if len(current_line) == 1:
                    lines.append(current_line.pop())
                else:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _pick_watermark_file(self, mode: str = 'corner', style: str = '') -> Path:
        import random
        watermark_files = sorted(self.watermark_dir.glob('*.png'))
        if not watermark_files:
            return None
        # Use random selection instead of deterministic hash
        return random.choice(watermark_files)

    def add_watermark(self, image, opacity=0.7, style: str = '', mode: str = 'corner', color_match: bool = False, blend_mode: str = 'normal', position: str = 'bottom-right', size_percent: float = 0.15):
        """
        Add watermark with multiple modes
        
        Args:
            image: Base image
            opacity: Watermark opacity
            style: Design style name
            mode: 'corner', 'stripe', 'color-match', 'subtle'
            color_match: Whether to match watermark color to image
        """
        watermark_path = self._pick_watermark_file(mode=mode, style=style)
        if not watermark_path:
            return image

        try:
            watermark = Image.open(watermark_path).convert('RGBA')

            # Color-match mode
            if mode == 'color-match' or color_match:
                dominant = self.extract_dominant_color(image)
                # Tint watermark to match image
                watermark = self._tint_image(watermark, dominant)
                opacity = 0.5  # Lower opacity for color-matched

            # Stripe mode
            if mode == 'stripe':
                base = image.convert('RGBA')
                wm = watermark.copy()

                w_target = max(160, int(min(self.width, self.height) * 0.12))
                ratio = w_target / max(1, wm.width)
                h_target = max(1, int(wm.height * ratio))
                wm = wm.resize((w_target, h_target), Image.Resampling.LANCZOS)

                alpha = wm.split()[3].point(lambda p: int(p * opacity))
                wm.putalpha(alpha)

                diag = int(math.hypot(self.width, self.height))
                tile = Image.new('RGBA', (diag, diag), (0, 0, 0, 0))

                step_x = int(wm.width * 1.8)
                step_y = int(wm.height * 1.8)
                for y in range(-wm.height, diag + wm.height, max(1, step_y)):
                    for x in range(-wm.width, diag + wm.width, max(1, step_x)):
                        tile.alpha_composite(wm, (x, y))

                tile = tile.rotate(-22, resample=Image.Resampling.BICUBIC, expand=True)

                left = max(0, (tile.width - self.width) // 2)
                top = max(0, (tile.height - self.height) // 2)
                tile = tile.crop((left, top, left + self.width, top + self.height))

                return Image.alpha_composite(base, tile)

            max_size = max(32, int(min(self.width, self.height) * float(size_percent or 0.15)))
            watermark.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            pad = 30
            pos_key = str(position or 'bottom-right').strip().lower()
            if pos_key == 'bottom-left':
                position = (pad, self.height - watermark.height - pad)
            else:
                position = (self.width - watermark.width - pad, self.height - watermark.height - pad)

            base = image.convert('RGBA')
            wm = watermark.copy()

            # Neon style special handling
            if str(style).strip().lower() == 'neon':
                glow = wm.copy()
                glow_alpha = glow.split()[3].point(lambda p: int(p * 0.92))
                glow.putalpha(glow_alpha)
                glow = glow.filter(ImageFilter.GaussianBlur(10))

                layer_glow = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                layer_glow.paste(glow, position, glow)

                layer_wm = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                wm_alpha = wm.split()[3].point(lambda p: int(p * opacity))
                wm.putalpha(wm_alpha)
                layer_wm.paste(wm, position, wm)

                base = ImageChops.screen(base, layer_glow)
                base = Image.alpha_composite(base, layer_wm)
                return base

            # Standard watermark with optional blend
            wm_alpha = wm.split()[3]
            wm_alpha = wm_alpha.point(lambda p: int(p * opacity))
            wm.putalpha(wm_alpha)

            if str(blend_mode).strip().lower() == 'multiply':
                layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                layer.paste(wm, position, wm)
                return ImageChops.multiply(base, layer)
            if str(blend_mode).strip().lower() == 'screen':
                layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                layer.paste(wm, position, wm)
                return ImageChops.screen(base, layer)
            if str(blend_mode).strip().lower() == 'overlay':
                layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                layer.paste(wm, position, wm)
                return ImageChops.overlay(base, layer)

            base.paste(wm, position, wm)
            return base

        except Exception as e:
            print(f"Warning: Could not add watermark: {e}")
            return image

    def _tint_image(self, image, color):
        """Tint an RGBA image with a color"""
        r, g, b = color
        tinted = image.copy()
        tinted_data = tinted.getdata()
        
        new_data = []
        for item in tinted_data:
            if item[3] > 0:  # If not transparent
                new_data.append((
                    min(255, (item[0] + r) // 2),
                    min(255, (item[1] + g) // 2),
                    min(255, (item[2] + b) // 2),
                    item[3]
                ))
            else:
                new_data.append(item)
        
        tinted.putdata(new_data)
        return tinted

    def generate(self, quote, author, style='minimal', category='', add_watermark=True, author_image: str = '', 
                 watermark_mode: str = 'corner', watermark_opacity: float = None, watermark_blend: str = 'normal', avatar_position: str = 'top-left', font_name: str = None,
                 quote_font_size: int = None, author_font_size: int = None, watermark_size_percent: float = None, watermark_position: str = 'bottom-right',
                 background_mode: str = 'none', ai_model: str = None):
        """Generate image and save"""
        prev_regular = self._selected_font_regular_path
        prev_bold = self._selected_font_bold_path
        try:
            if font_name is not None:
                self.set_font(str(font_name))

            if quote_font_size is not None:
                try:
                    self.quote_font_size = int(quote_font_size)
                except Exception:
                    pass
            if author_font_size is not None:
                try:
                    self.author_font_size = int(author_font_size)
                except Exception:
                    pass

            style_func = self.styles.get(style, self.minimal_style)
            img = style_func(quote, author)

            bg_mode = str(background_mode or 'none').strip().lower()
            if bg_mode != 'none':
                bg_path = self._resolve_background_path(
                    mode=bg_mode,
                    quote=str(quote or ''),
                    author=str(author or ''),
                    category=str(category or ''),
                    ai_model=str(ai_model) if ai_model else None,
                )
                if bg_path:
                    bg_img = self._load_background_image(bg_path)
                    if bg_img:
                        try:
                            base = bg_img.convert('RGB')
                            styled = img.convert('RGB')
                            img = Image.blend(base, styled, 0.35)
                        except Exception:
                            pass
            
            # Always add avatar if available
            img = self.add_avatar(img, author_image, position=avatar_position)
            
            if add_watermark:
                op = 0.7 if watermark_opacity is None else float(watermark_opacity)
                sp = watermark_size_percent
                try:
                    sp = float(sp) if sp is not None else None
                except Exception:
                    sp = None
                img = self.add_watermark(
                    img,
                    style=style,
                    mode=watermark_mode,
                    opacity=op,
                    blend_mode=str(watermark_blend or 'normal'),
                    position=str(watermark_position or 'bottom-right'),
                    size_percent=sp if sp is not None else 0.15
                )

            # Generate filename with format: <Category> - <Quote> - <Author> - <DD-MM-YYYY_HHMM>
            from datetime import datetime
            import re
            
            # Clean and truncate text for filename
            clean_category = re.sub(r'[^\w\s-]', '', str(category)).strip() if category else 'General'
            clean_quote = re.sub(r'[^\w\s-]', '', str(quote)).strip()
            clean_author = re.sub(r'[^\w\s-]', '', str(author)).strip()
            
            # Limit lengths to avoid overly long filenames
            clean_category = clean_category[:20] if len(clean_category) > 20 else clean_category
            clean_quote = clean_quote[:30] if len(clean_quote) > 30 else clean_quote
            clean_author = clean_author[:20] if len(clean_author) > 20 else clean_author
            
            # Replace spaces with hyphens and remove extra spaces
            clean_category = re.sub(r'\s+', '-', clean_category)
            clean_quote = re.sub(r'\s+', '-', clean_quote)
            clean_author = re.sub(r'\s+', '-', clean_author)
            
            # Get current timestamp
            timestamp = datetime.now().strftime('%d-%m-%Y_%H%M')
            
            # Build filename
            filename = f"{clean_category} - {clean_quote} - {clean_author} - {timestamp}.png"
            
            output_path = self.output_dir / filename
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output_path, format='PNG', quality=95)
            return str(output_path)
        finally:
            self._selected_font_regular_path = prev_regular
            self._selected_font_bold_path = prev_bold

    def _load_background_image(self, path: str):
        try:
            p = Path(path)
            if not p.exists():
                return None
            bg = Image.open(str(p))
            if bg.mode not in ('RGB', 'RGBA'):
                bg = bg.convert('RGB')
            bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
            return bg
        except Exception:
            return None

    def _resolve_background_path(self, mode: str, quote: str, author: str, category: str, ai_model: str | None = None) -> str | None:
        m = str(mode or 'none').strip().lower()
        if m == 'custom':
            folder = Path('assets') / 'custom_backgrounds'
            if not folder.exists():
                return None
            files = []
            for ext in ('*.jpg', '*.jpeg', '*.png'):
                files.extend(folder.glob(ext))
            if not files:
                return None
            return str(random.choice(sorted(files)))

        if m == 'ai':
            try:
                from ai_prompt_generator import AIPromptGenerator
                from ai_image_generator import AIImageGenerator
            except Exception:
                return None

            prompt_gen = AIPromptGenerator()
            prompt_data = prompt_gen.generate_prompt(quote=quote, author=author, category=category)

            generator = AIImageGenerator()
            filename = f"ai_generated_{int(time.time())}.png"
            out = generator.generate_image(
                prompt=str(prompt_data.get('prompt') or ''),
                negative_prompt=str(prompt_data.get('negative_prompt') or ''),
                filename=filename,
                model=str(ai_model) if ai_model else None,
            )
            return str(out) if out else None

        return None
    
    # ============== ORIGINAL STYLES ==============
    
    def minimal_style(self, quote, author):
        """Minimal clean design"""
        img = Image.new('RGB', (self.width, self.height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        y = self.height // 2 - (len(lines) * 60) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#2C3E50', font=quote_font)
            y += 70
        
        y += 40
        author_text = f"- {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#7F8C8D', font=author_font)
        
        return img
    
    def bright_style(self, quote, author):
        """Bright vibrant gradient background"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        colors = [
            ('#FF6B6B', '#4ECDC4'),
            ('#A8E6CF', '#FFD3B6'),
            ('#FF8B94', '#FFAAA5'),
            ('#FFA07A', '#FFD700'),
        ]
        color_pair = random.choice(colors)
        
        for y in range(self.height):
            r1, g1, b1 = int(color_pair[0][1:3], 16), int(color_pair[0][3:5], 16), int(color_pair[0][5:7], 16)
            r2, g2, b2 = int(color_pair[1][1:3], 16), int(color_pair[1][3:5], 16), int(color_pair[1][5:7], 16)
            
            r = int(r1 + (r2 - r1) * y / self.height)
            g = int(g1 + (g2 - g1) * y / self.height)
            b = int(b1 + (b2 - b1) * y / self.height)
            
            draw.rectangle([(0, y), (self.width, y+1)], fill=(r, g, b))
        
        quote_font = self.get_font(self.quote_font_size, bold=True)
        author_font = self.get_font(self.author_font_size)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        y = self.height // 2 - (len(lines) * 65) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += 75
        
        y += 50
        author_text = f"- {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#F0F0F0', font=author_font)
        
        return img
    
    def elegant_style(self, quote, author):
        """Elegant pastel design with decorative elements"""
        pastels = ['#FFF5F7', '#F0F8FF', '#F5F5DC', '#FFF0F5', '#F0FFF0']
        bg_color = random.choice(pastels)
        img = Image.new('RGB', (self.width, self.height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        border_color = '#D4A5A5'
        margin = 60
        draw.rectangle(
            [(margin, margin), (self.width - margin, self.height - margin)],
            outline=border_color,
            width=3
        )
        
        inner_margin = margin + 15
        draw.rectangle(
            [(inner_margin, inner_margin), (self.width - inner_margin, self.height - inner_margin)],
            outline=border_color,
            width=1
        )
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size)
        
        lines = self.wrap_text(quote, quote_font, self.width - 280)
        y = self.height // 2 - (len(lines) * 58) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#4A4A4A', font=quote_font)
            y += 68
        
        y += 45
        author_text = f"— {author} —"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#8B7D7D', font=author_font)
        
        return img
    
    def bold_style(self, quote, author):
        """Bold solid color blocks"""
        bold_colors = ['#FF4757', '#3742FA', '#2ED573', '#FFA502', '#5F27CD']
        bg_color = random.choice(bold_colors)
        img = Image.new('RGB', (self.width, self.height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(self.quote_font_size, bold=True)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 180)
        y = self.height // 2 - (len(lines) * 70) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += 80
        
        y += 55
        author_text = f"{author.upper()}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#F0F0F0', font=author_font)
        
        return img
    
    def modern_style(self, quote, author):
        """Modern minimalist with geometric shapes"""
        img = Image.new('RGB', (self.width, self.height), color='#F5F5F5')
        draw = ImageDraw.Draw(img)
        
        accent_colors = ['#00D2FF', '#FF6B9D', '#C471ED', '#12CBC4', '#FDA7DF']
        accent = random.choice(accent_colors)
        draw.ellipse([(-100, -100), (300, 300)], fill=accent)
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size)
        
        lines = self.wrap_text(quote, quote_font, self.width - 220)
        y = self.height // 2 - (len(lines) * 62) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#2C3E50', font=quote_font)
            y += 72
        
        y += 48
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#7F8C8D', font=author_font)
        
        return img
    
    def neon_style(self, quote, author):
        """Futuristic neon design with glow"""
        img = Image.new('RGB', (self.width, self.height), color='#070816')
        draw = ImageDraw.Draw(img)

        accent_colors = ['#00D2FF', '#FF6B9D', '#C471ED', '#12CBC4']
        a1 = random.choice(accent_colors)
        a2 = random.choice([c for c in accent_colors if c != a1])

        for y in range(self.height):
            t = y / max(1, self.height - 1)
            r1, g1, b1 = int(a1[1:3], 16), int(a1[3:5], 16), int(a1[5:7], 16)
            r2, g2, b2 = int(a2[1:3], 16), int(a2[3:5], 16), int(a2[5:7], 16)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            draw.rectangle([(0, y), (self.width, y + 1)], fill=(r // 10, g // 10, b // 10))

        ring = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        rd = ImageDraw.Draw(ring)
        rd.ellipse([(-160, -160), (520, 520)], outline=a1, width=10)
        rd.ellipse([(-210, -210), (570, 570)], outline=a2, width=6)
        ring = ring.filter(ImageFilter.GaussianBlur(6))
        img = Image.alpha_composite(img.convert('RGBA'), ring).convert('RGB')
        draw = ImageDraw.Draw(img)

        quote_font = self.get_font(self.quote_font_size, bold=True)
        author_font = self.get_font(self.author_font_size)

        def glow_text(x, y, text, font, glow_color, main_color):
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)]:
                draw.text((x + dx, y + dy), text, fill=glow_color, font=font)
            draw.text((x, y), text, fill=main_color, font=font)

        lines = self.wrap_text(quote, quote_font, self.width - 240)
        y = self.height // 2 - (len(lines) * 70) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            glow_text(x, y, line, quote_font, a1, '#F8FAFF')
            y += 78

        y += 44
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        glow_text(x, y, author_text, author_font, a2, '#DDE6FF')

        return img

    # ============== NEW ENHANCED STYLES ==============
    
    def gradient_sunset_style(self, quote, author):
        """Beautiful sunset gradient with warm colors"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        # Sunset gradients
        gradients = [
            ('#FF6B35', '#F7931E', '#FDC830'),  # Orange sunset
            ('#FF512F', '#DD2476', '#8E2DE2'),  # Pink purple
            ('#FF6B6B', '#FFE66D', '#4ECDC4'),  # Warm to cool
        ]
        colors = random.choice(gradients)
        
        # Multi-stop gradient
        for y in range(self.height):
            if y < self.height // 3:
                # Top third
                t = y / (self.height // 3)
                r1, g1, b1 = int(colors[0][1:3], 16), int(colors[0][3:5], 16), int(colors[0][5:7], 16)
                r2, g2, b2 = int(colors[1][1:3], 16), int(colors[1][3:5], 16), int(colors[1][5:7], 16)
            else:
                # Bottom two-thirds
                t = (y - self.height // 3) / (2 * self.height // 3)
                r1, g1, b1 = int(colors[1][1:3], 16), int(colors[1][3:5], 16), int(colors[1][5:7], 16)
                r2, g2, b2 = int(colors[2][1:3], 16), int(colors[2][3:5], 16), int(colors[2][5:7], 16)
            
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            draw.rectangle([(0, y), (self.width, y+1)], fill=(r, g, b))
        
        quote_font = self.get_font(self.quote_font_size, bold=True)
        author_font = self.get_font(self.author_font_size)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        y = self.height // 2 - (len(lines) * 65) // 2
        
        # Add text shadow for depth
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            # Shadow
            draw.text((x+3, y+3), line, fill='#00000040', font=quote_font)
            # Main text
            draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += 75
        
        y += 50
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x+2, y+2), author_text, fill='#00000030', font=author_font)
        draw.text((x, y), author_text, fill='#FFFFFF', font=author_font)
        
        return img
    
    def professional_style(self, quote, author):
        """Clean professional corporate style"""
        img = Image.new('RGB', (self.width, self.height), color='#FAFAFA')
        draw = ImageDraw.Draw(img)
        
        # Accent bar on left
        accent_colors = ['#2C3E50', '#34495E', '#1A252F', '#0F4C81']
        accent = random.choice(accent_colors)
        draw.rectangle([(0, 0), (20, self.height)], fill=accent)
        
        # Subtle background pattern
        for i in range(0, self.height, 40):
            draw.line([(20, i), (self.width, i)], fill='#F0F0F0', width=1)
        
        quote_font = self.get_font(48)
        author_font = self.get_font(28)
        
        lines = self.wrap_text(quote, quote_font, self.width - 280)
        y = self.height // 2 - (len(lines) * 58) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2 + 20
            draw.text((x, y), line, fill='#2C3E50', font=quote_font)
            y += 68
        
        y += 40
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2 + 20
        draw.text((x, y), author_text, fill=accent, font=author_font)
        
        return img
    
    def vintage_style(self, quote, author):
        """Vintage paper texture style"""
        # Vintage paper colors
        paper_colors = ['#F4E8C1', '#E8DCC3', '#F5E6D3', '#FFF8DC']
        bg_color = random.choice(paper_colors)
        img = Image.new('RGB', (self.width, self.height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Add vintage texture (noise)
        import random as rand
        for _ in range(2000):
            x = rand.randint(0, self.width-1)
            y = rand.randint(0, self.height-1)
            brightness = rand.randint(-20, 20)
            current = img.getpixel((x, y))
            new_color = tuple(max(0, min(255, c + brightness)) for c in current)
            img.putpixel((x, y), new_color)
        
        draw = ImageDraw.Draw(img)
        
        # Decorative corners
        corner_color = '#8B7355'
        corner_size = 60
        # Top left
        draw.line([(20, 20), (corner_size, 20)], fill=corner_color, width=3)
        draw.line([(20, 20), (20, corner_size)], fill=corner_color, width=3)
        # Top right
        draw.line([(self.width-corner_size, 20), (self.width-20, 20)], fill=corner_color, width=3)
        draw.line([(self.width-20, 20), (self.width-20, corner_size)], fill=corner_color, width=3)
        # Bottom left
        draw.line([(20, self.height-20), (corner_size, self.height-20)], fill=corner_color, width=3)
        draw.line([(20, self.height-corner_size), (20, self.height-20)], fill=corner_color, width=3)
        # Bottom right
        draw.line([(self.width-corner_size, self.height-20), (self.width-20, self.height-20)], fill=corner_color, width=3)
        draw.line([(self.width-20, self.height-corner_size), (self.width-20, self.height-20)], fill=corner_color, width=3)
        
        quote_font = self.get_font(50)
        author_font = self.get_font(30)
        
        lines = self.wrap_text(quote, quote_font, self.width - 250)
        y = self.height // 2 - (len(lines) * 60) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#3E2723', font=quote_font)
            y += 70
        
        y += 45
        author_text = f"~ {author} ~"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#5D4037', font=author_font)
        
        return img
    
    def nature_style(self, quote, author):
        """Nature-inspired green gradients"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        # Nature gradients
        gradients = [
            ('#134E5E', '#71B280'),  # Deep teal to sage
            ('#0F2027', '#2C5364'),  # Dark forest
            ('#56AB2F', '#A8E063'),  # Fresh green
        ]
        colors = random.choice(gradients)
        
        for y in range(self.height):
            r1, g1, b1 = int(colors[0][1:3], 16), int(colors[0][3:5], 16), int(colors[0][5:7], 16)
            r2, g2, b2 = int(colors[1][1:3], 16), int(colors[1][3:5], 16), int(colors[1][5:7], 16)
            
            t = y / self.height
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            
            draw.rectangle([(0, y), (self.width, y+1)], fill=(r, g, b))
        
        # Add subtle leaf pattern
        overlay = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for i in range(5):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            overlay_draw.ellipse([(x, y), (x+30, y+50)], fill=(255, 255, 255, 15))
        
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(self.quote_font_size, bold=True)
        author_font = self.get_font(self.author_font_size)
        
        lines = self.wrap_text(quote, quote_font, self.width - 220)
        y = self.height // 2 - (len(lines) * 62) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += 72
        
        y += 48
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#E8F5E9', font=author_font)
        
        return img
    
    def ocean_style(self, quote, author):
        """Ocean waves blue gradients"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        # Ocean gradients
        gradients = [
            ('#2E3192', '#1BFFFF'),  # Deep blue to cyan
            ('#0575E6', '#021B79'),  # Ocean depth
            ('#00B4DB', '#0083B0'),  # Tropical water
        ]
        colors = random.choice(gradients)
        
        for y in range(self.height):
            r1, g1, b1 = int(colors[0][1:3], 16), int(colors[0][3:5], 16), int(colors[0][5:7], 16)
            r2, g2, b2 = int(colors[1][1:3], 16), int(colors[1][3:5], 16), int(colors[1][5:7], 16)
            
            t = y / self.height
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            
            draw.rectangle([(0, y), (self.width, y+1)], fill=(r, g, b))
        
        # Add wave pattern
        overlay = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for i in range(0, self.height, 100):
            overlay_draw.arc([(0, i-50), (self.width, i+50)], 0, 180, fill=(255, 255, 255, 20), width=3)
        
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(54, bold=True)
        author_font = self.get_font(32)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        y = self.height // 2 - (len(lines) * 64) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x+2, y+2), line, fill='#00000040', font=quote_font)
            draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += 74
        
        y += 50
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x+2, y+2), author_text, fill='#00000030', font=author_font)
        draw.text((x, y), author_text, fill='#FFFFFF', font=author_font)
        
        return img
    
    def cosmic_style(self, quote, author):
        """Cosmic space theme with stars"""
        img = Image.new('RGB', (self.width, self.height), color='#0a0a1a')
        draw = ImageDraw.Draw(img)
        
        # Add stars
        import random as rand
        for _ in range(300):
            x = rand.randint(0, self.width)
            y = rand.randint(0, self.height)
            size = rand.randint(1, 3)
            brightness = rand.randint(150, 255)
            draw.ellipse([(x, y), (x+size, y+size)], fill=(brightness, brightness, brightness))
        
        # Add cosmic gradient overlay
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        colors = ['#8E2DE2', '#4A00E0', '#FF6B6B', '#00D2FF']
        for i, color in enumerate(colors):
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            overlay_draw.ellipse([
                (rand.randint(-200, self.width), rand.randint(-200, self.height)),
                (rand.randint(0, self.width+200), rand.randint(0, self.height+200))
            ], fill=(r, g, b, 30))
        
        overlay = overlay.filter(ImageFilter.GaussianBlur(60))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(self.quote_font_size, bold=True)
        author_font = self.get_font(self.author_font_size)
        
        lines = self.wrap_text(quote, quote_font, self.width - 220)
        y = self.height // 2 - (len(lines) * 66) // 2
        
        # Glowing text
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            # Glow
            for offset in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
                draw.text((x+offset[0], y+offset[1]), line, fill='#8E2DE2', font=quote_font)
            # Main
            draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += 76
        
        y += 50
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        for offset in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            draw.text((x+offset[0], y+offset[1]), author_text, fill='#4A00E0', font=author_font)
        draw.text((x, y), author_text, fill='#E0E0E0', font=author_font)
        
        return img
    
    def minimalist_dark_style(self, quote, author):
        """Minimalist dark theme"""
        img = Image.new('RGB', (self.width, self.height), color='#1a1a1a')
        draw = ImageDraw.Draw(img)
        
        # Accent line
        accent_colors = ['#00D2FF', '#FF6B9D', '#00FF88', '#FFD700']
        accent = random.choice(accent_colors)
        draw.line([(100, self.height//2 - 100), (self.width-100, self.height//2 - 100)], 
                  fill=accent, width=2)
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size)
        
        lines = self.wrap_text(quote, quote_font, self.width - 220)
        y = self.height // 2 - (len(lines) * 60) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += 70
        
        y += 40
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill=accent, font=author_font)
        
        # Bottom accent line
        draw.line([(100, y + 60), (self.width-100, y + 60)], fill=accent, width=2)
        
        return img
    
    def creative_split_style(self, quote, author):
        """Split design with two colors"""
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        # Color pairs
        color_pairs = [
            ('#FF6B6B', '#4ECDC4'),
            ('#A8E6CF', '#3D5A80'),
            ('#FFD93D', '#6BCF7F'),
            ('#FF6B9D', '#C471ED'),
        ]
        colors = random.choice(color_pairs)
        
        # Diagonal split
        split_angle = 25
        for y in range(self.height):
            split_x = int(self.width * 0.3 + y * math.tan(math.radians(split_angle)))
            
            r1, g1, b1 = int(colors[0][1:3], 16), int(colors[0][3:5], 16), int(colors[0][5:7], 16)
            r2, g2, b2 = int(colors[1][1:3], 16), int(colors[1][3:5], 16), int(colors[1][5:7], 16)
            
            draw.rectangle([(0, y), (split_x, y+1)], fill=(r1, g1, b1))
            draw.rectangle([(split_x, y), (self.width, y+1)], fill=(r2, g2, b2))
        
        quote_font = self.get_font(52, bold=True)
        author_font = self.get_font(30)
        
        lines = self.wrap_text(quote, quote_font, self.width - 240)
        y = self.height // 2 - (len(lines) * 62) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x+2, y+2), line, fill='#00000040', font=quote_font)
            draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += 72
        
        y += 48
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x+2, y+2), author_text, fill='#00000030', font=author_font)
        draw.text((x, y), author_text, fill='#FFFFFF', font=author_font)
        
        return img
    
    def geometric_style(self, quote, author):
        """Modern geometric shapes background"""
        img = Image.new('RGB', (self.width, self.height), color='#FAFAFA')
        draw = ImageDraw.Draw(img)
        
        # Background shapes
        shapes_overlay = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 0))
        shapes_draw = ImageDraw.Draw(shapes_overlay)
        
        colors = ['#00D2FF', '#FF6B9D', '#C471ED', '#FFD700', '#00FF88']
        
        import random as rand
        for _ in range(8):
            color = random.choice(colors)
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            
            shape_type = rand.choice(['circle', 'square', 'triangle'])
            x = rand.randint(0, self.width)
            y = rand.randint(0, self.height)
            size = rand.randint(100, 300)
            
            if shape_type == 'circle':
                shapes_draw.ellipse([(x, y), (x+size, y+size)], fill=(r, g, b, 30))
            elif shape_type == 'square':
                shapes_draw.rectangle([(x, y), (x+size, y+size)], fill=(r, g, b, 30))
            else:  # triangle
                shapes_draw.polygon([(x, y+size), (x+size//2, y), (x+size, y+size)], 
                                   fill=(r, g, b, 30))
        
        img = Image.alpha_composite(img.convert('RGBA'), shapes_overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(self.quote_font_size, bold=True)
        author_font = self.get_font(self.author_font_size)
        
        lines = self.wrap_text(quote, quote_font, self.width - 220)
        y = self.height // 2 - (len(lines) * 60) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            # Background for readability
            draw.rectangle([(x-20, y-10), (x+text_width+20, y+70)], 
                          fill=(255, 255, 255, 200))
            draw.text((x, y), line, fill='#2C3E50', font=quote_font)
            y += 70
        
        y += 40
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#7F8C8D', font=author_font)
        
        return img
    
    def artistic_style(self, quote, author):
        """Artistic watercolor-like effect"""
        img = Image.new('RGB', (self.width, self.height), color='#FFFFFF')
        
        # Create watercolor effect
        watercolor = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 0))
        wc_draw = ImageDraw.Draw(watercolor)
        
        colors = [
            ('#FF6B6B', '#FFE66D'),
            ('#4ECDC4', '#44A08D'),
            ('#A8E6CF', '#FFD3B6'),
            ('#C471ED', '#FF6B9D'),
        ]
        color_pair = random.choice(colors)
        
        import random as rand
        for _ in range(50):
            color = random.choice([color_pair[0], color_pair[1]])
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            
            x = rand.randint(-100, self.width+100)
            y = rand.randint(-100, self.height+100)
            size = rand.randint(100, 400)
            alpha = rand.randint(10, 40)
            
            wc_draw.ellipse([(x, y), (x+size, y+size)], fill=(r, g, b, alpha))
        
        watercolor = watercolor.filter(ImageFilter.GaussianBlur(40))
        img = Image.alpha_composite(img.convert('RGBA'), watercolor).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(52)
        author_font = self.get_font(30)
        
        lines = self.wrap_text(quote, quote_font, self.width - 220)
        y = self.height // 2 - (len(lines) * 62) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#2C3E50', font=quote_font)
            y += 72
        
        y += 48
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#7F8C8D', font=author_font)
        
        return img


# Standalone function
def create_quote_image(quote, author, style='minimal', category='', output_dir='Generated_Images'):
    """Quick function to create a quote image"""
    generator = QuoteImageGenerator(output_dir)
    return generator.generate(quote, author, style, category)
