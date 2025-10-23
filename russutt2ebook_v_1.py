#!/usr/bin/env python3
"""
Functional EPUB generator for Russian sutta translations from theravada.ru
Uses functional programming paradigms with pure functions where possible.
"""

import requests
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
import re, os, time
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from functools import partial
from tqdm import tqdm
import uuid
import html


# Configuration
BASE_URL = "https://theravada.ru/Teaching/Canon/Suttanta/Texts/"
ENCODING = 'windows-1251'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
    }


def create_session() -> requests.Session:
    """Create configured requests session."""
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    return session


def fetch_page_content(session: requests.Session, url: str) -> str:
    """Fetch and decode page content with proper encoding."""
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        # Decode with windows-1251
        content = response.content.decode(ENCODING)
        return content
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""


def extract_sutta_info(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract sutta title and metadata from BeautifulSoup object."""
    # Extract main title
    title_elem = soup.find('font', size='5')
    title = title_elem.get_text().strip() if title_elem else "Untitled"
    
    # Extract sutta number (e.g., "МН 141")
    sutta_num = ""
    if title_elem and title_elem.find_next('font', size='3'):
        sutta_num = title_elem.find_next('font', size='3').get_text().strip()
    
    # Extract translation info
    translation_info = ""
    info_div = soup.find('div', align='right')
    if info_div:
        translation_info = info_div.get_text().strip()
    
    return {
        'title': title,
        'sutta_number': sutta_num,
        'translation_info': translation_info
    }


def clean_text_content(text: str) -> str:
    """Clean and normalize text content."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def extract_sutta_content(soup: BeautifulSoup) -> str:
    """Extract and format sutta content as clean HTML."""
    # Find the main content table
    content_td = soup.find('td', {'style': 'text-align: justify', 'valign': 'top'})
    if not content_td:
        return "<p>Content not found</p>"
    
    # Start building clean HTML
    html_parts = []
    
    # Process each div with class 'a' (indented paragraphs)
    for div in content_td.find_all('div'):
        if div.get('class') == ['a'] or 'TEXT-INDENT: 2em' in str(div):
            # This is a paragraph
            text_content = div.get_text().strip()
            if text_content:
                # Check if it's a section header (bold text)
                bold_elem = div.find('b')
                if bold_elem and len(bold_elem.get_text().strip()) > 10:
                    # Section header
                    html_parts.append(f"<h3>{html.escape(text_content)}</h3>")
                else:
                    # Regular paragraph
                    html_parts.append(f"<p class='indent'>{html.escape(text_content)}</p>")
    
    # If no structured content found, extract all text
    if not html_parts:
        text_content = content_td.get_text()
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
        html_parts = [f"<p>{html.escape(p)}</p>" for p in paragraphs[:10]]  # Limit paragraphs
    
    return '\n'.join(html_parts)


def process_sutta(session: requests.Session, href: str) -> Optional[Dict[str, str]]:
    """Process a single sutta page and return structured data."""
    # url = BASE_URL + href
    url = href
    print(f"Processing: {href}")
    
    content = fetch_page_content(session, url)
    if not content:
        return None
    
    soup = BeautifulSoup(content, 'html.parser')
    info = extract_sutta_info(soup)
    content_html = extract_sutta_content(soup)
    
    return {
        'href': href,
        'url': url,
        'title': info['title'],
        'sutta_number': info['sutta_number'],
        'translation_info': info['translation_info'],
        'content_html': content_html
    }


def create_css() -> str:
    """Generate CSS styles for the EPUB."""
    return """
    body {
        font-family: "Times New Roman", serif;
        line-height: 1.6;
        margin: 0;
        padding: 20px;
    }
    
    h1 {
        text-align: center;
        color: #8B4513;
        margin-bottom: 30px;
        font-size: 1.8em;
    }
    
    h2 {
        color: #8B4513;
        margin-top: 30px;
        margin-bottom: 15px;
        font-size: 1.4em;
    }
    
    h3 {
        color: #8B4513;
        margin-top: 25px;
        margin-bottom: 10px;
        font-size: 1.2em;
    }
    
    p {
        margin-bottom: 12px;
        text-align: justify;
    }
    
    p.indent {
        text-indent: 2em;
    }
    
    .translation-info {
        font-size: 0.9em;
        color: #666;
        text-align: right;
        margin-bottom: 20px;
    }
    
    .center {
        text-align: center;
    }
    
    .title-page {
        text-align: center;
        margin-top: 50px;
    }
    
    .title-page h1 {
        font-size: 2.2em;
        margin-bottom: 40px;
    }
    
    .title-page p {
        font-size: 1.2em;
        margin: 20px 0;
    }
    """


def create_cover_page() -> str:
    """Create HTML for the cover page."""
    return f"""
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>Маджхима Никая</title>
        <link rel="stylesheet" type="text/css" href="style.css"/>
    </head>
    <body>
        <div class="title-page">
            <h1>Маджхима Никая</h1>
            <h2>«Средние проповеди Будды»</h2>
            <p>Перевод с английского: SV</p>
            <p>Источник: Majjhima Nikaya by Bodhi &amp; Nyanamoli</p>
            <p>www.theravada.ru</p>
        </div>
    </body>
    </html>
    """


def create_sutta_html(sutta_data: Dict[str, str]) -> str:
    """Create HTML for a single sutta chapter."""
    return f"""
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>{html.escape(sutta_data['title'])}</title>
        <link rel="stylesheet" type="text/css" href="style.css"/>
    </head>
    <body>
        <h1>{html.escape(sutta_data['title'])}</h1>
        {f'<h2>{html.escape(sutta_data["sutta_number"])}</h2>' if sutta_data['sutta_number'] else ''}
        {f'<div class="translation-info"><p>{html.escape(sutta_data["translation_info"])}</p></div>' if sutta_data['translation_info'] else ''}
        <div class="content">
            {sutta_data['content_html']}
        </div>
    </body>
    </html>
    """


def create_epub_book(title: str, author: str, suttas_data: List[Dict[str, str]]) -> epub.EpubBook:
    """Create and configure EPUB book with all content."""
    # Create book
    book = epub.EpubBook()
    
    # Set metadata
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(title)
    book.set_language('ru')
    book.add_author(author)
    book.add_metadata('DC', 'description', 'Сборник средних проповедей Будды на русском языке')
    
    # Add CSS
    nav_css = epub.EpubItem(
        uid="nav_css",
        file_name="style/nav.css",
        media_type="text/css",
        content=create_css()
    )
    book.add_item(nav_css)
    
    style_css = epub.EpubItem(
        uid="style_css",
        file_name="style/style.css",
        media_type="text/css",
        content=create_css()
    )
    book.add_item(style_css)
    
    # Create cover page
    cover_html = create_cover_page()
    cover_chapter = epub.EpubHtml(
        title='Титульная страница',
        file_name='cover.xhtml',
        lang='ru'
    )
    cover_chapter.content = cover_html
    cover_chapter.add_item(style_css)
    book.add_item(cover_chapter)
    
    # Create sutta chapters
    chapters = [cover_chapter]
    toc_entries = []
    
    for i, sutta in enumerate(suttas_data):
        if not sutta:  # Skip failed downloads
            continue
            
        chapter_html = create_sutta_html(sutta)
        
        # Create safe filename
        safe_title = re.sub(r'[^\w\s-]', '', sutta['title']).strip()
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        filename = f"chapter_{i+1:03d}_{safe_title[:30]}.xhtml"
        
        chapter = epub.EpubHtml(
            title=sutta['title'],
            file_name=filename,
            lang='ru'
        )
        chapter.content = chapter_html
        chapter.add_item(style_css)
        
        book.add_item(chapter)
        chapters.append(chapter)
        toc_entries.append(chapter)
    
    # Define Table of Contents
    book.toc = toc_entries
    
    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Define CSS style for nav
    book.spine = ['nav'] + chapters
    
    return book


def generate_epub(hrefs: List[str], output_filename: str = "majjhima_nikaya.epub") -> None:
    """Main function to generate EPUB from list of hrefs."""
    print(f"Starting EPUB generation for {len(hrefs)} suttas...")
    
    # Create session
    session = create_session()
    
    # Process all suttas
    process_sutta_with_session = partial(process_sutta, session)
    
    print("Fetching and processing suttas...")
    suttas_data = []
    for i, href in tqdm(enumerate(hrefs), desc='Processing suttas:', ascii=True, colour='green'):
        # print(f"Progress: {i+1}/{len(hrefs)}")
        sutta_data = process_sutta_with_session(href)
        suttas_data.append(sutta_data)
        
        # Optional: Add small delay to be respectful to the server
        time.sleep(0.5)
    
    # Filter out failed downloads
    valid_suttas = [s for s in suttas_data if s is not None]
    print(f"Successfully processed {len(valid_suttas)} out of {len(hrefs)} suttas")
    
    # Create EPUB
    print("Creating EPUB book...")
    book = create_epub_book(
        title="Маджхима Никая: Средние проповеди Будды",
        author="SV (перевод)",
        suttas_data=valid_suttas
    )
    
    # Write EPUB file
    print(f"Writing EPUB to {output_filename}...")
    epub.write_epub(output_filename, book)
    
    print(f"EPUB generation complete! File saved as: {output_filename}")
    print(f"Total chapters: {len(valid_suttas)}")

def sutta_list(nikaya_name):
    suttanta_url = 'https://тхеравада.рф/palicanon/суттанта/'
    nikaya_url = suttanta_url + nikaya_name
    raw_html = os.path.join('Russ_suttas', f'{nikaya_name}')

    # Send a GET request to the URL
    response = requests.get(nikaya_url, headers=headers, stream=True)

    # Check if the request was successful
    if response.status_code == 200:
        # Get the content of the page as a Unicode string

        page_content = response.content.decode('utf-8')
            
        with open(raw_html, 'w', encoding='utf-8') as file:
            file.write(page_content)

        soup = BeautifulSoup(page_content, features='lxml')
        links = soup.find_all('a')
        hrefs = [link.get('href') for link in links if link.get('href').endswith('sv.htm')]
        return hrefs
    else:
        # logger.info(f"Failed to retrieve the page. Status code: {response.status_code}")
        print(f"Failed to retrieve the page. Status code: {response.status_code}")

# Example usage
if __name__ == "__main__":
    nikaya_name = 'мадджхима-hикая'
    sutta_links  = sutta_list(nikaya_name)

    
    
    # Generate EPUB
    generate_epub(sutta_links, "Маджхима Никая.epub")