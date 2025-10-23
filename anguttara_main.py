#!/usr/bin/env python3
"""
Functional EPUB generator for Russian sutta translations from theravada.ru
Uses functional programming paradigms with pure functions where possible.
"""

import requests
from bs4 import BeautifulSoup
import chardet, re, html, os, os.path
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
from cobraprint import col
from tqdm import tqdm
from ebooklib import epub
from time import time
from pprint import pprint

# Configuration
BASE_URL = "https://theravada.ru/Teaching/Canon/Suttanta/"
ENCODING = 'windows-1251'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

nipatas = {
    '1': 'Екака Нипата: Книга Единиц',
    '2': 'Дука Нипата - Книга Двух',
    '3': 'Тика Нипата: Книга Трёх',
    '4': 'Чатукка Нипата: Книга Четырёх',
    '5': 'Панчака Нипата: Книга Пяти',
    '6': 'Чхакка Нипата: Книга Шести',
    '7': 'Саттака Нипата: Книга Семи',
    '8': 'Аттхака Нипата: Книга Восьми',
    '9': 'Навака Нипата: Книга Девяти',
    '10': 'Дасака Нипата: Книга десяти',
    '11': 'Екадасака Нипата: Книга Одиннадцати'
}

def create_session() -> requests.Session:
    """Create configured requests session."""
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})
    return session

