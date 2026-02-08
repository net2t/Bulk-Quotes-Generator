#!/usr/bin/env python3
"""
AI Prompt Generator
Analyzes quotes and generates detailed Text-to-Image prompts for AI generation
"""

import re
from typing import Dict, Optional
import json


class AIPromptGenerator:
    """Generate AI image prompts based on quote content and mood"""
    
    def __init__(self):
        # Keyword mappings for different themes
        self.themes = {
            'nature': ['tree', 'forest', 'mountain', 'ocean', 'sky', 'sunset', 'sunrise', 'flower', 'garden', 'river', 'lake', 'cloud', 'rain', 'snow'],
            'wisdom': ['wisdom', 'knowledge', 'learn', 'teach', 'think', 'mind', 'understand', 'truth', 'enlighten'],
            'love': ['love', 'heart', 'romance', 'passion', 'emotion', 'feeling', 'care', 'affection'],
            'success': ['success', 'achieve', 'goal', 'dream', 'ambition', 'winner', 'victory', 'triumph'],
            'motivation': ['motivate', 'inspire', 'courage', 'strength', 'power', 'determination', 'perseverance'],
            'peace': ['peace', 'calm', 'serenity', 'tranquil', 'quiet', 'silence', 'meditation', 'zen'],
            'life': ['life', 'live', 'exist', 'journey', 'path', 'experience', 'moment', 'time'],
            'happiness': ['happy', 'joy', 'smile', 'laughter', 'delight', 'pleasure', 'cheerful'],
            'sadness': ['sad', 'sorrow', 'grief', 'pain', 'tear', 'cry', 'melancholy'],
            'hope': ['hope', 'faith', 'believe', 'trust', 'optimism', 'bright', 'future'],
            'darkness': ['dark', 'night', 'shadow', 'fear', 'alone', 'lonely'],
            'light': ['light', 'bright', 'shine', 'glow', 'illuminate', 'radiant'],
            'time': ['time', 'clock', 'hour', 'minute', 'second', 'past', 'future', 'present'],
            'journey': ['journey', 'travel', 'road', 'path', 'way', 'destination', 'adventure'],
            'freedom': ['freedom', 'free', 'liberty', 'independent', 'fly', 'soar', 'wings'],
        }
        
        # Color schemes based on mood
        self.color_schemes = {
            'positive': 'bright, warm colors, golden hour lighting, vibrant',
            'negative': 'cool colors, muted tones, soft lighting, melancholic',
            'neutral': 'balanced colors, natural lighting, professional',
            'energetic': 'bold colors, high contrast, dynamic lighting',
            'calm': 'pastel colors, soft lighting, peaceful atmosphere',
            'dramatic': 'dark background, spotlight effect, cinematic lighting',
        }
        
        # Style descriptors
        self.art_styles = [
            'digital art',
            'watercolor painting',
            'oil painting style',
            'minimalist design',
            'photorealistic',
            'abstract art',
            'vintage illustration',
            'modern graphic design',
        ]
    
    def detect_themes(self, text: str) -> list:
        """Detect themes present in the quote text"""
        text_lower = text.lower()
        detected = []
        
        for theme, keywords in self.themes.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if theme not in detected:
                        detected.append(theme)
                    break
        
        # Default to 'life' if no theme detected
        if not detected:
            detected.append('life')
        
        return detected[:3]  # Return top 3 themes
    
    def analyze_mood(self, text: str) -> str:
        """Analyze the emotional mood of the quote"""
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = ['love', 'joy', 'happy', 'success', 'peace', 'hope', 'beautiful', 
                         'wonderful', 'inspire', 'dream', 'smile', 'triumph', 'victory']
        # Negative indicators  
        negative_words = ['pain', 'sorrow', 'sad', 'fear', 'dark', 'lonely', 'grief',
                         'loss', 'tear', 'suffer', 'despair']
        # Energetic indicators
        energetic_words = ['power', 'strong', 'energy', 'action', 'fight', 'rise',
                          'conquer', 'achieve', 'passion']
        # Calm indicators
        calm_words = ['peace', 'calm', 'quiet', 'gentle', 'soft', 'tranquil',
                     'serene', 'silence', 'meditation']
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        energy_count = sum(1 for word in energetic_words if word in text_lower)
        calm_count = sum(1 for word in calm_words if word in text_lower)
        
        # Determine dominant mood
        if energy_count >= 2:
            return 'energetic'
        if calm_count >= 2:
            return 'calm'
        if pos_count > neg_count:
            return 'positive'
        if neg_count > pos_count:
            return 'negative'
        
        return 'neutral'
    
    def get_scene_description(self, themes: list) -> str:
        """Generate scene description based on themes"""
        scene_map = {
            'nature': 'beautiful natural landscape with mountains and trees',
            'wisdom': 'ancient library with glowing books and mystical atmosphere',
            'love': 'romantic sunset scene with soft pink and purple hues',
            'success': 'summit of a mountain at sunrise, achievement symbolism',
            'motivation': 'person climbing upward, rays of light breaking through clouds',
            'peace': 'zen garden with calm water reflection and cherry blossoms',
            'life': 'winding path through a scenic landscape, journey symbolism',
            'happiness': 'bright sunny meadow filled with colorful wildflowers',
            'sadness': 'rainy window with soft droplets, melancholic atmosphere',
            'hope': 'dawn breaking through darkness, light at the end of tunnel',
            'darkness': 'starry night sky with deep blues and cosmic elements',
            'light': 'sunbeams breaking through clouds, divine light effect',
            'time': 'ethereal clockwork mechanism with flowing time elements',
            'journey': 'scenic road stretching into horizon, adventure awaits',
            'freedom': 'bird soaring in vast open sky, sense of liberation',
        }
        
        # Get description for primary theme
        primary_theme = themes[0] if themes else 'life'
        return scene_map.get(primary_theme, 'inspiring abstract background')
    
    def generate_prompt(self, quote: str, author: str = '', category: str = '') -> Dict[str, str]:
        """
        Generate complete AI image prompt for a quote
        
        Returns:
            {
                'prompt': 'Full detailed prompt',
                'negative_prompt': 'Things to avoid',
                'style': 'Art style',
                'mood': 'Detected mood',
                'themes': 'Detected themes',
                'color_scheme': 'Suggested colors'
            }
        """
        # Detect themes and mood
        themes = self.detect_themes(quote)
        mood = self.analyze_mood(quote)
        
        # Get scene and colors
        scene = self.get_scene_description(themes)
        colors = self.color_schemes.get(mood, self.color_schemes['neutral'])
        
        # Choose art style based on mood
        if mood == 'energetic':
            style = 'digital art, bold and dynamic'
        elif mood == 'calm':
            style = 'watercolor painting, soft and peaceful'
        elif mood == 'dramatic':
            style = 'cinematic digital art, dramatic lighting'
        else:
            style = 'digital art, professional and clean'
        
        # Build the complete prompt
        prompt_parts = [
            scene,
            colors,
            style,
            'highly detailed',
            'professional quality',
            '4k resolution',
            'perfect for quote overlay',
            'centered composition',
            'no text or words',
        ]
        
        full_prompt = ', '.join(prompt_parts)
        
        # Negative prompt (things to avoid)
        negative_prompt = 'text, words, letters, watermark, signature, blurry, low quality, distorted, busy background, cluttered, ugly, bad anatomy'
        
        return {
            'prompt': full_prompt,
            'negative_prompt': negative_prompt,
            'style': style,
            'mood': mood,
            'themes': ', '.join(themes),
            'color_scheme': colors,
            'category': category,
        }
    
    def generate_simple_prompt(self, quote: str) -> str:
        """Generate a simple one-line prompt for quick use"""
        themes = self.detect_themes(quote)
        mood = self.analyze_mood(quote)
        scene = self.get_scene_description(themes)
        colors = self.color_schemes.get(mood, 'natural colors')
        
        return f"{scene}, {colors}, digital art, no text, high quality"


# Quick function for standalone use
def generate_ai_prompt(quote: str, author: str = '', category: str = '') -> Dict[str, str]:
    """Quick function to generate AI prompt"""
    generator = AIPromptGenerator()
    return generator.generate_prompt(quote, author, category)


# Test the generator
if __name__ == '__main__':
    # Test examples
    test_quotes = [
        "The only way to do great work is to love what you do.",
        "In the middle of darkness, light persists.",
        "The journey of a thousand miles begins with a single step.",
    ]
    
    generator = AIPromptGenerator()
    
    print("🎨 AI Prompt Generator - Test Results\n")
    print("=" * 80)
    
    for i, quote in enumerate(test_quotes, 1):
        print(f"\n📝 Quote {i}: {quote}")
        result = generator.generate_prompt(quote)
        print(f"\n🎯 Themes: {result['themes']}")
        print(f"🎭 Mood: {result['mood']}")
        print(f"🎨 Colors: {result['color_scheme']}")
        print(f"\n🖼️  Full Prompt:")
        print(f"   {result['prompt']}")
        print(f"\n🚫 Negative Prompt:")
        print(f"   {result['negative_prompt']}")
        print("\n" + "=" * 80)
