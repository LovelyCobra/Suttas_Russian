from PIL import Image, ImageDraw, ImageFont
import os

def add_text_to_image(input_path, output_path):
    """
    Add Russian text overlays to the JPG image as specified
    """
    # Open the image
    img = Image.open(input_path)
    width, height = img.size
    
    # Create a drawing context
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts (you may need to adjust paths based on your system)
    try:
        # For Windows
        font_h3 = ImageFont.truetype("arial.ttf", int(height * 0.04))  # Top subtitle
        font_h2 = ImageFont.truetype("arial.ttf", int(height * 0.06))  # СУТТАНТА
        font_h1 = ImageFont.truetype("arial.ttf", int(height * 0.1))   # Main title
        font_h4 = ImageFont.truetype("arial.ttf", int(height * 0.035)) # Bottom subtitle
    except:
        try:
            # For macOS
            font_h3 = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", int(height * 0.04))
            font_h2 = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", int(height * 0.06))
            font_h1 = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", int(height * 0.1))
            font_h4 = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", int(height * 0.035))
        except:
            try:
                # For Linux
                font_h3 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(height * 0.04))
                font_h2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(height * 0.06))
                font_h1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(height * 0.1))
                font_h4 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(height * 0.035))
            except:
                # Fallback to default font
                font_h3 = ImageFont.load_default()
                font_h2 = ImageFont.load_default()
                font_h1 = ImageFont.load_default()
                font_h4 = ImageFont.load_default()
    
    # Define colors
    light_green = (129, 199, 132)  # Light green for outlines
    light_text = (232, 245, 232)   # Very light green/white for text
    semi_transparent_bg = (46, 125, 50, 180)  # Semi-transparent dark green
    
    # Text content
    text_h3 = "Палийский канон"
    text_h2 = "СУТТАНТА"
    text_h1 = "Дигха Никая"
    text_h4 = "www.theravada.ru"
    
    # Helper function to get text dimensions
    def get_text_bbox(text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    # Helper function to draw text with background
    def draw_text_with_bg(text, font, position, text_color, bg_color=None, bg_padding=10):
        text_width, text_height = get_text_bbox(text, font)
        x, y = position
        
        if bg_color:
            # Create a semi-transparent overlay for background
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([
                (0, y - bg_padding),
                (width, y + text_height + bg_padding)
            ], fill=bg_color)
            img.paste(Image.alpha_composite(img.convert('RGBA'), overlay), (0, 0))
            draw = ImageDraw.Draw(img)
        
        # Draw text shadow for better visibility
        shadow_offset = 2
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), text, font=font, fill=text_color)
    
    # Helper function to draw outlined text (for main title)
    def draw_outlined_text(text, font, position, outline_color, outline_width=3):
        x, y = position
        
        # Draw outline by drawing text in multiple positions
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    
    # 1. Top subtitle: "Палийский канон" with colored background
    h3_width, h3_height = get_text_bbox(text_h3, font_h3)
    h3_x = (width - h3_width) // 2
    h3_y = int(height * 0.05)
    draw_text_with_bg(text_h3, font_h3, (h3_x, h3_y), light_text, semi_transparent_bg, 15)
    
    # 2. H2 subtitle: "СУТТАНТА" in upper part
    h2_width, h2_height = get_text_bbox(text_h2, font_h2)
    h2_x = (width - h2_width) // 2
    h2_y = int(height * 0.25)
    draw_text_with_bg(text_h2, font_h2, (h2_x, h2_y), light_text)
    
    # 3. Main title: "Дигха Никая" with light green outline and transparent middle
    h1_width, h1_height = get_text_bbox(text_h1, font_h1)
    h1_x = (width - h1_width) // 2
    h1_y = int(height * 0.45)
    
    # Draw the outlined text
    draw_outlined_text(text_h1, font_h1, (h1_x, h1_y), light_green, 4)
    
    # 4. Bottom subtitle: "www.theravada.ru"
    h4_width, h4_height = get_text_bbox(text_h4, font_h4)
    h4_x = (width - h4_width) // 2
    h4_y = int(height * 0.9)
    
    # Create a subtle background for the bottom text
    bottom_bg = (27, 94, 32, 150)
    draw_text_with_bg(text_h4, font_h4, (h4_x, h4_y), light_text, bottom_bg, 12)
    
    # Save the result
    # Convert back to RGB if it was converted to RGBA
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    img.save(output_path, 'JPEG', quality=95)
    print(f"Image saved as {output_path}")

def main(input_path, output_path):
    # Input and output file paths
    input_image = input_path  # Replace with your image filename
    output_image = output_path
    
    # Check if input file exists
    if not os.path.exists(input_image):
        print(f"Error: Input file '{input_image}' not found.")
        print("Please make sure your JPG image is in the same directory and named correctly.")
        return
    
    try:
        add_text_to_image(input_image, output_image)
        print("Text overlay completed successfully!")
    except Exception as e:
        print(f"Error processing image: {e}")

if __name__ == "__main__":
    input_path = 'Russ_suttas/Digha_cover.jpg'
    output_path = 'Russ_suttas/Digha-cover.jpg'

    main(input_path, output_path)