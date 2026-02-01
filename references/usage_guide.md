# Quote Image Generator - Complete Usage Guide

## Quick Start

### 1. Initial Setup (One-time)

Navigate to your project folder:
```bash
cd "c:\\Users\\NADEEM\\Downloads\\Quotes Images"
```

Run setup script:
```bash
python scripts/setup_environment.py
```

This will:
- ✅ Check for credentials.json
- ✅ Create Watermarks/ and Generated_Images/ folders
- ✅ Install required Python packages

### 2. Prepare Your Watermark

1. Create a watermark image (PNG with transparency)
2. Save it in the `Watermarks/` folder
3. Recommended size: 200x200 to 400x400 pixels
4. Make sure background is transparent

### 3. Set Google Sheet URL

**Windows Command Prompt:**
```cmd
set GOODREADS_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
```

**Windows PowerShell:**
```powershell
$env:GOODREADS_SHEET_URL="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

**Alternative:** Edit the script files directly to include the URL

### 4. Launch Dashboard

```bash
python scripts/dashboard.py
```

Open your browser and go to: http://localhost:8000

## Using the Dashboard

### Step-by-Step Workflow

1. **Select Topic**
   - Click the "Select Topic" dropdown
   - Choose from available topics (populated from your Google Sheet)
   - Example: Motivation, Love, Wisdom, etc.

2. **Choose Quote**
   - After selecting topic, quotes will load automatically
   - Click "Select Quote" dropdown
   - Pick an author/quote from the list

3. **Pick Design Style**
   - Click on one of the style cards:
     - ⚪ **Minimal** - Clean, professional, white background
     - 🌈 **Bright** - Vibrant gradients, high energy
     - ✨ **Elegant** - Soft pastels, decorative borders
     - ⚡ **Bold** - Strong colors, maximum impact
     - 🔷 **Modern** - Geometric, contemporary
     - 🧿 **Neon** - Dark futuristic neon with glow

4. **Choose Watermark Mode**
   - **Corner**: watermark placed bottom-right
   - **Stripe**: diagonal tiled watermark across the image

5. **Generate Image**
   - Click the "Generate Image" button
   - Wait for processing (usually 2-5 seconds)
   - Image is created and watermark is added
   - If the author image is available, a circular avatar is added top-left

6. **Sheet Write-back (optional)**
   - Turn on **Sheet Write-back** to write results back to your Google Sheet
   - Writes:
     - `PREVIEW_LINK` (Column H) as a clickable "Preview Image" hyperlink
     - `STATUS` (Column I) as `Done`
     - `DIMENSIONS` (auto-added column at end) like `1080x1080`
     - `GENERATED_AT` (auto-added column at end) like `2026-02-01 21:05:00`
   - Images are always saved locally in `Generated_Images/`

## Bulk Processing (Dashboard)

Use the **Bulk Generator** panel in the dashboard:
- Choose a topic
- Choose a style
- Set the count
- Click **Generate Bulk**

If Sheet Write-back is enabled, bulk generation will also write back links + metadata per generated row.

## Design Style Guide

### When to Use Each Style

**Minimal** - Best for:
- Professional content
- Corporate social media
- Life advice quotes
- Philosophy topics
- Clean, timeless look

**Bright** - Best for:
- Motivational content
- Inspiration posts
- Success quotes
- High-energy messages
- Instagram/Facebook posts

**Elegant** - Best for:
- Love quotes
- Poetry
- Romantic content
- Sophisticated messaging
- Special occasions

**Bold** - Best for:
- Humor quotes
- Strong statements
- Call-to-action messages
- Youth-oriented content
- Maximum visibility

**Modern** - Best for:
- Tech/business quotes
- Contemporary topics
- Minimalist aesthetic
- Professional branding
- LinkedIn posts

## Customization

### Changing Image Size

Edit `references/config.json`:

```json
{
  "image_settings": {
    "width": 1080,     // Instagram square
    "height": 1080
  }
}
```

**Common Sizes:**
- Instagram Post: 1080 x 1080
- Instagram Story: 1080 x 1920
- Facebook Post: 1200 x 630
- Twitter Post: 1024 x 512
- Pinterest: 1000 x 1500

### Adjusting Watermark

In `config.json`:

```json
{
  "watermark": {
    "opacity": 0.7,              // 0.0 to 1.0
    "position": "bottom-right",  // bottom-right, bottom-left, etc.
    "max_size_percent": 20       // % of image size
  }
}
```

### Changing Colors

Modify color schemes in `config.json` or directly in `scripts/image_generator.py`

**Example - Adding new gradient to Bright style:**

```python
colors = [
    ('#FF6B6B', '#4ECDC4'),
    ('#YOUR_COLOR1', '#YOUR_COLOR2'),  # Add here
]
```

### Custom Fonts

There are two kinds of fonts:

1) **Generated image fonts**
- Put `.ttf` files in `assets/fonts/`
- The generator will automatically pick the first `.ttf` it finds as the default font

2) **Dashboard UI fonts**
- Put `.ttf` files in `assets/fonts/`
- The dashboard loads them automatically and they appear as "(Local)" fonts in the Dashboard Font dropdown

## Advanced Features

### Reading from CSV Instead of Sheets

If you prefer using local CSV files:

```python
# In dashboard.py, modify to read from Export/ folder
import pandas as pd

def get_quotes_from_csv(topic):
    csv_path = f"Export/{topic}.csv"
    df = pd.read_csv(csv_path)
    return df.to_dict('records')
```

### Adding New Design Styles

1. Open `scripts/image_generator.py`
2. Add new method to `QuoteImageGenerator` class:

```python
def my_custom_style(self, quote, author):
    img = Image.new('RGB', (self.width, self.height), color='#YOUR_BG')
    draw = ImageDraw.Draw(img)
    
    # Your custom design logic here
    
    return img
```

3. Register in `self.styles` dictionary:

```python
self.styles = {
    # ... existing styles ...
    'custom': self.my_custom_style,
}
```

4. Update dashboard HTML to include new style card

### Organizing Drive Uploads

Google Drive upload is currently disabled in the dashboard UI (kept in code for future use).

## Tips & Best Practices

1. **Quote Length**: Keep quotes under 280 characters for best results
2. **Testing**: Test each style with your content before bulk generation
3. **Watermark**: Use subtle watermarks (70% opacity works well)
4. **Caching**: The system caches sheet data to reduce API calls
5. **Backup**: Keep local copies in Generated_Images/ folder
6. **Naming**: Images are auto-named with style and hash for uniqueness

## Workflow Examples

### Daily Social Media Posting

```bash
# Generate 3 different styles for one quote
python scripts/batch_generator.py --topic "Inspiration" --style "bright" --count 1 --upload
python scripts/batch_generator.py --topic "Inspiration" --style "minimal" --count 1 --upload
python scripts/batch_generator.py --topic "Inspiration" --style "modern" --count 1 --upload
```

### Weekly Content Batch

```bash
# Generate 35 images (5 per day for a week)
python scripts/batch_generator.py --topic "Motivation" --style "bright" --count 35 --upload
```

### Topic-Specific Campaigns

Use the dashboard for precise control over individual images when you need specific quotes for a campaign.

## Next Steps

Once comfortable with basic usage:
- Experiment with watermark stripe mode
- Add more fonts in `assets/fonts/`
- Add new design styles in `scripts/image_generator.py`
