
import os
import re
from PIL import Image, ImageDraw, ImageFont
from cobraprint import col
from ebooklib import epub
from bs4 import BeautifulSoup  # For potential HTML cleaning, but minimally used here

def create_cover_image(input_image_path, output_image_path):
    """
    Creates the EPUB cover image by adding text overlays to the base image.
    Harmonizes font colors with dark brown background (using gold and white).
    """
    img = Image.open(input_image_path)
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Font paths (adjust if needed for Linux Mint; using system fonts)
    regular_font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    italic_font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf'
    
    # Colors: Gold for main, white for others
    gold_color = (255, 215, 0)  # #FFD700
    white_color = (255, 255, 255)  # #FFFFFF
    
    # Subtitle: "Authentic Dhamma" at top
    subtitle_font = ImageFont.truetype(regular_font_path, 200)
    subtitle_text = "Authentic Dhamma"
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    draw.text(((width - subtitle_width) / 2, 200), subtitle_text, font=subtitle_font, fill=white_color)
    
    # Main title: "Buddha's Words"
    main_font = ImageFont.truetype(regular_font_path, 400)
    main_text = "Buddha's Words"
    main_bbox = draw.textbbox((0, 0), main_text, font=main_font)
    main_width = main_bbox[2] - main_bbox[0]
    draw.text(((width - main_width) / 2, 600), main_text, font=main_font, fill=gold_color)
    
    # Small italic: "Selected suttas from Dīgha and Majjhima Nikāyas - in Russian & English translations"
    italic_font = ImageFont.truetype(italic_font_path, 100)
    italic_text = "Selected suttas from Dīgha and Majjhima Nikāyas - in Russian & English translations"
    italic_bbox = draw.textbbox((0, 0), italic_text, font=italic_font)
    italic_width = italic_bbox[2] - italic_bbox[0]
    draw.text(((width - italic_width) / 2, 1100), italic_text, font=italic_font, fill=white_color)
    
    # Bottom: "www.probud.narod.ru"
    bottom_font = ImageFont.truetype(regular_font_path, 150)
    bottom_text = "www.probud.narod.ru"
    bottom_bbox = draw.textbbox((0, 0), bottom_text, font=bottom_font)
    bottom_width = bottom_bbox[2] - bottom_bbox[0]
    draw.text(((width - bottom_width) / 2, height - 600), bottom_text, font=bottom_font, fill=white_color)
    
    # Small bottom: "Ebook made by www.github.com/LovelyCobra"
    small_font = ImageFont.truetype(regular_font_path, 50)
    small_text = "Ebook made by www.github.com/LovelyCobra"
    small_bbox = draw.textbbox((0, 0), small_text, font=small_font)
    small_width = small_bbox[2] - small_bbox[0]
    draw.text(((width - small_width) / 2, height - 100), small_text, font=small_font, fill=white_color)
    
    img.save(output_image_path)

def generate_title_page_html():
    """
    Generates HTML for the title page with the same information as the cover.
    """
    html = """
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>Title Page</title>
        <style>
            body { text-align: center; font-family: sans-serif; }
            .subtitle { font-size: 2em; color: #FFFFFF; }
            .main-title { font-size: 4em; color: #FFD700; }
            .italic-small { font-size: 1em; font-style: italic; color: #FFFFFF; }
            .bottom { font-size: 1.5em; color: #FFFFFF; }
            .small-bottom { font-size: 0.8em; color: #FFFFFF; }
        </style>
    </head>
    <body>
        <div class="subtitle">Authentic Dhamma</div>
        <div class="main-title">Buddha's Words</div>
        <div class="italic-small">Selected suttas from Dīgha and Majjhima Nikāyas - in Russian & English translations</div>
        <br/><br/><br/><br/>
        <div class="bottom">www.probud.narod.ru</div>
        <div class="small-bottom">Ebook made by www.github.com/LovelyCobra</div>
    </body>
    </html>
    """
    return html

def extract_russian_title(file_path):
    """
    Extracts the Russian sutta title from the HTML file (e.g., "Маханидана Сутта").
    Searches for the first line containing and ending with 'Сутта'.
    """
    with open(file_path, 'r', encoding='utf-8') as fp:
        for line in fp:
            line = line.strip()
            if 'Сутта' in line and line.endswith('Сутта'):
                return line
    return "Unknown Title"  # Fallback

