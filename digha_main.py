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

    # Extract sutta number (e.g., "МН 141")
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
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def clean_text_for_html(text: str) -> str:
    """Clean text to avoid HTML/XML parsing issues."""
    if not text:
        return ""
    
    # Remove any problematic characters that might cause parsing issues
    text = text.replace('\x00', '')  # Remove null bytes
    text = text.replace('\ufffd', '')  # Remove replacement characters
    text = text.replace('<o:p>', '')  # Remove replacement characters
    text = text.replace('</o:p>', '')  # Remove replacement characters
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_sutta_content(soup: BeautifulSoup) -> str:
    """Extract and format sutta content as clean HTML."""

    # Adding the root url to all hrefs refering to other subpages
    refs = soup.find_all('a')
    for r in refs:
        if r.get('href') and r['href'].endswith('.htm'):
            old_ref = r['href']
            new_ref = f'https://theravada.ru/Teaching/Canon/Suttanta/Texts/{old_ref}'
            r['href'] = new_ref

    # Find the main content table
    all_td_tags = soup.find_all('td', {'style': 'text-align: justify', 'valign': 'top'})

    content_td = all_td_tags[-1]
    if not content_td:
        return "<p>Content not found</p>"
    
    # Start building clean HTML
    html_parts = []
    td_children = content_td.contents
    initial_tag = td_children[0]
    if len(str(initial_tag)) == 1: td_children.pop(0)

    for kid in tqdm(td_children, desc="Processing the content:", ascii=True, colour='magenta'):
        if kid.name == 'b':
            kid.name = 'h3'
            fnt = kid.font
            fnt['size'] = '4'
        elif kid.name == 'font':
            pass
        elif kid.name == 'p':
            if 'align' in kid.attrs and kid['align'] == 'center':
                kid.name = 'h3'
                fnt = kid.font
                fnt['size'] = '4'
            elif kid.find('i'):
                kid.name = 'h4'
            else:
                kid.name = 'h3'
                fnt = kid.font
                fnt['size'] = '3'
        elif kid.name == 'div':
            kid.name = 'p'
        if kid.name != 'br':
            html_parts.append(str(kid))

    # Adding the back notes
    table_cells = soup.find_all('td')
    # Determining where notes start and end
    for i, cell in enumerate(table_cells):
        if cell.get('style') == 'text-align: justify' and cell.get('valign') == "top":
            note_start = i+1
        if '<td class="bottom" colspan="4" height="2">' in str(cell):
            note_end = i
    
    all_notes = table_cells[note_start:note_end]
    for i, note in enumerate(all_notes):
        if i%3 == 0:
            return_link = note.a['href']
            continue
        elif i%3 == 1:
            note_no = note.get_text()
            continue
        elif i%3 == 2:
            note.name = 'p'
            return_tag = soup.new_tag('a')
            return_tag['href'] = return_link
            return_tag['style'] = "color: #996600; font-size: 2; font-family: Times New Roman, Times, serif"

            return_tag.string = note_no
            font_tag = note.find('font', color="#999966")
            first_text = font_tag.find(string=True, recursive=False)
            if first_text:
                first_text.insert_before(return_tag)
            try:
                return_tag.insert_after(' ')
            except:
                continue
            html_parts.append(str(note))

    # If no structured content found, extract all text
    if not html_parts:
        text_content = content_td.get_text()
        paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
        html_parts = [f"<p>{html.escape(p)}</p>" for p in paragraphs[:10]]  # Limit paragraphs
    

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

