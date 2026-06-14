from PIL import Image, ImageDraw, ImageFont
import os

def generate_logo():
    # Load icon
    icon_path = 'assets/neurex_icon.png'
    icon = Image.open(icon_path).convert("RGBA")
    
    # Target height 120
    target_height = 120
    aspect_ratio = icon.width / icon.height
    target_width = int(target_height * aspect_ratio)
    icon = icon.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # Create canvas: width 620, height 120
    canvas_width = 620
    canvas = Image.new("RGBA", (canvas_width, target_height), (0, 0, 0, 0))
    
    # Paste icon at left
    canvas.alpha_composite(icon, (0, 0))
    
    # Setup draw
    draw = ImageDraw.Draw(canvas)
    
    # Find font
    font_paths = [
        'assets/conthrax_font/Conthrax-SemiBold.otf',
        '.neurex/skills/neurex-awesome-skills/skills/canvas-design/canvas-fonts/Outfit-Bold.ttf',
        '/usr/share/fonts/TTF/OpenSans-Bold.ttf',
        '/usr/share/fonts/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/noto/NotoSans-Bold.ttf'
    ]
    
    font = None
    for path in font_paths:
        if os.path.exists(path):
            font = ImageFont.truetype(path, 80)
            break
            
    if not font:
        font = ImageFont.load_default()
        print("Warning: default font loaded")
        
    # Text coordinates
    text = "NEUREX"
    # Measure text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text vertically: (canvas_height - text_height) // 2
    # Adjust y-offset due to font descenders/ascenders
    y_pos = (target_height - text_height) // 2 - bbox[1]
    x_pos = target_width + 24 # 24px spacing
    
    # Draw text in clean light grey (#e8e8f0)
    draw.text((x_pos, y_pos), text, fill=(232, 232, 240, 255), font=font)
    
    # Crop to content width
    total_width = x_pos + text_width + 10
    canvas = canvas.crop((0, 0, total_width, target_height))
    
    # Save logo
    canvas.save('assets/neurex_logo.png', 'PNG')
    print(f"Merged logo saved successfully (width: {total_width}, height: {target_height})")

if __name__ == '__main__':
    generate_logo()
