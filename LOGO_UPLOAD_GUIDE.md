# Logo Upload Guide

## Where to Place Your Logo

Your logo should be placed in:
```
app/static/images/
```

## Current Location
- **Path**: `c:\Users\parmi\Documents\Project\Mobile Database Management Tool\app\static\images\`
- **Default Logo**: `logo.svg` (placeholder - replace with your own)

## Supported Formats
- **PNG** (`logo.png`) - Recommended for photos
- **SVG** (`logo.svg`) - Best for crisp graphics (current)
- **JPG/JPEG** (`logo.jpg`) - Good for photos
- **WebP** (`logo.webp`) - Modern, better compression

## How to Upload Your Logo

### Option 1: Replace Existing Logo
1. Navigate to: `app/static/images/`
2. Replace `logo.svg` with your own logo file
3. Keep the same filename (`logo.svg`) or update the dashboard reference below

### Option 2: Add Your Logo with a Different Name
1. Place your logo file in `app/static/images/`
2. Open `app/templates/dashboard.html` in VS Code
3. Find this line (~line 210):
   ```html
   <img src="{{ url_for('static', filename='images/logo.svg') }}" alt="Logo" onerror="this.style.display='none'">
   ```
4. Change `images/logo.svg` to your filename, e.g., `images/your-logo.png`

### Option 3: Direct File Replacement
Since the dashboard is already configured to look for `logo.svg`:
- Simply replace the current `logo.svg` file with your own logo
- No code changes needed!

## Logo Specifications
- **Recommended Size**: 200x200px or larger (will scale automatically)
- **Background**: Transparent (for PNG/SVG) or solid color
- **Format**: Square aspect ratio works best
- **File Size**: Under 500KB

## Preview
- Your logo will appear in the top-left corner of the dashboard
- It displays in a 60x60px rounded box
- Falls back to 💼 emoji if image doesn't load

## Files in This Directory
```
app/static/images/
├── logo.svg          ← Replace with your company logo
```

## How the Dashboard Uses Your Logo
The dashboard automatically looks for `logo.svg` in the images folder and displays it in the header. If it can't find the file or load it, it falls back to the briefcase emoji (💼).

## Example: Replace Logo Steps
1. **Window Explorer**: Navigate to `c:\Users\parmi\Documents\Project\Mobile Database Management Tool\app\static\images\`
2. **Backup**: Optionally copy `logo.svg` somewhere safe
3. **Replace**: Put your company logo file in this folder and name it `logo.svg` (or update the HTML reference)
4. **Refresh**: Open http://localhost:5001 and refresh the page (Ctrl+R or Cmd+R)
5. **Done**: Your logo should appear in the dashboard!

---
**Need help?** Make sure:
- The file is in the correct directory
- The filename matches exactly (case-sensitive on some systems)
- The file format is readable (PNG, SVG, JPG, etc.)
- Your Flask server is running
