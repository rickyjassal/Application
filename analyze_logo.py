from PIL import Image
from collections import Counter
import os

# Load the logo
logo_path = os.path.join(os.path.dirname(__file__), 'app/static/images/logo.png')

try:
    img = Image.open(logo_path)
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize for faster processing
    img = img.resize((150, 150))
    
    # Get all pixels
    pixels = list(img.getdata())
    
    # Filter out very light colors (near white) and very dark colors (near black)
    # to get actual logo colors
    filtered_colors = []
    for r, g, b in pixels:
        # Skip near-white pixels
        if not (r > 240 and g > 240 and b > 240):
            # Skip near-black pixels
            if not (r < 15 and g < 15 and b < 15):
                # Calculate brightness
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                # Keep colors in mid-range brightness
                if 30 < brightness < 230:
                    filtered_colors.append((r, g, b))
    
    # Get most common colors
    if filtered_colors:
        color_counts = Counter(filtered_colors)
        most_common = color_counts.most_common(5)
        
        print("\n" + "="*60)
        print("🎨 LOGO COLOR ANALYSIS")
        print("="*60)
        print(f"\nLogo file: {logo_path}")
        print(f"Image size: {img.size}")
        print(f"\n📌 TOP 5 DOMINANT COLORS:\n")
        
        for i, (color, count) in enumerate(most_common, 1):
            r, g, b = color
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            rgb_str = f"rgb({r}, {g}, {b})"
            percentage = (count / len(filtered_colors)) * 100
            
            print(f"{i}. {hex_color} ({rgb_str})")
            print(f"   Frequency: {percentage:.1f}%\n")
        
        # Get primary and secondary colors
        primary_color = most_common[0][0]
        primary_hex = f"#{primary_color[0]:02x}{primary_color[1]:02x}{primary_color[2]:02x}"
        
        secondary_color = most_common[1][0] if len(most_common) > 1 else most_common[0][0]
        secondary_hex = f"#{secondary_color[0]:02x}{secondary_color[1]:02x}{secondary_color[2]:02x}"
        
        print("="*60)
        print(f"\n✨ SUGGESTED THEME COLORS:")
        print(f"   Primary Color: {primary_hex}")
        print(f"   Secondary Color: {secondary_hex}")
        print("\n" + "="*60)
        
    else:
        print("⚠️  Could not extract meaningful colors from logo")
        print("Make sure the logo has distinct colors (not just white/black)")
        
except FileNotFoundError:
    print(f"❌ Logo file not found at: {logo_path}")
    print(f"   Please ensure logo.png is in: app/static/images/")
except Exception as e:
    print(f"❌ Error analyzing logo: {e}")
    print("   Make sure Pillow is installed: pip install Pillow")
