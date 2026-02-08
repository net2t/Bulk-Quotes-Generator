# Bulk Quotes Image Generator

A powerful Python application for generating beautiful quote images in bulk with 16 professional design templates. Features smart filename formatting, Google Sheets integration, and Google Drive upload capabilities.

Current version: **1.100.1.1**

## Features

### Core Features
- **16 Professional Design Templates** - From elegant to modern, neon to vintage
- **Smart Filename Format** - `<Category> - <Quote> - <Author> - <DD-MM-YYYY_HHMM>.png`
- **Google Sheets Integration** - Connects to your Database worksheet
- **Bulk Generation** - Generate multiple images at once
- **Google Drive Upload** - Automatic upload with shareable links

### Design Templates
1. **Elegant** - Sophisticated with gradient backgrounds
2. **Modern** - Bold colors with accent bars
3. **Neon** - Glowing text effects
4. **Vintage** - Sepia tone with texture
5. **Minimalist Dark** - Clean dark theme
6. **Creative Split** - Split screen design
7. **Geometric** - Pattern-based backgrounds
8. **Artistic** - Watercolor style
9. **Gradient** - Beautiful color gradients
10. **Typography** - Focus on text design
11. **Photo** - Photographic backgrounds
12. **Abstract** - Abstract art style
13. **Nature** - Nature-inspired themes
14. **Tech** - Digital/circuit style
15. **Handwritten** - Personal notebook style
16. **Minimal** - Clean and simple

### Customization Options
- **Font Selection** - Multiple font options
- **Font Size Control** - Adjustable quote and author text sizes
- **Watermark Controls** - Opacity, size, blend modes, positioning
- **Avatar Support** - Circular author images with positioning
- **Background Options** - None / Custom (random) / AI-generated backgrounds

## Requirements

### Python Packages
```bash
pip install flask gspread google-auth google-auth-oauthlib google-auth-httplib2 pillow google-api-python-client
```

### System Requirements
- Python 3.7+
- Google Service Account credentials
- Access to Google Sheets (Database worksheet)

## Quick Start

### 1. Setup Google Sheets
1. Open your Database sheet: https://docs.google.com/spreadsheets/d/1jn1DroWU8GB5Sc1rQ7wT-WusXK9v4V05ISYHgUEjYZc/edit
2. Share with your service account email
3. Ensure columns: `QUOTE`, `AUTHOR`, `CATEGORY`, `STATUS`

### 2. Setup Credentials
1. Place `credentials.json` in the project root
2. Ensure the service account has access to:
   - Google Sheets API
   - Google Drive API

### 3. Run the Dashboard
```bash
cd "I:\My Drive\Python\Bulk Quotes Image Generator"
python scripts/dashboard.py
```

Access at: http://localhost:8000

### Optional: Enable AI Backgrounds (Hugging Face)

Set your free Hugging Face token as an environment variable:

```cmd
set HUGGINGFACE_API_KEY=hf_your_token_here
```

### 4. Generate Images
1. Select a topic from your Database sheet
2. Choose a quote and design style
3. Customize fonts, watermarks, and avatars
4. Click "Generate Quote Image"
5. Optionally upload to Google Drive

## Project Structure

```
Bulk Quotes Image Generator/
├── scripts/
│   ├── dashboard.py              # Web dashboard
│   ├── image_generator.py        # Core image generation
│   ├── sheet_reader.py           # Google Sheets integration
│   ├── batch_generator.py        # CLI batch generation
│   └── google_drive_uploader.py  # Drive upload functionality
├── tests/                         # Smoke tests
├── docs/                          # Extra documentation
├── assets/
│   ├── fonts/                    # Font files
│   ├── ai_backgrounds/           # AI-generated backgrounds
│   └── custom_backgrounds/       # Custom backgrounds
├── Watermarks/                   # Watermark images
├── Generated_Images/             # Output directory
├── references/
│   └── config.json              # Configuration file
└── credentials.json             # Google service account credentials
```

## Usage Options

### Web Dashboard
```bash
python scripts/dashboard.py
```
- Interactive web interface
- Real-time preview
- Batch generation
- Google Drive integration

### CLI Batch Generation
```bash
python scripts/batch_generator.py --topic "Inspirational Quotes" --style elegant --count 20 --upload
```

### Single Image Generation
```python
from scripts.image_generator import QuoteImageGenerator

generator = QuoteImageGenerator()
image_path = generator.generate(
    quote="Your quote here",
    author="Author Name",
    style="elegant",
    category="Inspirational Quotes"
)
```

## Google Sheets Integration

### Database Worksheet Structure
| Column | Purpose |
|--------|---------|
| QUOTE | Quote text |
| AUTHOR | Author name |
| CATEGORY | Quote category/topic |
| STATUS | Generation status (Done/Skip) |
| PREVIEW_LINK | Generated image link |
| DIMENSIONS | Image dimensions |
| GENERATED_AT | Timestamp |

### Supported Operations
- **Read quotes** by category
- **Mark as generated** with image links
- **Track remaining quotes** per author
- **Update metadata** (dimensions, timestamps)

## Google Drive Integration

### Automatic Upload
- Creates "Bulk Quote Images" folder
- Organizes by topic/category
- Generates shareable links
- Makes images publicly accessible

### Folder Structure
```
Bulk Quote Images/
├── Inspirational Quotes/
├── Life Quotes/
├── Love Quotes/
└── [Other Categories]/
```

## Customization

### Adding Custom Fonts
1. Place `.ttf` files in `assets/fonts/`
2. Fonts appear automatically in dashboard
3. Supported formats: TTF, OTF

### Custom Backgrounds
1. Add images to `assets/custom_backgrounds/`
2. Supported formats: JPG, PNG
3. Recommended size: 1080x1080

### AI Backgrounds
1. Set `HUGGINGFACE_API_KEY` (optional)
2. In the dashboard select:
   - Background Mode = `AI (Hugging Face)`
   - Choose model: Stable Diffusion / OpenJourney / Realistic Vision

### Watermark Customization
- Add PNG watermarks to `Watermarks/` folder
- Adjust opacity (0-1)
- Control size (5-40%)
- Choose blend modes (Normal, Multiply, Screen, Overlay)

## Configuration

Edit `references/config.json`:

```json
{
  "google_sheets": {
    "sheet_url": "your-sheet-url",
    "database_worksheet": "Database",
    "status_done_value": "Done",
    "max_length": 200,
    "english_only": true
  },
  "image_generation": {
    "default_style": "elegant",
    "width": 1080,
    "height": 1080
  },
  "drive_upload": {
    "default_folder": "Bulk Quote Images",
    "make_public": true
  }
}
```

## Troubleshooting

### Common Issues

**"Sheet connection failed"**
- Verify credentials.json path
- Check service account permissions
- Ensure sheet is shared with service account

**"No fonts found"**
- Check assets/fonts/ directory
- Verify TTF files are valid
- Restart dashboard after adding fonts

**"Drive upload failed"**
- Check Google Drive API access
- Verify service account permissions
- Ensure sufficient Drive storage

### Debug Mode
Enable debug logging:
```bash
python scripts/dashboard.py --debug
```

## Documentation

- `CHANGELOG.md`
- `docs/ENHANCED_SETUP_GUIDE.md`
- `docs/CHANGES_SUMMARY.md`
- `docs/QUICK_REFERENCE.md`

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and support:
1. Check the troubleshooting section
2. Verify your Google Sheets setup
3. Ensure credentials are properly configured
4. Test with a single quote first

---

**Generated with ❤️ by Bulk Quotes Image Generator**