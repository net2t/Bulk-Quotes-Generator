#!/usr/bin/env python3
"""
Enhanced Quote Image Generator for Bulk Quotes Image Generator
- 16 professional design templates
- Smart filename format: <Category> - <Quote> - <Author> - <DD-MM-YYYY_HHMM>
- Avatar support with circular cropping
- Watermark blend modes and sizing
- Font customization
"""

import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import textwrap
from typing import Optional, Union, Tuple
import re

class QuoteImageGenerator:
    def __init__(self, output_dir='Generated_Images', width=1080, height=1080):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.width = width
        self.height = height
        
        # Font paths
        self.font_dir = Path('assets/fonts')
        self.default_font_path = self.font_dir / 'Garf - Normal.ttf'
        self.bold_font_path = self.font_dir / 'BURNODS.ttf'
        
        # Background directories
        self.ai_backgrounds_dir = Path('assets/ai_backgrounds')
        self.custom_backgrounds_dir = Path('assets/custom_backgrounds')
        
        # Watermark directory
        self.watermark_dir = Path('Watermarks')
        
        # Font sizes
        self.quote_font_size = 52
        self.author_font_size = 30
        
        # Selected font paths (for font switching)
        self._selected_font_regular_path = None
        self._selected_font_bold_path = None
        
        # Style mapping
        self.styles = {
            'elegant': self.elegant_style,
            'modern': self.modern_style,
            'neon': self.neon_style,
            'vintage': self.vintage_style,
            'minimalist_dark': self.minimalist_dark_style,
            'creative_split': self.creative_split_style,
            'geometric': self.geometric_style,
            'artistic': self.artistic_style,
            'minimal': self.minimal_style,
            'gradient': self.gradient_style,
            'typography': self.typography_style,
            'photo': self.photo_style,
            'abstract': self.abstract_style,
            'nature': self.nature_style,
            'tech': self.tech_style,
            'handwritten': self.handwritten_style
        }
    
    def set_font(self, font_name: str):
        """Set custom font by name"""
        font_path = self.font_dir / f"{font_name}.ttf"
        bold_path = self.font_dir / f"{font_name}-Bold.ttf"
        
        if font_path.exists():
            self._selected_font_regular_path = font_path
        else:
            self._selected_font_regular_path = self.default_font_path
            
        if bold_path.exists():
            self._selected_font_bold_path = bold_path
        else:
            self._selected_font_bold_path = self.bold_font_path
    
    def get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Get font with specified size and weight"""
        try:
            if bold:
                font_path = self._selected_font_bold_path or self.bold_font_path
            else:
                font_path = self._selected_font_regular_path or self.default_font_path
            
            return ImageFont.truetype(str(font_path), size)
        except:
            return ImageFont.load_default()
    
    def wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
        """Wrap text to fit within max_width"""
        lines = []
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if paragraph.strip() == '':
                lines.append('')
                continue
                
            words = paragraph.split()
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = font.getbbox(test_line)
                text_width = bbox[2] - bbox[0]
                
                if text_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        # Word is too long, add it anyway
                        lines.append(word)
                        current_line = []
            
            if current_line:
                lines.append(' '.join(current_line))
        
        return lines
    
    def add_watermark(self, img: Image.Image, style: str = 'corner', mode: str = 'corner', 
                     opacity: float = 0.7, blend_mode: str = 'normal', 
                     position: str = 'bottom-right', size_percent: float = 0.15) -> Image.Image:
        """Add watermark to image with various options"""
        try:
            watermark_files = sorted(self.watermark_dir.glob('*.png'))
            if not watermark_files:
                return img
                
            key = f"{str(mode or '').strip().lower()}|{str(style or '').strip().lower()}"
            hash_obj = hash(key)
            watermark_idx = hash_obj % len(watermark_files)
            watermark_path = watermark_files[watermark_idx]
            
            watermark = Image.open(watermark_path).convert('RGBA')
            
            # Calculate watermark size
            wm_width = int(img.width * size_percent)
            wm_height = int(watermark.height * (wm_width / watermark.width))
            watermark = watermark.resize((wm_width, wm_height), Image.Resampling.LANCZOS)
            
            # Apply opacity
            if opacity < 1.0:
                alpha = watermark.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
                watermark.putalpha(alpha)
            
            # Position watermark
            positions = {
                'top-left': (20, 20),
                'top-right': (img.width - wm_width - 20, 20),
                'bottom-left': (20, img.height - wm_height - 20),
                'bottom-right': (img.width - wm_width - 20, img.height - wm_height - 20),
                'center': ((img.width - wm_width) // 2, (img.height - wm_height) // 2)
            }
            
            pos = positions.get(position, positions['bottom-right'])
            
            # Apply blend mode
            if blend_mode == 'multiply':
                base_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
                base_layer.paste(watermark, pos, watermark)
                img = Image.alpha_composite(img.convert('RGBA'), base_layer)
            elif blend_mode == 'screen':
                base_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
                base_layer.paste(watermark, pos, watermark)
                img = Image.alpha_composite(img.convert('RGBA'), base_layer)
            elif blend_mode == 'overlay':
                base_layer = Image.new('RGBA', img.size, (128, 128, 128, 0))
                base_layer.paste(watermark, pos, watermark)
                img = Image.alpha_composite(img.convert('RGBA'), base_layer)
            else:  # normal
                img.paste(watermark, pos, watermark)
                
        except Exception as e:
            print(f"Warning: Could not add watermark: {e}")
            
        return img
    
    def add_avatar(self, img: Image.Image, avatar_url: str = '', position: str = 'top-left', size: int = 80) -> Image.Image:
        """Add circular avatar to image"""
        if not avatar_url:
            return img
            
        try:
            # For now, create a placeholder circular avatar
            # In a real implementation, you would download and process the avatar_url
            avatar_size = size
            
            # Create circular mask
            mask = Image.new('L', (avatar_size, avatar_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse([(0, 0), (avatar_size, avatar_size)], fill=255)
            
            # Create placeholder avatar (gradient circle)
            avatar = Image.new('RGBA', (avatar_size, avatar_size), (100, 150, 200, 255))
            draw = ImageDraw.Draw(avatar)
            draw.ellipse([(2, 2), (avatar_size-2, avatar_size-2)], fill=(150, 200, 250, 255))
            
            # Apply circular mask
            avatar.putalpha(mask)
            
            # Position avatar
            positions = {
                'top-left': (30, 30),
                'top-right': (img.width - avatar_size - 30, 30),
                'bottom-left': (30, img.height - avatar_size - 30),
                'bottom-right': (img.width - avatar_size - 30, img.height - avatar_size - 30)
            }
            
            pos = positions.get(position, positions['top-left'])
            img.paste(avatar, pos, avatar)
            
        except Exception as e:
            print(f"Warning: Could not add avatar: {e}")
            
        return img

    def generate(self, quote, author, style='minimal', category='', add_watermark=True, author_image: str = '', 
                 watermark_mode: str = 'corner', watermark_opacity: float = None, watermark_blend: str = 'normal', avatar_position: str = 'top-left', font_name: str = None,
                 quote_font_size: int = None, author_font_size: int = None, watermark_size_percent: float = None, watermark_position: str = 'bottom-right'):
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
    
    # ============== ORIGINAL STYLES ==============
    
    def minimal_style(self, quote, author):
        """Minimal clean design"""
        img = Image.new('RGB', (self.width, self.height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        # Calculate text positioning
        line_height = self.quote_font_size + 10
        total_text_height = len(lines) * line_height + self.author_font_size + 20
        
        start_y = (self.height - total_text_height) // 2
        
        # Draw quote
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                draw.text((x, y), line, fill='#2C3E50', font=quote_font)
            y += line_height
        
        # Draw author
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#7F8C8D', font=author_font)
        
        return img

    def elegant_style(self, quote, author):
        """Elegant design with gradient background"""
        img = Image.new('RGB', (self.width, self.height), color='#1A1A2E')
        draw = ImageDraw.Draw(img)
        
        # Add subtle gradient
        for y in range(self.height):
            color_value = int(26 + (y / self.height) * 20)
            color = f'#{color_value:02x}{color_value:02x}{color_value + 10:02x}'
            draw.line([(0, y), (self.width, y)], fill=color)
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        line_height = self.quote_font_size + 15
        total_text_height = len(lines) * line_height + self.author_font_size + 30
        
        start_y = (self.height - total_text_height) // 2
        
        # Draw quote with elegant formatting
        y = start_y
        for i, line in enumerate(lines):
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                
                # Add quote marks for first line
                if i == 0:
                    draw.text((x - 30, y), '"', fill='#E94560', font=quote_font)
                
                draw.text((x, y), line, fill='#F5F5F5', font=quote_font)
                
                if i == len(lines) - 1:
                    bbox_end = draw.textbbox((0, 0), line, font=quote_font)
                    end_x = x + (bbox_end[2] - bbox_end[0])
                    draw.text((end_x + 10, y), '"', fill='#E94560', font=quote_font)
                    
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#B8B8D1', font=author_font)
        
        return img

    def modern_style(self, quote, author):
        """Modern design with bold colors"""
        img = Image.new('RGB', (self.width, self.height), color='#0F3460')
        draw = ImageDraw.Draw(img)
        
        # Add accent color bar
        bar_height = 80
        draw.rectangle([(0, 0), (self.width, bar_height)], fill='#E94560')
        
        quote_font = self.get_font(self.quote_font_size - 5)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 180)
        
        line_height = self.quote_font_size + 10
        start_y = bar_height + 60
        
        # Draw quote
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                draw.text((x, y), line, fill='#F5F5F5', font=quote_font)
            y += line_height
        
        # Draw author
        y += 30
        author_text = f"— {author.upper()}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#E94560', font=author_font)
        
        return img

    def neon_style(self, quote, author):
        """Neon glow style"""
        img = Image.new('RGB', (self.width, self.height), color='#0A0A0A')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        line_height = self.quote_font_size + 15
        total_text_height = len(lines) * line_height + self.author_font_size + 30
        
        start_y = (self.height - total_text_height) // 2
        
        # Draw neon text with glow effect
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                
                # Glow effect
                for offset in [4, 3, 2, 1]:
                    glow_color = (255, 0, 255, 50 // offset)
                    draw.text((x + offset, y + offset), line, fill=glow_color, font=quote_font)
                    draw.text((x - offset, y + offset), line, fill=glow_color, font=quote_font)
                    draw.text((x + offset, y - offset), line, fill=glow_color, font=quote_font)
                    draw.text((x - offset, y - offset), line, fill=glow_color, font=quote_font)
                
                # Main text
                draw.text((x, y), line, fill='#00FFFF', font=quote_font)
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#FF00FF', font=author_font)
        
        return img

    def vintage_style(self, quote, author):
        """Vintage sepia style"""
        img = Image.new('RGB', (self.width, self.height), color='#F4E8D0')
        draw = ImageDraw.Draw(img)
        
        # Add vintage texture effect
        for _ in range(500):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point((x, y), fill='#D2B48C')
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        line_height = self.quote_font_size + 12
        total_text_height = len(lines) * line_height + self.author_font_size + 30
        
        start_y = (self.height - total_text_height) // 2
        
        # Draw quote
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                draw.text((x, y), line, fill='#5D4037', font=quote_font)
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#8D6E63', font=author_font)
        
        return img

    def minimalist_dark_style(self, quote, author):
        """Minimalist dark style"""
        img = Image.new('RGB', (self.width, self.height), color='#1E1E1E')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        line_height = self.quote_font_size + 15
        total_text_height = len(lines) * line_height + self.author_font_size + 30
        
        start_y = (self.height - total_text_height) // 2
        
        # Draw quote
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#B0B0B0', font=author_font)
        
        return img

    def creative_split_style(self, quote, author):
        """Creative split screen style"""
        img = Image.new('RGB', (self.width, self.height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        # Split screen
        split_x = self.width // 2
        draw.rectangle([(0, 0), (split_x, self.height)], fill='#FF6B6B')
        draw.rectangle([(split_x, 0), (self.width, self.height)], fill='#4ECDC4')
        
        quote_font = self.get_font(self.quote_font_size - 10)
        author_font = self.get_font(self.author_font_size - 5, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 220)
        
        line_height = self.quote_font_size + 8
        start_y = 100
        
        # Draw quote across split
        y = start_y
        for i, line in enumerate(lines):
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                
                # Alternate colors for visual interest
                color = '#FFFFFF' if i % 2 == 0 else '#FFFFFF'
                draw.text((x, y), line, fill=color, font=quote_font)
            y += line_height
        
        # Draw author
        y += 30
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#FFFFFF', font=author_font)
        
        return img

    def geometric_style(self, quote, author):
        """Geometric pattern style"""
        img = Image.new('RGB', (self.width, self.height), color='#2C3E50')
        draw = ImageDraw.Draw(img)
        
        # Add geometric patterns
        for i in range(0, self.width, 100):
            for j in range(0, self.height, 100):
                if (i + j) % 200 == 0:
                    draw.rectangle([(i, j), (i + 50, j + 50)], fill='#34495E')
                else:
                    draw.polygon([(i + 25, j), (i + 50, j + 25), (i + 25, j + 50), (i, j + 25)], fill='#34495E')
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        line_height = self.quote_font_size + 12
        total_text_height = len(lines) * line_height + self.author_font_size + 30
        
        start_y = (self.height - total_text_height) // 2
        
        # Draw quote
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                draw.text((x, y), line, fill='#ECF0F1', font=quote_font)
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#BDC3C7', font=author_font)
        
        return img

    def artistic_style(self, quote, author):
        """Artistic watercolor style"""
        img = Image.new('RGB', (self.width, self.height), color='#FFE5E5')
        draw = ImageDraw.Draw(img)
        
        # Add artistic blobs
        for _ in range(20):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(50, 150)
            color = (random.randint(200, 255), random.randint(150, 255), random.randint(150, 255))
            draw.ellipse([(x, y), (x + size, y + size)], fill=color)
        
        # Add semi-transparent overlay
        overlay = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 180))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        line_height = self.quote_font_size + 15
        total_text_height = len(lines) * line_height + self.author_font_size + 30
        
        start_y = (self.height - total_text_height) // 2
        
        # Draw quote
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                draw.text((x, y), line, fill='#2C3E50', font=quote_font)
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#7F8C8D', font=author_font)
        
        return img

    # ============== ADDITIONAL STYLES ==============
    
    def gradient_style(self, quote, author):
        """Beautiful gradient background"""
        img = Image.new('RGB', (self.width, self.height), color='#667EEA')
        draw = ImageDraw.Draw(img)
        
        # Create gradient
        for y in range(self.height):
            ratio = y / self.height
            r = int(102 + (118 - 102) * ratio)
            g = int(126 + (75 - 126) * ratio)
            b = int(234 + (162 - 234) * ratio)
            draw.line([(0, y), (self.width, y)], fill=f'#{r:02x}{g:02x}{b:02x}')
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        line_height = self.quote_font_size + 15
        total_text_height = len(lines) * line_height + self.author_font_size + 30
        
        start_y = (self.height - total_text_height) // 2
        
        # Draw quote
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#E0E7FF', font=author_font)
        
        return img

    def typography_style(self, quote, author):
        """Focus on typography"""
        img = Image.new('RGB', (self.width, self.height), color='#FAFAFA')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(self.quote_font_size + 10)
        author_font = self.get_font(self.author_font_size + 5)
        
        lines = self.wrap_text(quote, quote_font, self.width - 180)
        
        line_height = self.quote_font_size + 20
        total_text_height = len(lines) * line_height + self.author_font_size + 40
        
        start_y = (self.height - total_text_height) // 2
        
        # Draw quote with emphasis
        y = start_y
        for i, line in enumerate(lines):
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                
                # Make first word larger
                words = line.split()
                if words:
                    first_word = words[0]
                    rest = ' '.join(words[1:]) if len(words) > 1 else ''
                    
                    # Draw first word
                    big_font = self.get_font(self.quote_font_size + 20)
                    bbox_big = draw.textbbox((0, 0), first_word, font=big_font)
                    big_width = bbox_big[2] - bbox_big[0]
                    big_x = x - 20
                    draw.text((big_x, y), first_word, fill='#1A202C', font=big_font)
                    
                    # Draw rest of line
                    if rest:
                        rest_x = big_x + big_width + 10
                        draw.text((rest_x, y + 5), rest, fill='#4A5568', font=quote_font)
            y += line_height
        
        # Draw author with style
        y += 30
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        
        # Add underline
        draw.line([(x - 10, y + 25), (x + text_width + 10, y + 25)], fill='#E53E3E', width=2)
        draw.text((x, y), author_text, fill='#2D3748', font=author_font)
        
        return img

    def photo_style(self, quote, author):
        """Photo background style"""
        # Create a photographic-looking background
        img = Image.new('RGB', (self.width, self.height), color='#87CEEB')
        draw = ImageDraw.Draw(img)
        
        # Add landscape elements
        # Sky gradient
        for y in range(self.height // 2):
            ratio = y / (self.height // 2)
            r = int(135 + (255 - 135) * ratio)
            g = int(206 + (255 - 206) * ratio)
            b = int(235 + (255 - 235) * ratio)
            draw.line([(0, y), (self.width, y)], fill=f'#{r:02x}{g:02x}{b:02x}')
        
        # Ground
        draw.rectangle([(0, self.height // 2), (self.width, self.height)], fill='#8FBC8F')
        
        # Add some simple mountains
        draw.polygon([(200, self.height // 2), (400, 200), (600, self.height // 2)], fill='#696969')
        draw.polygon([(500, self.height // 2), (700, 250), (900, self.height // 2)], fill='#808080')
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        line_height = self.quote_font_size + 15
        start_y = self.height - (len(lines) * line_height + self.author_font_size + 100)
        
        # Draw quote with shadow
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                
                # Shadow
                draw.text((x + 2, y + 2), line, fill='#000000', font=quote_font)
                # Main text
                draw.text((x, y), line, fill='#FFFFFF', font=quote_font)
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        
        draw.text((x + 2, y + 2), author_text, fill='#000000', font=author_font)
        draw.text((x, y), author_text, fill='#FFFFFF', font=author_font)
        
        return img

    def abstract_style(self, quote, author):
        """Abstract art style"""
        img = Image.new('RGB', (self.width, self.height), color='#FFFFFF')
        draw = ImageDraw.Draw(img)
        
        # Add abstract shapes
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        
        for _ in range(15):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(30, 120)
            color = random.choice(colors)
            
            shape_type = random.choice(['ellipse', 'rectangle', 'polygon'])
            if shape_type == 'ellipse':
                draw.ellipse([(x, y), (x + size, y + size)], fill=color)
            elif shape_type == 'rectangle':
                draw.rectangle([(x, y), (x + size, y + size)], fill=color)
            else:
                points = [
                    (x + size // 2, y),
                    (x + size, y + size // 2),
                    (x + size // 2, y + size),
                    (x, y + size // 2)
                ]
                draw.polygon(points, fill=color)
        
        # Add semi-transparent overlay for text readability
        overlay = Image.new('RGBA', (self.width, self.height), (255, 255, 255, 200))
        img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        line_height = self.quote_font_size + 15
        total_text_height = len(lines) * line_height + self.author_font_size + 30
        
        start_y = (self.height - total_text_height) // 2
        
        # Draw quote
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                draw.text((x, y), line, fill='#2C3E50', font=quote_font)
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#7F8C8D', font=author_font)
        
        return img

    def nature_style(self, quote, author):
        """Nature-inspired style"""
        img = Image.new('RGB', (self.width, self.height), color='#E8F5E8')
        draw = ImageDraw.Draw(img)
        
        # Add nature elements
        # Tree
        draw.rectangle([(100, 400), (120, 600)], fill='#8B4513')  # Trunk
        draw.ellipse([(50, 300), (170, 450)], fill='#228B22')  # Leaves
        
        # Sun
        draw.ellipse([(800, 100), (950, 250)], fill='#FFD700')
        
        # Grass
        for x in range(0, self.width, 20):
            height = random.randint(20, 60)
            draw.line([(x, self.height), (x + 10, self.height - height)], fill='#90EE90', width=3)
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        line_height = self.quote_font_size + 15
        start_y = 150
        
        # Draw quote
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                draw.text((x, y), line, fill='#2E7D32', font=quote_font)
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#558B2F', font=author_font)
        
        return img

    def tech_style(self, quote, author):
        """Tech/modern digital style"""
        img = Image.new('RGB', (self.width, self.height), color='#0D1117')
        draw = ImageDraw.Draw(img)
        
        # Add tech grid
        for x in range(0, self.width, 50):
            draw.line([(x, 0), (x, self.height)], fill='#161B22', width=1)
        for y in range(0, self.height, 50):
            draw.line([(0, y), (self.width, y)], fill='#161B22', width=1)
        
        # Add circuit-like lines
        for _ in range(10):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = x1 + random.randint(-100, 100)
            y2 = y1 + random.randint(-100, 100)
            draw.line([(x1, y1), (x2, y2)], fill='#58A6FF', width=2)
            
            # Add nodes
            draw.ellipse([(x1 - 5, y1 - 5), (x1 + 5, y1 + 5)], fill='#79C0FF')
        
        quote_font = self.get_font(self.quote_font_size)
        author_font = self.get_font(self.author_font_size, bold=True)
        
        lines = self.wrap_text(quote, quote_font, self.width - 200)
        
        line_height = self.quote_font_size + 15
        total_text_height = len(lines) * line_height + self.author_font_size + 30
        
        start_y = (self.height - total_text_height) // 2
        
        # Draw quote with tech styling
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = (self.width - text_width) // 2
                
                # Add glow effect
                for offset in [2, 1]:
                    glow_color = (88, 166, 255, 100 // offset)
                    draw.text((x + offset, y + offset), line, fill=glow_color, font=quote_font)
                
                draw.text((x, y), line, fill='#C9D1D9', font=quote_font)
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), author_text, fill='#58A6FF', font=author_font)
        
        return img

    def handwritten_style(self, quote, author):
        """Handwritten personal style"""
        img = Image.new('RGB', (self.width, self.height), color='#FFF8E1')
        draw = ImageDraw.Draw(img)
        
        # Add notebook lines
        for y in range(100, self.height - 100, 30):
            draw.line([(50, y), (self.width - 50, y)], fill='#E0E0E0', width=1)
        
        # Add margin line
        draw.line([(80, 100), (80, self.height - 100)], fill='#FF5252', width=2)
        
        quote_font = self.get_font(self.quote_font_size - 10)
        author_font = self.get_font(self.author_font_size - 5)
        
        lines = self.wrap_text(quote, quote_font, self.width - 220)
        
        line_height = self.quote_font_size + 5
        start_y = 150
        
        # Draw quote with slight rotation for handwritten effect
        y = start_y
        for line in lines:
            if line.strip():
                bbox = draw.textbbox((0, 0), line, font=quote_font)
                text_width = bbox[2] - bbox[0]
                x = 100 + random.randint(-5, 5)  # Slight random horizontal offset
                y += random.randint(-3, 3)  # Slight random vertical offset
                
                # Use ink-like color
                draw.text((x, y), line, fill='#1A237E', font=quote_font)
            y += line_height
        
        # Draw author
        y += 20
        author_text = f"— {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        text_width = bbox[2] - bbox[0]
        x = 100 + random.randint(-5, 5)
        draw.text((x, y), author_text, fill='#3949AB', font=author_font)
        
        return img


# Standalone function
def create_quote_image(quote, author, style='minimal', category='', output_dir='Generated_Images'):
    """Quick function to create a quote image"""
    generator = QuoteImageGenerator(output_dir)
    return generator.generate(quote, author, style, category)