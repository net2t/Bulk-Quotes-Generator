#!/usr/bin/env python3
"""
AI Image Generator using Hugging Face Inference API (FREE)
Generates background images from text prompts using AI models
"""

import os
import requests
from pathlib import Path
from typing import Optional
import time
import io
from PIL import Image


class AIImageGenerator:
    """Generate images using Hugging Face's free Inference API"""
    
    def __init__(self, api_key: Optional[str] = None, output_dir: str = "assets/ai_backgrounds"):
        """
        Initialize AI Image Generator
        
        Args:
            api_key: Hugging Face API key (get free at https://huggingface.co/settings/tokens)
            output_dir: Directory to save generated images
        """
        self.api_key = api_key or os.getenv('HUGGINGFACE_API_KEY')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Free models available on Hugging Face
        # These are completely FREE to use!
        self.models = {
            'stable_diffusion': 'stabilityai/stable-diffusion-2-1',  # Main model
            'openjourney': 'prompthero/openjourney',  # Artistic style
            'realistic': 'SG161222/Realistic_Vision_V5.1_noVAE',  # Realistic
        }
        
        self.default_model = self.models['stable_diffusion']
        self.api_url = f"https://api-inference.huggingface.co/models/{self.default_model}"
        
        if not self.api_key:
            print("⚠️  WARNING: No Hugging Face API key found!")
            print("   Get your FREE API key at: https://huggingface.co/settings/tokens")
            print("   Then set it as environment variable: HUGGINGFACE_API_KEY")
    
    def set_model(self, model_name: str):
        """Switch to a different AI model"""
        if model_name in self.models:
            self.default_model = self.models[model_name]
            self.api_url = f"https://api-inference.huggingface.co/models/{self.default_model}"
        else:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(self.models.keys())}")
    
    def generate_image(
        self, 
        prompt: str, 
        negative_prompt: str = '',
        filename: Optional[str] = None,
        max_retries: int = 3,
        model: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate an image from text prompt using AI
        
        Args:
            prompt: Text description of the image
            negative_prompt: Things to avoid in the image
            filename: Custom filename (auto-generated if None)
            max_retries: Number of retry attempts if model is loading
            model: Which model to use ('stable_diffusion', 'openjourney', 'realistic')
        
        Returns:
            Path to generated image file, or None if failed
        """
        if not self.api_key:
            print("❌ Cannot generate image: No API key configured")
            return None
        
        # Switch model if specified
        if model and model in self.models:
            original_url = self.api_url
            self.set_model(model)
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Prepare payload
        payload = {
            "inputs": prompt,
        }
        
        # Add negative prompt if provided
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        print(f"🎨 Generating AI image...")
        print(f"   Model: {self.default_model}")
        print(f"   Prompt: {prompt[:80]}...")
        
        # Try generating the image with retries
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
                
                if response.status_code == 200:
                    # Success! Save the image
                    image_data = response.content
                    
                    # Generate filename if not provided
                    if not filename:
                        timestamp = int(time.time())
                        filename = f"ai_generated_{timestamp}.png"
                    
                    # Ensure .png extension
                    if not filename.endswith('.png'):
                        filename += '.png'
                    
                    output_path = self.output_dir / filename
                    
                    # Save the image
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    
                    # Verify it's a valid image
                    try:
                        img = Image.open(output_path)
                        img.verify()
                        print(f"✅ Image generated successfully: {output_path}")
                        print(f"   Size: {img.size[0]}x{img.size[1]}")
                        return str(output_path)
                    except Exception as e:
                        print(f"❌ Generated file is not a valid image: {e}")
                        if output_path.exists():
                            output_path.unlink()
                        return None
                
                elif response.status_code == 503:
                    # Model is loading, wait and retry
                    error_data = response.json()
                    wait_time = error_data.get('estimated_time', 20)
                    print(f"⏳ Model is loading... waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time + 5)  # Add extra buffer
                    continue
                
                else:
                    # Other error
                    print(f"❌ Error {response.status_code}: {response.text}")
                    return None
            
            except requests.exceptions.Timeout:
                print(f"⏰ Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(10)
                    continue
                return None
            
            except Exception as e:
                print(f"❌ Error generating image: {e}")
                return None
        
        print(f"❌ Failed to generate image after {max_retries} attempts")
        return None
    
    def generate_batch(
        self, 
        prompts: list, 
        negative_prompt: str = '',
        model: Optional[str] = None,
        delay: int = 3
    ) -> list:
        """
        Generate multiple images from a list of prompts
        
        Args:
            prompts: List of text prompts
            negative_prompt: Things to avoid (applied to all)
            model: Which model to use
            delay: Seconds to wait between requests (rate limiting)
        
        Returns:
            List of file paths for successfully generated images
        """
        results = []
        
        print(f"\n🎨 Batch Generation: {len(prompts)} images")
        print("=" * 60)
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n[{i}/{len(prompts)}] Generating...")
            
            result = self.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                filename=f"batch_{i}_{int(time.time())}.png",
                model=model
            )
            
            if result:
                results.append(result)
            
            # Rate limiting: wait between requests
            if i < len(prompts):
                print(f"   ⏳ Waiting {delay}s before next generation...")
                time.sleep(delay)
        
        print("\n" + "=" * 60)
        print(f"✅ Batch complete: {len(results)}/{len(prompts)} successful")
        
        return results
    
    def test_connection(self) -> bool:
        """Test if API key is valid and working"""
        if not self.api_key:
            print("❌ No API key configured")
            return False
        
        print("🔍 Testing Hugging Face API connection...")
        
        try:
            # Try a simple generation
            test_prompt = "simple blue sky with white clouds, minimalist"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {"inputs": test_prompt}
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                print("✅ API connection successful!")
                return True
            elif response.status_code == 503:
                print("⚠️  API is working but model is loading (this is normal)")
                return True
            else:
                print(f"❌ API error {response.status_code}: {response.text}")
                return False
        
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False


# Quick function for standalone use
def generate_ai_image(prompt: str, api_key: Optional[str] = None) -> Optional[str]:
    """Quick function to generate a single AI image"""
    generator = AIImageGenerator(api_key=api_key)
    return generator.generate_image(prompt)


# Main test script
if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🤖 AI Image Generator - Test Mode")
    print("=" * 80)
    
    # Check for API key
    api_key = os.getenv('HUGGINGFACE_API_KEY')
    
    if not api_key:
        print("\n⚠️  NO API KEY FOUND!")
        print("\n📝 To use this feature:")
        print("   1. Go to https://huggingface.co/settings/tokens")
        print("   2. Click 'New token' (it's FREE!)")
        print("   3. Copy your token")
        print("   4. Set environment variable:")
        print("      Windows: set HUGGINGFACE_API_KEY=your_token_here")
        print("      Linux/Mac: export HUGGINGFACE_API_KEY=your_token_here")
        print("\n   Or add to your .env file")
        print("\n" + "=" * 80)
    else:
        print(f"\n✅ API Key found: {api_key[:10]}...{api_key[-5:]}")
        
        generator = AIImageGenerator(api_key=api_key)
        
        # Test connection
        if generator.test_connection():
            print("\n🎨 Running test generation...")
            
            test_prompt = "beautiful mountain landscape at sunset, warm colors, peaceful atmosphere, digital art, no text, high quality"
            
            result = generator.generate_image(
                prompt=test_prompt,
                negative_prompt="text, words, watermark, blurry",
                filename="test_image.png"
            )
            
            if result:
                print(f"\n🎉 SUCCESS! Test image saved to: {result}")
            else:
                print("\n❌ Test generation failed")
        
        print("\n" + "=" * 80)
