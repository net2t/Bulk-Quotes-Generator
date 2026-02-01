# Troubleshooting Guide

## Common Issues and Solutions

### 1. Google Credentials Error

**Problem:** "credentials.json not found" or authentication fails

**Solutions:**

- Ensure `credentials.json` exists in the project root (same folder as `scripts/`)
- Verify it's a valid Google Service Account JSON file
- Check that the service account has access to:
  - Google Sheets API
  - Google Drive API
- Make sure the spreadsheet is shared with the service account email

**How to get credentials:**

1. Go to Google Cloud Console
2. Create a new project (or use existing)
3. Enable Google Sheets API and Google Drive API
4. Create Service Account credentials
5. Download JSON key file and save as `credentials.json`

### 2. Missing Python Packages

**Problem:** ImportError or ModuleNotFoundError

**Solution:**

```bash
pip install pillow gspread google-auth google-api-python-client flask
```

Or run the setup script:

```bash
python scripts/setup_environment.py
```

### 3. Watermark Not Appearing

**Problem:** Generated images don't have watermarks

**Solutions:**

- Check if `Watermarks/` folder exists
- Ensure there's at least one PNG file in the folder
- Verify the PNG has transparency (alpha channel)
- Check file permissions

**Stripe watermark not visible:**

- Increase watermark opacity (in code or future settings)
- Use a higher-contrast watermark PNG

### 4. Font Rendering Issues

**Problem:** Text appears as boxes or default font looks bad

**Solutions:**

- System fonts (Arial) are used as fallback
- For better results, add custom fonts to `assets/fonts/`
- Modify `image_generator.py` to use custom fonts:

  ```python
  return ImageFont.truetype("assets/fonts/YourFont.ttf", size)
  ```

**Dashboard UI font not loading (404 /assets/fonts/...):**

- Confirm the font file exists in `assets/fonts/`
- Restart the dashboard server

### 5. Google Drive Upload Fails

**Problem:** Images generate but don't upload to Drive

**Important:** Google Drive upload is currently disabled in the dashboard UI (kept in code for future use). Use Sheet write-back or local `Generated_Images/`.

**Enable Google Drive API:**

1. Go to Google Cloud Console
2. Navigate to "APIs & Services" > "Library"
3. Search for "Google Drive API"
4. Click "Enable"

### 6. Sheet URL Not Found

**Problem:** Cannot connect to Google Sheets

**Solutions:**

- Set environment variable: `GOODREADS_SHEET_URL=<your-sheet-url>`
- Or modify code to use direct URL
- Ensure sheet is shared with service account email
- Check URL format (should include `/edit` or similar)

**Sheet write-back columns:**

- `PREVIEW_LINK` is written to column `H`
- `STATUS` is written to column `I`
- `DIMENSIONS` and `GENERATED_AT` are auto-added at the end of the sheet

**Set environment variable (Windows):**

```cmd
set GOODREADS_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
```

**Set environment variable (Linux/Mac):**

```bash
export GOODREADS_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
```

### 7. Dashboard Won't Start

**Problem:** Flask app doesn't run or crashes

**Solutions:**

- Check if port 8000 is already in use
- Try a different port: modify `dashboard.py`

  ```python
  app.run(host='0.0.0.0', port=5000, debug=True)
  ```

- Ensure Flask is installed: `pip install flask`
- Check for syntax errors in imported modules

**If you changed code and nothing updates in the browser:**

- Stop the server with `CTRL + C`
- Start again: `python scripts/dashboard.py`

### 8. Images Too Large/Small

**Problem:** Generated images are wrong size

**Solution:**
Edit `references/config.json`:

```json
{
  "image_settings": {
    "width": 1080,    // Change this
    "height": 1920,   // For Instagram stories
    "quality": 95
  }
}
```

Or modify directly in `image_generator.py`:

```python
self.width = 1080
self.height = 1920
```

### 9. Text Overflow

**Problem:** Quote text doesn't fit in image

**Solutions:**

- Reduce font size in `config.json`
- Increase image dimensions
- Modify padding in `wrap_text()` function
- Use shorter quotes or truncate long ones

### 10. Color/Design Issues

**Problem:** Colors don't look right or designs are broken

**Solutions:**

- Check `config.json` color values are valid hex codes
- Ensure RGB values are 0-255
- Modify design functions in `image_generator.py`
- Test with different styles to isolate issue

## Getting Help

If issues persist:

1. Check Python version (3.8+ required)
2. Review console error messages carefully
3. Test each component separately:
   - Test sheet connection
   - Test image generation
   - Test Drive upload
4. Enable debug mode for more details

## Performance Tips

- Cache quotes locally to reduce API calls
- Generate images in batches for efficiency
- Use smaller watermarks for faster processing
- Compress images if file size is an issue
