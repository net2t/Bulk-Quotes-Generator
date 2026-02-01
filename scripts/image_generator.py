#!/usr/bin/env python3
"""
Image Generator
Creates beautiful quote images with different design styles
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from pathlib import Path
import textwrap
import random
import io
import urllib.request

class QuoteImageGenerator:
    def __init__(self, output_dir="Generated_Images", watermark_dir="Watermarks"):
        self.output_dir = Path(output_dir)
        self.watermark_dir = Path(watermark_dir)
        self.output_dir.mkdir(exist_ok=True)

        self._font_regular_path = None
        self._font_bold_path = None
        self._init_custom_fonts()

        # Default image size
        self.width = 1080
        self.height = 1080

        # Design styles
        self.styles = {
            'minimal': self.minimal_style,
            'bright': self.bright_style,
            'elegant': self.elegant_style,
            'bold': self.bold_style,
            'modern': self.modern_style,
            'neon': self.neon_style,
        }

    def _init_custom_fonts(self):
        fonts_dir = Path("assets") / "fonts"
        if not fonts_dir.exists():
            return
        ttf_files = sorted(list(fonts_dir.glob("*.ttf")))
        if not ttf_files:
            return

        bold_candidates = [p for p in ttf_files if "bold" in p.stem.lower()]
        self._font_regular_path = ttf_files[0]
        self._font_bold_path = bold_candidates[0] if bold_candidates else ttf_files[0]

    def get_font(self, size, bold=False):
        """Get a font, falling back to default if custom fonts unavailable"""
        try:
            if self._font_regular_path:
                font_path = self._font_bold_path if bold else self._font_regular_path
                return ImageFont.truetype(str(font_path), size)
            if bold:
                return ImageFont.truetype("arial.ttf", size)
            return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default()

    def add_avatar(self, image, author_image: str, opacity: float = 0.92):
        """Add a top-left circular avatar image"""
        if not author_image:
            return image

        try:
            img = image.convert('RGBA')
            if str(author_image).strip().lower().startswith('http'):
                with urllib.request.urlopen(str(author_image).strip(), timeout=6) as resp:
                    data = resp.read()
                avatar = Image.open(io.BytesIO(data)).convert('RGBA')
            else:
                avatar = Image.open(str(author_image)).convert('RGBA')

            max_size = int(min(self.width, self.height) * 0.12)
            avatar.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            size = min(avatar.width, avatar.height)
            left = (avatar.width - size) // 2
            top = (avatar.height - size) // 2
            avatar = avatar.crop((left, top, left + size, top + size))

            mask = Image.new('L', (size, size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, size, size), fill=255)

            alpha = avatar.split()[3].point(lambda p: int(p * opacity))
            avatar.putalpha(alpha)

            pad = 36
            img.paste(avatar, (pad, pad), mask)
            return img
        except Exception:
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

    def add_watermark(self, image, opacity=0.7, style: str = ''):
        """Add watermark from Watermarks folder"""
        watermark_files = list(self.watermark_dir.glob('*.png'))
        if not watermark_files:
            return image

        try:
            watermark_path = watermark_files[0]
            watermark = Image.open(watermark_path).convert('RGBA')

            max_size = min(self.width, self.height) // 5
            watermark.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            position = (
                self.width - watermark.width - 30,
                self.height - watermark.height - 30
            )

            base = image.convert('RGBA')
            wm = watermark.copy()

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

            wm_alpha = wm.split()[3]
            wm_alpha = wm_alpha.point(lambda p: int(p * opacity))
            wm.putalpha(wm_alpha)

            base.paste(wm, position, wm)
            return base

        except Exception as e:
            print(f"Warning: Could not add watermark: {e}")

        return image

    def generate(self, quote, author, style='minimal', add_watermark=True, author_image: str = ''):
        """Generate image and save"""
        style_func = self.styles.get(style, self.minimal_style)
        img = style_func(quote, author)

        img = self.add_avatar(img, author_image)
        if add_watermark:
            img = self.add_watermark(img, style=style)

        filename = f"quote_{style}_{random.randint(10000, 99999)}.png"
        output_path = self.output_dir / filename
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output_path, format='PNG')
        return str(output_path)
    
    def minimal_style(self, quote, author):
        """Minimal clean design"""
        # White background
        img = Image.new('RGB', (self.width, self.height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        # Fonts
        quote_font = self.get_font(50)
        author_font = self.get_font(30)
        
        # Draw quote
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        y = self.height // 2 - (len(lines) * 60) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#2C3E50', font=quote_font)
            y += 70
        
        # Draw author
        y += 40
        author_text = f"- {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#7F8C8D', font=author_font)
        
        return img
    
    def bright_style(self, quote, author):
        """Bright vibrant gradient background"""
        # Gradient background
        img = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        # Create gradient
        colors = [
            ('#FF6B6B', '#4ECDC4'),  # Red to Teal
            ('#A8E6CF', '#FFD3B6'),  # Green to Peach
            ('#FF8B94', '#FFAAA5'),  # Pink gradient
            ('#FFA07A', '#FFD700'),  # Orange to Gold
        ]
        color_pair = random.choice(colors)
        
        for y in range(self.height):
            r1, g1, b1 = int(color_pair[0][1:3], 16), int(color_pair[0][3:5], 16), int(color_pair[0][5:7], 16)
            r2, g2, b2 = int(color_pair[1][1:3], 16), int(color_pair[1][3:5], 16), int(color_pair[1][5:7], 16)
            
            r = int(r1 + (r2 - r1) * y / self.height)
            g = int(g1 + (g2 - g1) * y / self.height)
            b = int(b1 + (b2 - b1) * y / self.height)
            
            draw.rectangle([(0, y), (self.width, y+1)], fill=(r, g, b))
        
        # Fonts
        quote_font = self.get_font(55, bold=True)
        author_font = self.get_font(32)
        
        # Draw quote
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        y = self.height // 2 - (len(lines) * 65) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += 75
        
        # Draw author
        y += 50
        author_text = f"- {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#F0F0F0', font=author_font)
        
        return img
    
    def elegant_style(self, quote, author):
        """Elegant pastel design with decorative elements"""
        # Soft pastel background
        pastels = ['#FFF5F7', '#F0F8FF', '#F5F5DC', '#FFF0F5', '#F0FFF0']
        bg_color = random.choice(pastels)
        img = Image.new('RGB', (self.width, self.height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Decorative border
        border_color = '#D4A5A5'
        margin = 60
        draw.rectangle(
            [(margin, margin), (self.width - margin, self.height - margin)],
            outline=border_color,
            width=3
        )
        
        # Inner border
        inner_margin = margin + 15
        draw.rectangle(
            [(inner_margin, inner_margin), (self.width - inner_margin, self.height - inner_margin)],
            outline=border_color,
            width=1
        )
        
        # Fonts
        quote_font = self.get_font(48)
        author_font = self.get_font(28)
        
        # Draw quote
        lines = self.wrap_text(quote, quote_font, self.width - 280)
        y = self.height // 2 - (len(lines) * 58) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#4A4A4A', font=quote_font)
            y += 68
        
        # Draw author
        y += 45
        author_text = f"— {author} —"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#8B7D7D', font=author_font)
        
        return img
    
    def bold_style(self, quote, author):
        """Bold solid color blocks"""
        # Solid bold background
        bold_colors = ['#FF4757', '#3742FA', '#2ED573', '#FFA502', '#5F27CD']
        bg_color = random.choice(bold_colors)
        img = Image.new('RGB', (self.width, self.height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Fonts
        quote_font = self.get_font(60, bold=True)
        author_font = self.get_font(35, bold=True)
        
        # Draw quote
        lines = self.wrap_text(quote, quote_font, self.width - 180)
        y = self.height // 2 - (len(lines) * 70) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += 80
        
        # Draw author
        y += 55
        author_text = f"{author.upper()}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#F0F0F0', font=author_font)
        
        return img
    
    def modern_style(self, quote, author):
        """Modern minimalist with geometric shapes"""
        # Light gray background
        img = Image.new('RGB', (self.width, self.height), color='#F5F5F5')
        draw = ImageDraw.Draw(img)
        
        # Geometric accent (circle in corner)
        accent_colors = ['#00D2FF', '#FF6B9D', '#C471ED', '#12CBC4', '#FDA7DF']
        accent = random.choice(accent_colors)
        draw.ellipse([(-100, -100), (300, 300)], fill=accent)
        
        # Fonts
        quote_font = self.get_font(52)
        author_font = self.get_font(30)
        
        # Draw quote
        lines = self.wrap_text(quote, quote_font, self.width - 220)
        y = self.height // 2 - (len(lines) * 62) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=quote_font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
            draw.text((x, y), line, fill='#2C3E50', font=quote_font)
            y += 72
        
        # Draw author
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

        # Subtle vertical gradient
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            r1, g1, b1 = int(a1[1:3], 16), int(a1[3:5], 16), int(a1[5:7], 16)
            r2, g2, b2 = int(a2[1:3], 16), int(a2[3:5], 16), int(a2[5:7], 16)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            draw.rectangle([(0, y), (self.width, y + 1)], fill=(r // 10, g // 10, b // 10))

        # Glow ring overlay
        ring = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        rd = ImageDraw.Draw(ring)
        rd.ellipse([(-160, -160), (520, 520)], outline=a1, width=10)
        rd.ellipse([(-210, -210), (570, 570)], outline=a2, width=6)
        ring = ring.filter(ImageFilter.GaussianBlur(6))
        img = Image.alpha_composite(img.convert('RGBA'), ring).convert('RGB')
        draw = ImageDraw.Draw(img)

        quote_font = self.get_font(56, bold=True)
        author_font = self.get_font(30)

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

# Standalone function
def create_quote_image(quote, author, style='minimal', output_dir='Generated_Images'):
    """Quick function to create a quote image"""
    generator = QuoteImageGenerator(output_dir)
    return generator.generate(quote, author, style)