def clean_html_content(file_path):
    """
    Reads the HTML file, removes <DOCUMENT> tags, and returns cleaned content as string.
    Preserves font colors and styles.
    """
    with open(file_path, 'r', encoding='utf-8') as fp:
        content = fp.read()
    
    # Remove <DOCUMENT> and </DOCUMENT>
    content = re.sub(r'<DOCUMENT filename="[^"]+">', '', content)
    content = content.replace('</DOCUMENT>', '')
    
    # Wrap in proper XHTML if needed (assume it's already HTML-like)
    soup = BeautifulSoup(content, 'html.parser')
    return str(soup)  # Returns prettified HTML

def create_epub_chapter(file_name, chap_title, content):
    """
    Creates an EpubHtml item for a chapter.
    """
    chap = epub.EpubHtml(title=chap_title, file_name=file_name.replace('.html', '.xhtml'), lang='ru')
    chap.content = content
    return chap

def main():
    dir_path = 'probud_narod'
    output_epub = 'buddhas_words.epub'
    cover_image_path = os.path.join(dir_path, 'probnar_cover.jpg')
    generated_cover_path = 'cover.jpg'
    
    # Create cover image
    create_cover_image(cover_image_path, generated_cover_path)
    
    # Initialize EPUB book
    book = epub.EpubBook()
    book.set_identifier('buddhas-words-2025')
    book.set_title("Buddha's Words")
    book.set_language('en')
    book.add_author('Buddha')
    
    # Set cover
    with open(generated_cover_path, 'rb') as cover_file:
        book.set_cover('cover.jpg', cover_file.read())
    
    # Title page
    title_html = generate_title_page_html()
    title_chap = epub.EpubHtml(title='Title Page', file_name='title.xhtml')
    title_chap.content = title_html
    book.add_item(title_chap)
    
    # Get and sort files
    # files = [f for f in os.listdir(dir_path) if f.endswith('.html')]
    # dn_files = sorted([f for f in files if f.startswith('DN')], key=lambda x: int(x[2:-5]))
    # mn_files = sorted([f for f in files if f.startswith('MN')], key=lambda x: int(x[2:-5]))
    sutta_list = [item for item in os.listdir('probud_narod') if item.endswith('.html')]
    sutta_list.sort()
    dn_files = sutta_list[:4]
    mn_files = sutta_list[4:]

    def sorting(file_name):
        sutta_num = re.search('[0-9]+', file_name).group()
        return int(sutta_num)
    
    mn_files.sort(key=sorting)
    
    # Digha chapters
    digha_chaps = []
    chap_num = 1
    for f in dn_files:
        full_path = os.path.join(dir_path, f)
        russian_title = extract_russian_title(full_path)
        code = f[:-5]
        chapter_code = f"{code[:2]} {code[2:]}"
        chap_title = f"{chap_num}. {russian_title} {chapter_code}"
        content = clean_html_content(full_path)
        chap_file_name = f"dn{chap_num}.xhtml"
        chap = create_epub_chapter(chap_file_name, chap_title, content)
        book.add_item(chap)
        digha_chaps.append(chap)
        chap_num += 1
    
    # Majjhima chapters
    majjhima_chaps = []
    chap_num = 1
    for f in mn_files:
        full_path = os.path.join(dir_path, f)
        russian_title = extract_russian_title(full_path)
        code = f[:-5]
        chapter_code = f"{code[:2]} {code[2:]}"
        chap_title = f"{chap_num}. {russian_title} {chapter_code}"
        content = clean_html_content(full_path)
        chap_file_name = f"mn{chap_num}.xhtml"
        chap = create_epub_chapter(chap_file_name, chap_title, content)
        book.add_item(chap)
        majjhima_chaps.append(chap)
        chap_num += 1
    
    # TOC structure
    book.toc = [
        title_chap,
        epub.Section('Dīgha Nikāya', digha_chaps),
        epub.Section('Majjhima Nikāya', majjhima_chaps)
    ]
    
    # Spine (reading order)
    book.spine = ['cover', title_chap] + digha_chaps + majjhima_chaps
    
    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Write EPUB
    epub.write_epub(output_epub, book, {})
    
    # Clean up generated cover
    os.remove(generated_cover_path)
    
    print(f"EPUB created: {output_epub}")

if __name__ == "__main__":
    main()
    
    
    # print(f'{col.SEP}{dn_files}\n\n{mn_files}{col.SEP}')