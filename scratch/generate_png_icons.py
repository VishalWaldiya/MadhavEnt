from PIL import Image, ImageDraw, ImageFont
import os

def create_pwa_icon(size, output_path):
    # Create background image with dark slate color #0f172a
    img = Image.new('RGBA', (size, size), (15, 23, 42, 255))
    draw = ImageDraw.Draw(img)
    
    # Draw rounded rectangle container / glowing circle
    margin = int(size * 0.1)
    circle_box = [margin, margin, size - margin, size - margin]
    draw.ellipse(circle_box, fill=(30, 41, 59, 255), outline=(59, 130, 246, 255), width=int(size * 0.03))
    
    # Draw Bolt / Energy Icon (lightning bolt polygon)
    # Scale polygon coordinates based on size
    s = size / 512.0
    bolt_points = [
        (270 * s, 100 * s),
        (190 * s, 260 * s),
        (255 * s, 260 * s),
        (220 * s, 410 * s),
        (330 * s, 230 * s),
        (265 * s, 230 * s)
    ]
    draw.polygon(bolt_points, fill=(59, 130, 246, 255)) # Primary blue #3b82f6

    # Inner highlight bolt
    bolt_inner = [
        (270 * s, 120 * s),
        (205 * s, 250 * s),
        (260 * s, 250 * s),
        (230 * s, 380 * s),
        (315 * s, 240 * s),
        (260 * s, 240 * s)
    ]
    draw.polygon(bolt_inner, fill=(96, 165, 250, 255)) # Light blue #60a5fa

    img.save(output_path, 'PNG')
    print(f"Saved {output_path} ({size}x{size})")

os.makedirs('static/icons', exist_ok=True)
create_pwa_icon(192, 'static/icons/icon-192.png')
create_pwa_icon(512, 'static/icons/icon-512.png')
create_pwa_icon(180, 'static/icons/apple-touch-icon.png')
