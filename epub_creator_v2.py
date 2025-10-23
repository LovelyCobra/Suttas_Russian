#!/usr/bin/env python3
"""
EPUB Creator for Buddha's Words - Selected Suttas
Functional programming approach for converting HTML suttas to EPUB format
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict
from PIL import Image, ImageDraw, ImageFont
from ebooklib import epub


def create_cover_image(source_image_path: str, output_path: str) -> None:
    """Create cover image with text overlay on the source image."""
    try:
        # Open the source image
        img = Image.open(source_image_path)
        draw = ImageDraw.Draw(img)
        
        # Get image dimensions
        width, height = img.size
        
        # Try to load fonts (fallback to default if not available)
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 120)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 80)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf", 50)
            tiny_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 35)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            tiny_font = ImageFont.load_default()
        
        # Text color that harmonizes with dark brown
        text_color = "#F4E4BC"  # Cream/beige color
        
        # Add subtitle at the top
        subtitle_text = "Authentic Dhamma"
        subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        draw.text(((width - subtitle_width) // 2, height * 0.08), subtitle_text, 
                 fill=text_color, font=subtitle_font)
        
        # Add main title
        title_text = "Buddha's Words"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((width - title_width) // 2, height * 0.18), title_text, 
                 fill=text_color, font=title_font)
        
        # Add description
        desc_lines = [
            "Selected suttas from Dīgha and",
            "Majjhima Nikāyas - in Russian",
            "& English translations"
        ]
        y_pos = height * 0.32
        for line in desc_lines:
            line_bbox = draw.textbbox((0, 0), line, font=small_font)
            line_width = line_bbox[2] - line_bbox[0]
            draw.text(((width - line_width) // 2, y_pos), line, 
                     fill=text_color, font=small_font)
            y_pos += 60
        
        # Add website at bottom
        website_text = "www.probud.narod.ru"
        website_bbox = draw.textbbox((0, 0), website_text, font=subtitle_font)
        website_width = website_bbox[2] - website_bbox[0]
        draw.text(((width - website_width) // 2, height * 0.85), website_text, 
                 fill=text_color, font=subtitle_font)
        
        # Add creator info at very bottom
        creator_text = "Ebook made by www.github.com/LovelyCobra"
        creator_bbox = draw.textbbox((0, 0), creator_text, font=tiny_font)
        creator_width = creator_bbox[2] - creator_bbox[0]
        draw.text(((width - creator_width) // 2, height * 0.94), creator_text, 
                 fill=text_color, font=tiny_font)
        
        # Save the cover
        img.save(output_path, "JPEG", quality=90)
        print(f"Cover image created: {output_path}")
        
    except Exception as e:
        print(f"Error creating cover image: {e}")


def extract_sutta_info(html_content: str, filename: str) -> Dict[str, str]:
    """Extract sutta information from HTML content."""
    info = {
        'title': '',
        'subtitle': '',
        'nikaya': '',
        'number': '',
        'filename': filename
    }
    
    # Extract title from the HTML
    title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
    if title_match:
        title_text = title_match.group(1).strip()
        # Clean up the title
        title_text = re.sub(r'\s+', ' ', title_text)
        info['title'] = title_text
    
    # Extract Nikaya info from font color purple text
    nikaya_match = re.search(r'<font color="#8000ff"[^>]*>(.*?)</font>', html_content, re.IGNORECASE | re.DOTALL)
    if nikaya_match:
        nikaya_text = nikaya_match.group(1).strip()
        nikaya_text = re.sub(r'<[^>]+>', '', nikaya_text)  # Remove HTML tags
        info['nikaya'] = nikaya_text
        
        # Extract number (DN/MN followed by number)
        number_match = re.search(r'(DN|MN)\s*(\d+)', nikaya_text)
        if number_match:
            info['number'] = f"{number_match.group(1)} {number_match.group(2)}"
    
    # Extract main sutta title
    main_title_match = re.search(r'<font size="\+2"><b>(.*?)</b></font>', html_content, re.IGNORECASE | re.DOTALL)
    if main_title_match:
        main_title = main_title_match.group(1).strip()
        main_title = re.sub(r'<[^>]+>', '', main_title)
        info['subtitle'] = main_title
    
    return info


def clean_html_content(html_content: str) -> str:
    """Clean and format HTML content for EPUB."""
    # Remove scripts and tracking code
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'<noscript[^>]*>.*?</noscript>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove navigation and page structure
    html_content = re.sub(r'<table[^>]*>.*?<tbody>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    html_content = re.sub(r'</tbody>.*?</table>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove header metadata but keep the main title sections
    html_content = re.sub(r'<p class="right">.*?</p>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove images and navigation links
    html_content = re.sub(r'<div align="center"><img[^>]*></div>', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'<p class="center">.*?</p>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    
    # Clean up extra whitespace and line breaks
    html_content = re.sub(r'\n\s*\n', '\n', html_content)
    html_content = re.sub(r'<br>\s*<br>', '<br/>', html_content, flags=re.IGNORECASE)
    
    return html_content.strip()


def create_chapter_html(sutta_info: Dict[str, str], html_content: str) -> str:
    """Create properly formatted HTML chapter for EPUB."""
    clean_content = clean_html_content(html_content)
    
    # Extract the main content (everything after the title section)
    content_match = re.search(r'<h3.*?</h3>(.*)', clean_content, re.DOTALL | re.IGNORECASE)
    if content_match:
        main_content = content_match.group(1)
    else:
        # Fallback: look for content after the title section
        title_end = re.search(r'</div>\s*<h3', clean_content, re.IGNORECASE)
        if title_end:
            main_content = clean_content[title_end.end()-3:]
        else:
            main_content = clean_content
    
    # Create the EPUB chapter HTML
    chapter_html = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{sutta_info['subtitle']}</title>
    <style type="text/css">
        body {{
            font-family: serif;
            line-height: 1.6;
            margin: 1em;
        }}
        .pali {{ color: #8B4513; font-family: "Times New Roman", serif; }}
        .english {{ color: #4848ee; }}
        .russian {{ color: black; }}
        h1, h2, h3 {{ color: #8B4513; }}
        .center {{ text-align: center; }}
        .right {{ text-align: right; }}
        font[color="brown"] {{ color: #8B4513 !important; }}
        font[color="#4848ee"] {{ color: #4848ee !important; }}
        font[color="#8000ff"] {{ color: #8000ff !important; }}
    </style>
</head>
<body>
    <h1>{sutta_info['subtitle']} ({sutta_info['number']})</h1>
    {main_content}
</body>
</html>'''
    
    return chapter_html


def create_title_page() -> str:
    """Create the title page HTML."""
    return '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Title Page</title>
    <style type="text/css">
        body {
            font-family: serif;
            text-align: center;
            margin: 2em;
        }
        .subtitle { font-size: 1.2em; color: #8B4513; margin-bottom: 0.5em; }
        .title { font-size: 2.5em; font-weight: bold; color: #8B4513; margin: 1em 0; }
        .description { font-style: italic; font-size: 1.1em; margin: 2em 0; }
        .website { font-size: 1.2em; color: #8B4513; margin-top: 3em; }
        .creator { font-size: 0.9em; color: #666; margin-top: 2em; }
    </style>
</head>
<body>
    <div class="subtitle">Authentic Dhamma</div>
    <div class="title">Buddha's Words</div>
    <div class="description">
        Selected suttas from Dīgha and Majjhima Nikāyas<br/>
        in Russian &amp; English translations
    </div>
    <div class="website">www.probud.narod.ru</div>
    <div class="creator">Ebook made by www.github.com/LovelyCobra</div>
</body>
</html>'''


def create_toc_page(suttas_info: List[Dict[str, str]]) -> str:
    """Create table of contents HTML."""
    digha_suttas = [s for s in suttas_info if 'DN' in s.get('number', '')]
    majjhima_suttas = [s for s in suttas_info if 'MN' in s.get('number', '')]
    
    # Sort by number
    def sort_key(sutta):
        num_match = re.search(r'(\d+)', sutta.get('number', ''))
        return int(num_match.group(1)) if num_match else 0
    
    digha_suttas.sort(key=sort_key)
    majjhima_suttas.sort(key=sort_key)
    
    toc_html = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Table of Contents</title>
    <style type="text/css">
        body {
            font-family: serif;
            margin: 2em;
        }
        h1 { color: #8B4513; text-align: center; }
        h2 { color: #8B4513; margin-top: 2em; }
        .toc-entry {
            margin: 0.5em 0;
            margin-left: 1em;
        }
        a { text-decoration: none; color: black; }
        a:hover { text-decoration: underline; }
        .sutta-number { color: #8B4513; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Table of Contents</h1>
    
    <h2>Dīgha Nikāya</h2>'''
    
    counter = 1
    for sutta in digha_suttas:
        title = sutta.get('subtitle', '').replace(' Сутта', ' Сутта')
        number = sutta.get('number', '')
        toc_html += f'''
    <div class="toc-entry">
        <span class="sutta-number">{counter}.</span> <a href="chapter{counter:02d}.xhtml">{title} {number}</a>
    </div>'''
        counter += 1
    
    toc_html += '''
    
    <h2>Majjhima Nikāya</h2>'''
    
    for sutta in majjhima_suttas:
        title = sutta.get('subtitle', '').replace(' Сутта', ' Сутта')
        number = sutta.get('number', '')
        toc_html += f'''
    <div class="toc-entry">
        <span class="sutta-number">{counter}.</span> <a href="chapter{counter:02d}.xhtml">{title} {number}</a>
    </div>'''
        counter += 1
    
    toc_html += '''
</body>
</html>'''
    
    return toc_html


def create_epub_structure(suttas_info: List[Dict[str, str]]) -> Dict[str, str]:
    """Create EPUB structure files."""
    files = {}
    
    # Create mimetype
    files['mimetype'] = 'application/epub+zip'
    
    # Create container.xml
    files['META-INF/container.xml'] = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
    
    # Create content.opf
    manifest_items = '''    <item id="cover" href="cover.jpg" media-type="image/jpeg"/>
    <item id="titlepage" href="titlepage.xhtml" media-type="application/xhtml+xml"/>
    <item id="toc" href="toc.xhtml" media-type="application/xhtml+xml"/>'''
    
    spine_items = '''    <itemref idref="titlepage"/>
    <itemref idref="toc"/>'''
    
    for i, sutta in enumerate(suttas_info, 1):
        chapter_id = f"chapter{i:02d}"
        manifest_items += f'''
    <item id="{chapter_id}" href="{chapter_id}.xhtml" media-type="application/xhtml+xml"/>'''
        spine_items += f'''
    <itemref idref="{chapter_id}"/>'''
    
    files['OEBPS/content.opf'] = f'''<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:identifier id="BookId">urn:uuid:buddha-words-{datetime.now().strftime('%Y%m%d')}</dc:identifier>
        <dc:title>Buddha's Words: Selected Suttas</dc:title>
        <dc:creator opf:role="aut">Buddha Shakyamuni</dc:creator>
        <dc:contributor opf:role="trl">Various Translators</dc:contributor>
        <dc:publisher>www.probud.narod.ru</dc:publisher>
        <dc:date>{datetime.now().strftime('%Y-%m-%d')}</dc:date>
        <dc:language>en</dc:language>
        <dc:language>ru</dc:language>
        <dc:subject>Buddhism</dc:subject>
        <dc:subject>Dhamma</dc:subject>
        <dc:subject>Suttas</dc:subject>
        <meta name="cover" content="cover"/>
    </metadata>
    <manifest>
{manifest_items}
    </manifest>
    <spine toc="toc">
{spine_items}
    </spine>
</package>'''
    
    # Create toc.ncx
    nav_points = ''
    play_order = 3
    for i, sutta in enumerate(suttas_info, 1):
        title = sutta.get('subtitle', '').replace('&', '&amp;')
        nav_points += f'''
        <navPoint id="chapter{i:02d}" playOrder="{play_order}">
            <navLabel><text>{title}</text></navLabel>
            <content src="chapter{i:02d}.xhtml"/>
        </navPoint>'''
        play_order += 1
    
    files['OEBPS/toc.ncx'] = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
    <head>
        <meta name="dtb:uid" content="urn:uuid:buddha-words-{datetime.now().strftime('%Y%m%d')}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle><text>Buddha's Words: Selected Suttas</text></docTitle>
    <navMap>
        <navPoint id="titlepage" playOrder="1">
            <navLabel><text>Title Page</text></navLabel>
            <content src="titlepage.xhtml"/>
        </navPoint>
        <navPoint id="toc" playOrder="2">
            <navLabel><text>Table of Contents</text></navLabel>
            <content src="toc.xhtml"/>
        </navPoint>{nav_points}
    </navMap>
</ncx>'''
    
    return files


def process_html_files(directory: str) -> List[Tuple[Dict[str, str], str]]:
    """Process all HTML files in the directory."""
    html_files = []
    directory_path = Path(directory)
    
    for file_path in directory_path.glob("*.html"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            sutta_info = extract_sutta_info(content, file_path.name)
            html_files.append((sutta_info, content))
            print(f"Processed: {sutta_info.get('subtitle', file_path.name)} ({sutta_info.get('number', 'Unknown')})")
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Sort files: DN first, then MN, by number
    def sort_key(item):
        sutta_info, _ = item
        number_str = sutta_info.get('number', '')
        if 'DN' in number_str:
            num_match = re.search(r'(\d+)', number_str)
            return (0, int(num_match.group(1)) if num_match else 0)
        elif 'MN' in number_str:
            num_match = re.search(r'(\d+)', number_str)
            return (1, int(num_match.group(1)) if num_match else 0)
        else:
            return (2, 0)
    
    html_files.sort(key=sort_key)
    return html_files


def create_epub(source_directory: str, output_filename: str) -> None:
    """Main function to create the EPUB file using ebooklib."""
    source_path = Path(source_directory)
    
    # Check if source directory exists
    if not source_path.exists():
        print(f"Error: Directory {source_directory} does not exist")
        return
    
    # Process HTML files
    print("Processing HTML files...")
    processed_files = process_html_files(source_directory)
    
    if not processed_files:
        print("No HTML files found to process")
        return
    
    suttas_info = [info for info, _ in processed_files]
    
    # Create EPUB book
    print("Creating EPUB book structure...")
    book = epub.EpubBook(suttas_info)
    
    # Create cover image
    cover_source = source_path / "probnar_cover.jpg"
    cover_output = "temp_cover.jpg"
    
    if cover_source.exists():
        print("Creating cover image...")
        create_cover_image(str(cover_source), cover_output)
        
        # Add cover to book
        if os.path.exists(cover_output):
            with open(cover_output, 'rb') as cover_file:
                book.set_cover("cover.jpg", cover_file.read())
            os.remove(cover_output)  # Clean up temporary file
    else:
        print("Warning: Cover image not found, skipping cover creation")
    
    # Create CSS for styling
    css_style = '''
        body {
            font-family: serif;
            line-height: 1.6;
            margin: 1em;
        }
        .pali { color: #8B4513; font-family: "Times New Roman", serif; }
        .english { color: #4848ee; }
        .russian { color: black; }
        h1, h2, h3 { color: #8B4513; }
        .center { text-align: center; }
        .right { text-align: right; }
        font[color="brown"] { color: #8B4513 !important; }
        font[color="#4848ee"] { color: #4848ee !important; }
        font[color="#8000ff"] { color: #8000ff !important; }
        .subtitle { font-size: 1.2em; color: #8B4513; margin-bottom: 0.5em; }
        .title { font-size: 2.5em; font-weight: bold; color: #8B4513; margin: 1em 0; }
        .description { font-style: italic; font-size: 1.1em; margin: 2em 0; }
        .website { font-size: 1.2em; color: #8B4513; margin-top: 3em; }
        .creator { font-size: 0.9em; color: #666; margin-top: 2em; }
        .toc-entry { margin: 0.5em 0; margin-left: 1em; }
        a { text-decoration: none; color: black; }
        a:hover { text-decoration: underline; }
        .sutta-number { color: #8B4513; font-weight: bold; }
    '''
    
    # Add CSS to book
    nav_css = epub.EpubItem(uid="nav_css", file_name="style/nav.css", 
                           media_type="text/css", content=css_style)
    book.add_item(nav_css)
    
    # Create title page
    title_page_content = create_title_page()
    title_page = epub.EpubHtml(title='Title Page', file_name='titlepage.xhtml')
    title_page.content = title_page_content
    title_page.add_item(nav_css)
    book.add_item(title_page)
    
    # Create table of contents page
    toc_content = create_toc_page(suttas_info)
    toc_page = epub.EpubHtml(title='Table of Contents', file_name='toc.xhtml')
    toc_page.content = toc_content
    toc_page.add_item(nav_css)
    book.add_item(toc_page)
    
    # Add chapters
    print("Creating chapters...")
    chapters = []
    toc_sections = []
    
    # Organize chapters by Nikaya
    digha_chapters = []
    majjhima_chapters = []
    
    for i, (sutta_info, html_content) in enumerate(processed_files, 1):
        chapter_html = create_chapter_html(sutta_info, html_content)
        
        chapter = epub.EpubHtml(
            title=sutta_info.get('subtitle', f'Chapter {i}'),
            file_name=f'chapter{i:02d}.xhtml'
        )
        chapter.content = chapter_html
        chapter.add_item(nav_css)
        
        book.add_item(chapter)
        chapters.append(chapter)
        
        # Organize by Nikaya for TOC
        if 'DN' in sutta_info.get('number', ''):
            digha_chapters.append(chapter)
        elif 'MN' in sutta_info.get('number', ''):
            majjhima_chapters.append(chapter)
    
    # Create navigation structure
    book.toc = (
        epub.Link("titlepage.xhtml", "Title Page", "title"),
        epub.Link("toc.xhtml", "Table of Contents", "toc"),
        (epub.Section('Dīgha Nikāya'), digha_chapters),
        (epub.Section('Majjhima Nikāya'), majjhima_chapters)
    )
    
    # Create spine (reading order)
    book.spine = ['nav', title_page, toc_page] + chapters
    
    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Write EPUB file
    print(f"Writing EPUB file: {output_filename}")
    epub.write_epub(output_filename, book, {})
    
    print(f"EPUB created successfully: {output_filename}")
    print(f"Processed {len(suttas_info)} suttas:")
    for info in suttas_info:
        print(f"  - {info.get('subtitle', 'Unknown')} ({info.get('number', 'Unknown')})")



if __name__ == "__main__":
    # Configuration
    SOURCE_DIRECTORY = "probud_narod"
    OUTPUT_FILENAME = "buddhas_words_selected_suttas.epub"
    
    # Create the EPUB
    create_epub(SOURCE_DIRECTORY, OUTPUT_FILENAME)