def fetch_page_content(session: requests.Session, url: str) -> str:
    """Fetch and decode page content with proper encoding."""
    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()
        content = response.content.decode(ENCODING)
        return content
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def extract_sutta_info(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract sutta title and metadata from BeautifulSoup object."""
    title_elem = soup.find('font', size='5')
    if not title_elem: title_elem = soup.find('font', size='6')

    title = title_elem.get_text().strip() if title_elem else "Untitled"
    title = title.replace('\n', "")
    if title != "Untitled" and ": " in title:
        title_list = title.split(': ')
        if len(title_list) == 2:
            [pali_title, russ_title] = title_list
            russ_title = re.sub(r'ДН\s[0-9]+', '', russ_title)
        else:
            [pali_title, russ_title] = [title, title]
    else:
        [pali_title, russ_title] = [title, title]

    sutta_num = ""
    if title_elem and title_elem.find_next('font', size='3'):
        sutta_num = title_elem.find_next('font', size='3').get_text().strip()

    return {
        'pali_title': pali_title,
        'russ_title': russ_title,
        'sutta_number': sutta_num,
    }

def clean_text_content(text: str) -> str:
    """Clean and normalize text content."""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def clean_text_for_html(text: str) -> str:
    """Clean text to avoid HTML/XML parsing issues."""
    if not text:
        return ""
    text = text.replace('\x00', '')
    text = text.replace('\ufffd', '')
    text = text.replace('<o:p>', '')
    text = text.replace('</o:p>', '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_sutta_content(soup: BeautifulSoup) -> str:
    """Extract and format sutta content as clean HTML."""
    # Add root URL to hrefs referring to other subpages
    refs = soup.find_all('a')
    for r in refs:
        if r.get('href') and r['href'].endswith('.htm'):
            old_ref = r['href']
            new_ref = f'https://theravada.ru/Teaching/Canon/Suttanta/Texts/{old_ref}'
            r['href'] = new_ref

    # Find the main content table
    all_td_tags = soup.find_all('td', {'style': 'text-align: justify', 'valign': 'top'})
    content_td = all_td_tags[-1] if all_td_tags else None
    if not content_td:
        return "<p>Content not found</p>"

    # Start building clean HTML
    html_parts = []
    td_children = list(content_td.contents)
    if td_children and len(str(td_children[0]).strip()) <= 1:
        td_children.pop(0)

    toc_processed = False
    for kid in td_children:
        # Check for table of contents (font tag with multiple <a> tags)
        if kid.name == 'b' and kid.get_text().strip() == "Содержание:":
            kid.name = 'h3'
            fnt = kid.find('font')
            if fnt:
                fnt['size'] = '4'
            html_parts.append(str(kid))
            continue
        if kid.name == 'font' and kid.find_all('a') and not toc_processed:
            # Create a new font tag to wrap TOC
            font_tag = soup.new_tag('font', size="2", face="Arial, Helvetica, sans-serif", color="#999966")
            for a_tag in kid.find_all(['a', 'br']):
                if a_tag.name == 'br':
                    a_tag.decompose()
                    continue
                link = a_tag.get('href')
                if link:
                    ref_label = re.search(r'#[a-z][0-9]+$', link)
                    if ref_label:
                        a_tag['href'] = ref_label.group()
                text = a_tag.get_text().strip()
                if text:
                    # Detect nesting level based on numbering pattern (e.g., "1", "1.1", "1.1.1")
                    match = re.match(r'(\d+(\.\d+)*)', text)
                    nesting_level = len(match.group(0).split('.')) if match else 1
                    new_div = soup.new_tag('div')
                    if nesting_level == 2:
                        new_div['style'] = 'margin-top: 10px; text-indent: 1em;'
                    elif nesting_level == 3:
                        new_div['style'] = 'margin-bottom: 0px; text-indent: 2em;'
                    else:
                        new_div['style'] = 'margin-top: 10px; text-indent: 0em;'
                    if a_tag.find('b'):
                        a_tag['style'] = 'font-weight: bold; margin-bottom: 10px;'
                    # Wrap a_tag in div and append to font_tag
                    new_div.append(a_tag)
                    font_tag.append(new_div)
                    # font_tag.append(soup.new_tag('br'))
            html_parts.append(str(font_tag))
            toc_processed = True
            continue
        if kid.name == 'b':
            kid.name = 'h3'
            fnt = kid.find('font')
            if fnt:
                fnt['size'] = '4'
            html_parts.append(str(kid))
        elif kid.name == 'font' and not kid.find_all('a'):
            continue  # Skip standalone font tags not part of TOC
        elif kid.name == 'p':
            if 'align' in kid.attrs and kid['align'] == 'center':
                kid.name = 'h3'
                fnt = kid.find('font')
                if fnt:
                    fnt['size'] = '4'
            elif kid.find('i'):
                kid.name = 'h4'
                fnt = kid.find('font')
                if fnt:
                    fnt['size'] = '4'
            else:
                fnt = kid.find('font')
                if fnt and fnt.get('size') in ['4', '5', '6']:
                    kid.name = 'h3'
                    fnt['size'] = '3'
            html_parts.append(str(kid))
        elif kid.name == 'div':
            kid.name = 'p'
            html_parts.append(str(kid))
        elif kid.name != 'br':
            html_parts.append(str(kid))

    # Adding the back notes
    table_cells = soup.find_all('td')
    note_start = note_end = 0
    for i, cell in enumerate(table_cells):
        if cell.get('style') == 'text-align: justify' and cell.get('valign') == 'top':
            note_start = i + 1
        if '<td class="bottom" colspan="4" height="2">' in str(cell):
            note_end = i

    all_notes = table_cells[note_start:note_end]
    for i, note in enumerate(all_notes):
        if i % 3 == 0:
            return_link = note.a['href'] if note.a else ''
            continue
        elif i % 3 == 1:
            note_no = note.get_text()
            continue
        elif i % 3 == 2:
            note.name = 'p'
            if return_link:
                return_tag = soup.new_tag('a')
                return_tag['href'] = return_link
                return_tag['style'] = "color: #996600; font-size: 2; font-family: Times New Roman, Times, serif"
                return_tag.string = note_no
                font_tag = note.find('font', color="#999966")
                if font_tag:
                    first_text = font_tag.find(string=True, recursive=False)
                    if first_text:
                        first_text.insert_before(return_tag)
                        try:
                            return_tag.insert_after(' ')
                        except:
                            pass
            html_parts.append(str(note))

    if not html_parts:
        text_content = content_td.get_text()
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
        html_parts = [f"<p>{html.escape(p)}</p>" for p in paragraphs[:10]]

    return '\n'.join(html_parts)

def create_css() -> str:
    """Generate CSS styles for the EPUB."""
    return """
    body {
        background: #FFFFCC;
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
        margin-top: 15px;
        margin-bottom: 5px;
        font-size: 1.2em;
    }
    
    p {
        margin: 7px;
        text-align: justify;
    }
    
    p.indent {
        text-indent: 1em;
    }
    
    a {
        border: 0px solid #FFFFCC;
        text-decoration: none;
        color: #8B4513
    }

    .a {
        TEXT-INDENT: 1em
    }
    
    .center {
        text-align: center;
    }
    """

def sutta_title_html(pali_title, russ_title, sutta_number) -> str:
    return f"""
    <table width="100%" border="0" cellspacing="0" cellpadding="0">
        <tr>
        <td>
            <div align="center">
            <font size="4" face="Times New Roman, Times, serif"><i>{pali_title}</i>:<br>
                <font size="5" color="brown">{russ_title}</font>
                <br>
                <font size="3">{sutta_number}</font>
            </font>
            </div>
        </td>
        </tr>
    </table>
    <br>
    """

def create_epub(output_filename: str = "anguttara_nikaya.epub") -> None:
    directory = 'Ангуттара Никая grouped'
    os.makedirs(directory, exist_ok=True)
    htmls = os.listdir(directory)
    htmls.sort()

    sutta_groups = {}
    for html_file in htmls:
        if html_file.endswith('.html'):
            match = re.match(r'dn(\d+)(\.\d+)?\.html', html_file)
            if match:
                sutta_num = match.group(1)
                if sutta_num not in sutta_groups:
                    sutta_groups[sutta_num] = []
                sutta_groups[sutta_num].append(html_file)

    start_time = time()
    book = epub.EpubBook()
    book.set_identifier('anguttara-nikaya-ru')
    book.set_title('Ангуттара Никая: Номерные проповеди Будды')
    book.set_language('ru')
    book.add_author('Buddha')

    book.add_metadata('DC', 'description', 'Russian translation of Numerical Discourses of the Buddha')
    book.add_metadata('DC', 'publisher', 'theravada.ru')
    book.add_metadata('DC', 'source', 'Anguttara Nikaya of Pali Canon')

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

    with open('Russ_suttas/Anguttara-cover.png', 'rb') as cover_file:
        cover_content = cover_file.read()
    book.set_cover('cover.png', cover_content)

    title_chapter = epub.EpubHtml(title='Title Page', file_name='title.xhtml', lang='ru')
    title_chapter.content = (
        '<div style="text-align: center; margin-top: 15%;">'
        '<h2>Ангуттара Никая</h2>'
        '<h1>Номерные проповеди Будды</h1>'
        # '<p>С УДАРЕНИЯМИ<br>для студентов русскoвo</p>'
        '<h3>Перевод с палийского: SV</h3>'
        '<p><i>источник: Anguttara Nikaya of Pali Canon</i></p>'
        '<div style="text-align: center; margin-top: 47%;">'
        '<h2 style="margin-bottom: 1px">www.theravada.ru</h2>'
        '<div style="margin-top: 10px; font-size: 0.8em">Ebook by:<br>www.github.com/LovelyCobra</div>'
        # '<p><i>The stress marks added with the help of a free online tool at<br><b><u>www.RussianGram.com</u>.<br>Many thanks to its provider, Sergey Slepov.</b></i></p>'
        '</div>'
        '</div>'
    )
    book.add_item(title_chapter)

    chapters = []
    toc = []
    print(col.SEP)
    print(f"Processing Anguttara Nikaya suttas...")

    # This section needs to be adapted to the structure of Anguttara nikaya

    for sutta_num in sorted(sutta_groups.keys(), key=int):
        html_files = sorted(sutta_groups[sutta_num])
        combined_html = []
        first_file = html_files[0]
        # Fix regex for unclosed <p> tags
        pattern = r'<p(?:\s+[^>]*)?>(?!(?:(?!<p|</p>).)*</p>)'
        with open(f'{directory}/{first_file}', 'r', encoding='utf-8') as f:
            content = f.read()
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            soup = BeautifulSoup(content, 'lxml')
        sutta_info = extract_sutta_info(soup)
        pali_title = sutta_info['pali_title']
        russian_title = sutta_info['russ_title']
        sutta_number = sutta_info['sutta_number']
        toc_title = f"{sutta_num}. {pali_title}"

        for html_file in tqdm(html_files, desc=f"Processing sutta {sutta_num}:", ascii=True, colour="green"):
            with open(f'{directory}/{html_file}', 'r', encoding='utf-8') as f:
                content = f.read()
                content = re.sub(pattern, '', content, flags=re.DOTALL)
                soup = BeautifulSoup(content, 'lxml')
            pre_html = extract_sutta_content(soup)
            almost_html = clean_text_content(pre_html)
            main_html = clean_text_for_html(almost_html)
            combined_html.append(main_html)
        full_html = sutta_title_html(pali_title, russian_title, sutta_number) + '\n'.join(combined_html)
        sub_soup = BeautifulSoup(full_html, 'lxml')
        chapter = epub.EpubHtml(title=toc_title, file_name=f'sutta_{sutta_num}.xhtml', lang='ru')
        chapter.content = str(sub_soup)
        chapter.add_item(style_css)
        book.add_item(chapter)
        chapters.append(chapter)
        toc.append(chapter)

# This is the end of the section to be adapted

    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['cover', title_chapter, 'nav'] + chapters
    epub.write_epub(f'Russ_suttas/{output_filename}', book, {})
    end_time = time()
    print(f"{col.SEP}{col.RED}The ebook successfully created!!!\n{col.GREY}The process took {col.GREEN}{int((end_time - start_time)//60)}{col.GREY} minutes and {col.GREEN}{int((end_time - start_time)%60)} {col.GREY}seconds!!{col.SEP}")

if __name__ == "__main__":
    output_filename = 'Ангуттара Никая.epub'
    create_epub(output_filename)

    # Ангуттара Никая с ударениями.epub