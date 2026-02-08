# 🎯 Quick Reference Card

## 🚀 Daily Usage - Fast Commands

### Start the Dashboard
```bash
python scripts/dashboard.py
```
Then open: http://localhost:8000

---

## 🎨 Feature Quick Access

### 1. Generate AI Prompt for a Quote
```python
from scripts.ai_prompt_generator import AIPromptGenerator

gen = AIPromptGenerator()
result = gen.generate_prompt(
    quote="Your quote here",
    author="Author Name",
    category="Category"
)

print(result['prompt'])       # AI prompt
print(result['themes'])        # Themes: nature, love, etc.
print(result['mood'])          # Mood: positive, calm, etc.
print(result['color_scheme'])  # Recommended colors
```

### 2. Generate AI Background Image
```python
from scripts.ai_image_generator import AIImageGenerator

gen = AIImageGenerator()
image = gen.generate_image(
    prompt="mountain sunset, warm colors, digital art",
    negative_prompt="text, watermark, blurry"
)

print(f"Image saved: {image}")
```

### 3. Use Custom Background
1. Add your image to: `assets/custom_backgrounds/`
2. In dashboard: Select "Custom Image" template
3. Generate!

---

## 📊 Google Sheet Columns

### Required:
| S# | CATEGORY | AUTHOR | QUOTE |

### Auto-Generated:
| AI_PROMPT | DESIGN_STYLE | COLOR_SCHEME |

### System-Managed:
| PREVIEW_LINK | STATUS | DIMENSIONS | GENERATED_AT |

---

## 🔑 Environment Setup

### Set Hugging Face API Key:

**Windows:**
```cmd
set HUGGINGFACE_API_KEY=hf_your_token_here
```

**Linux/Mac:**
```bash
export HUGGINGFACE_API_KEY=hf_your_token_here
```

**Get FREE Key:** https://huggingface.co/settings/tokens

---

## 🧪 Testing Commands

### Test Everything:
```bash
python test_enhanced_system.py
```

### Test AI Prompts:
```bash
python scripts/ai_prompt_generator.py
```

### Test AI Images:
```bash
python scripts/ai_image_generator.py
```

---

## 🎨 Available Design Templates

| Template | Style | Best For |
|----------|-------|----------|
| elegant | Pastel borders | Wisdom, Love |
| modern | Geometric shapes | Business, Tech |
| neon | Glowing effects | Motivation, Energy |
| vintage | Paper texture | Classic, Timeless |
| minimalist_dark | Dark minimal | Professional, Bold |
| creative_split | Two-tone split | Creative, Artistic |
| geometric | Shape patterns | Modern, Abstract |
| artistic | Watercolor | Creative, Soft |

---

## 💡 Pro Tips

### For Best Results:

**AI Prompts:**
- ✅ Clear quotes = better prompts
- ✅ Emotional words help (love, hope, courage)
- ✅ Visual words help (mountain, ocean, sky)

**AI Images:**
- ✅ Simple prompts work better
- ✅ Use negative prompts
- ✅ First gen takes 20-30s (model loading)
- ✅ After that, ~5-10s per image

**Custom Backgrounds:**
- ✅ Use 1080x1080 or higher
- ✅ Simple backgrounds, not busy
- ✅ Empty space for text

---

## 🆘 Quick Fixes

### Issue: "Module not found"
```bash
python scripts/setup_environment.py
```

### Issue: "No API key"
```bash
set HUGGINGFACE_API_KEY=your_token
```

### Issue: "Model loading"
**Wait 20-30 seconds** - automatic retry

---

## 🎉 One-Line Quick Start

```bash
python test_enhanced_system.py && python scripts/dashboard.py
```

**Happy Quote Creating!** ✨