def create_epub(output_filename: str = "digha_nikaya.epub") -> None:
    directory = 'Дигха Никая'
    os.makedirs(directory, exist_ok=True)
    htmls = os.listdir(directory)
    htmls.sort(key=lambda x: float(re.search(r'dn.+[.]html$', x).group()[2:-5]))

    start_time = time()
    book = epub.EpubBook()
    book.set_identifier('digha-nikaya-ru')
    book.set_title('Дигха Никая: Длинные проповеди Будды»')
    book.set_language('ru')
    book.add_author('Buddha')

    # Add metadata with ASCII-safe description for better Calibre compatibility
    book.add_metadata('DC', 'description', 'Russian translation of Long Discourses of the Buddha')
    book.add_metadata('DC', 'publisher', 'theravada.ru')
    book.add_metadata('DC', 'source', 'Digha Nikaya of Pali Canon')
    
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

    # Add cover image
    with open('Russ_suttas/Digha-cover.jpg', 'rb') as cover_file:
        cover_content = cover_file.read()
    book.set_cover('cover.png', cover_content)

    # Create title page
    title_chapter = epub.EpubHtml(title='Title Page', file_name='title.xhtml', lang='ru')
    title_chapter.content = (
        '<div style="text-align: center; margin-top: 15%;">'
        '<h2>Дигха Никая</h2>'
        '<h1>Длинные проповеди Будды»</h1>'
        '<p>С УДАРЕНИЯМИ<br>для студентов русскoвo</p>'
        '<h3>Перевод с палийского: SV</h3>'
        '<p><i>источник: Digha Nikaya of Pali Canon</i></p>'
        '<div style="text-align: center; margin-top: 47%;">'
        '<h2 style="margin-bottom: 1px">www.theravada.ru</h2>'
        '<div style="margin-top: 10px; font-size: 0.8em">Ebook by:<br>www.github.com/LovelyCobra</div>'
        '<p><i>The stress marks added with the help of a free online tool at<br><b><u>www.RussianGram.com</u>.<br>Many thanks to its provider, Sergey Slepov.</b></i></p>'
        '</div>'
        '</div>'
    )
    book.add_item(title_chapter)

    # This section needs to be adapted to a different chapter structure

    # Define big sections and subgroup sizes
    big_sections = [
        ("Коренной раздел", 1, 50),
        ("Срединный раздел", 51, 100),
        ("Последний раздел", 101, 152)
    ]
    subgroup_sizes = {
        50: [10] * 5,
        52: [10, 10, 10, 12, 10]
    }

    chapters = []
    toc = []

    print(col.SEP)
    for big_name, start, end in big_sections:

        print(f"\nProcessing the section: {col.RED}{big_name}{col.END}\n")
        num_suttas = end - start + 1
        sizes = subgroup_sizes.get(num_suttas, [10] * (num_suttas // 10))
        big_toc_entries = []
        current_num = start
        for n, size in enumerate(sizes):
            print(f"{col.GREY}Working on subsection: {col.YELLOW}{n+1}{col.END}")
            sub_toc_entries = []
            sub_name = f"Сутты {current_num}-{current_num + size - 1}"
            for num in tqdm(range(current_num, current_num + size), desc="Fetching suttas:", ascii=True, colour="green"):
                if num != 155:
                    url = hrefs[num - 1]
                    subpage_name = re.search('mn.+?htm$', url).group()
                    if f"{subpage_name}l" not in os.listdir(directory):
                        resp = requests.get(url, headers=headers, stream=True)
                        resp.encoding = 'windows-1251'
                        with open(f'{directory}/{subpage_name}l', 'w', encoding='utf-8') as f:
                            f.write(resp.text)
                        soup = BeautifulSoup(resp.text, 'lxml')
                    else:
                        with open(f'{directory}/{subpage_name}l', 'r', encoding='utf-8') as f:
                            cont = f.read()
                        soup = BeautifulSoup(cont, 'lxml')
                else:
                    with open("Russ_suttas/mn140-dhatu-vibhanga-sutta-sv.html", 'r', encoding='utf-8') as f:
                        content = f.read()
                    soup = BeautifulSoup(content, 'lxml')
                    
                pre_html = extract_sutta_content(soup)
                sutta_info = extract_sutta_info(soup)
                pali_title = sutta_info['pali_title']
                russian_title = sutta_info['russ_title']
                sutta_number = sutta_info['sutta_number']
                intermed_html = sutta_title_html(pali_title, russian_title, sutta_number) + pre_html
                almost_html = clean_text_content(intermed_html)
                main_html = clean_text_for_html(almost_html)


                sub_soup = BeautifulSoup(main_html, 'lxml')
                toc_title = f"{num}. {pali_title}"

                # Create chapter
                chapter = epub.EpubHtml(title=toc_title, file_name=f'sutta_{num}.xhtml', lang='ru')
                chapter.content = str(sub_soup)
                chapter.add_item(style_css)
                book.add_item(chapter)
                chapters.append(chapter)
                sub_toc_entries.append(chapter)

            big_toc_entries.append((epub.Section(sub_name), sub_toc_entries))
            current_num += size

        toc.append((epub.Section(big_name), big_toc_entries))

    # This is the end of the section to be adapted 

    # Set TOC and spine
    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['cover', title_chapter, 'nav'] + chapters

    # Write the EPUB file
    epub.write_epub(f'Russ_suttas/{output_filename}', book, {})
    end_time = time()
    print(f"{col.SEP}{col.RED}The ebook successfuly created!!!\n{col.GREY}The process took {col.GREEN}{int((end_time - start_time)//60)}{col.GREY} minutes and {col.GREEN}{int((end_time - start_time)%60)} {col.GREY}seconds!!{col.SEP}")




if __name__ == "__main__":
    output_filename = 'Дигха Никая.epub'
    create_epub(output_filename)

    # no = '6-01'
    # url = "https://theravada.ru/Teaching/Canon/Suttanta/digha.htm"

    # sutta_html = f'Дигха Никая/dn{no}.html'
    # with open(sutta_html, 'r', encoding='utf-8') as f:
    #     cont = f.read()

    # # Removing the nonsencical unclose <p> at the beginning
    # pattern = r'<p(?:\s+[^>]*)?>(?!(?:(?!<p|</p>).)*</p>)'
    # clean_cont = re.sub(pattern, '', cont, flags=re.DOTALL)

    # soup = BeautifulSoup(clean_cont, 'lxml')
    
    # result = extract_sutta_content(soup)

    # print(col.SEP)
    # # pprint(sutta_info)
    # for item in  result[:20]:
    #     print(str(item))
    # print(col.SEP)