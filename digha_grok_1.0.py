import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from sutta_list import sutta_list
from tqdm import tqdm

def get_form_details(url):
    """
    Fetch the page and extract form details including available columns (checkboxes),
    form_build_id, form_id, and action URL.
    """
    print(f"Fetching URL: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch {url}: HTTP {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form')
    if not form:
        raise ValueError(f"No form found on {url}")
    
    columns = {}
    for inp in form.find_all('input', attrs={'type': 'checkbox', 'name': lambda n: n and n.startswith('col_')}):
        label_elem = inp.find_next_sibling('label')
        if label_elem:
            label = label_elem.text.strip()
            columns[label] = inp['name']
    
    form_build_id_input = form.find('input', attrs={'name': 'form_build_id'})
    if not form_build_id_input:
        raise ValueError(f"No input with name 'form_build_id' found on {url}")
    form_build_id = form_build_id_input['value']
    
    form_id_input = form.find('input', attrs={'name': 'form_id'})
    if not form_id_input:
        raise ValueError(f"No input with name 'form_id' found on {url}")
    form_id = form_id_input['value']
    
    action = 'https://tipitaka.theravada.su' + form['action'] if form['action'].startswith('/') else form['action']
    
    return columns, form_build_id, form_id, action

def fetch_sutta_content(url, russian_label="Сыркин А.Я., 2020 - русский", 
                        pref_eng_label="Морис Уолш - english", 
                        fall_eng_label="Thanissaro bhikkhu - english"):
    """
    Fetch the sutta content by submitting the form with selected columns.
    Extract chapter title and interleaved Russian-English paragraphs.
    """
    try:
        columns, form_build_id, form_id, action = get_form_details(url)
    except ValueError as e:
        print(f"Error in get_form_details for {url}: {e}")
        raise
    
    selected = []
    if russian_label in columns:
        selected.append(columns[russian_label])
    else:
        print(f"Warning: Russian translation '{russian_label}' not available on {url}")
        return None, None  # Skip this sutta
    
    eng_selected = None
    if pref_eng_label in columns:
        selected.append(columns[pref_eng_label])
        eng_selected = pref_eng_label
    elif fall_eng_label in columns:
        selected.append(columns[fall_eng_label])
        eng_selected = fall_eng_label
    
    post_data = {col: 'on' for col in selected}
    post_data['form_build_id'] = form_build_id
    post_data['form_id'] = form_id
    post_data['op'] = 'Обновить'
    
    response = requests.post(action, data=post_data)
    if response.status_code != 200:
        print(f"Warning: Failed to post form for {url}: HTTP {response.status_code}")
        return None, None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract chapter title
    chapter_p = soup.find('p', class_='chapter')
    if not chapter_p:
        print(f"Warning: No chapter title found on {url}")
        return None, None
    full_title = chapter_p.text.strip()
    
    # Parse table content
    table = soup.find('table', class_='table table-striped')
    if not table:
        print(f"Warning: No content table found on {url}")
        return None, None
    
    content_html = ''
    tbody = table.find('tbody')
    if tbody:
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            if not tds:
                continue
            
            # Handle potential subheadings (colspan)
            if len(tds) == 1 and tds[0].has_attr('colspan'):
                content_html += f'<h2>{tds[0].text.strip()}</h2>'
            else:
                # Assume first td is Russian, second (if exists) is English
                rus_text = tds[0].text.strip() if len(tds) > 0 else ''
                eng_text = tds[1].text.strip() if len(tds) > 1 else ''
                
                if rus_text:
                    content_html += f'<p>{rus_text}</p>'
                if eng_text:
                    content_html += f'<p>{eng_text}</p>'
    
    return full_title, content_html

def extract_toc_entry(full_title):
    """
    Extract TOC entry from full title, e.g., "ДН 1 Наставление о величайшей сети" -> "1. Наставление о величайшей сети"
    """
    try:
        parts = full_title.split(' ', 2)
        if len(parts) < 3 or not parts[0].startswith('ДН') or not parts[1].isdigit():
            raise ValueError(f"Invalid title format: {full_title}")
        number = parts[1]
        name = parts[2]
        return f"{number}. {name}"
    except ValueError as e:
        print(f"Error in TOC entry extraction: {e}")
        return full_title  # Fallback to full title

def create_epub(sutta_links, cover_path="Russ_suttas/Digha_cover.jpg", output_path="digha_nikaya.epub"):
    """
    Main function to create the EPUB ebook.
    """
    book = epub.EpubBook()
    book.set_identifier('digha-nikaya')
    book.set_title('Дигха Никая')
    book.set_language('ru')
    book.add_author('Buddha')
    
    # Add cover
    try:
        with open(cover_path, 'rb') as f:
            book.set_cover('cover.jpg', f.read())
    except FileNotFoundError:
        print(f"Warning: Cover image {cover_path} not found. Skipping cover.")
    
    # Title page
    title_page = epub.EpubHtml(title='Title Page', file_name='title.xhtml', lang='ru')
    title_page.content = (
        '<div style="text-align: center;">'
        '<h1>Дигха Никая:</h1>'
        '<h2>«Средние проповеди Будды»</h2>'
        '<p>Русский перевод: А.Я.Сыркин</p>'
        '<p>English translation: Maurice Walshe & Thanissaro Bhikkhu</p>'
        '<p>www.tipitaka.theravada.su</p>'
        '</div>'
    )
    book.add_item(title_page)
    
    # Fetch all suttas and collect chapters and TOC entries
    chapters = []
    toc_entries = []
    for i, link in enumerate(tqdm(sutta_links, desc="Processing chapters:", ascii=True, colour='green'), start=1):
        try:
            full_title, content_html = fetch_sutta_content(link)
            if full_title is None or content_html is None:
                print(f"Skipping sutta {link} due to fetch errors")
                continue
            
            toc_entry = extract_toc_entry(full_title)
            toc_entries.append(toc_entry)
            
            ch = epub.EpubHtml(title=full_title, file_name=f'chap_{i}.xhtml', lang='ru')
            ch.content = f'<h1>{full_title}</h1>{content_html}'
            book.add_item(ch)
            chapters.append(ch)
        except Exception as e:
            print(f"Error processing {link}: {e}")
            continue
    
    if not chapters:
        raise ValueError("No chapters were successfully processed. EPUB creation aborted.")
    
    # Build TOC with grouping
    book.toc = [
        epub.Section('I. О нравственности (DH 1-13)', [
            epub.Link(f'chap_{j}.xhtml', toc_entries[j-1], f'chap_{j}') for j in range(1, min(14, len(chapters)+1))
        ]),
        epub.Section('II. Большой раздел (DH 14-23)', [
            epub.Link(f'chap_{j}.xhtml', toc_entries[j-1], f'chap_{j}') for j in range(14, min(24, len(chapters)+1))
        ]),
        epub.Section('III. Сутты Патики (DH 24-34)', [
            epub.Link(f'chap_{j}.xhtml', toc_entries[j-1], f'chap_{j}') for j in range(24, len(chapters)+1)
        ])
    ]
    
    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Spine
    book.spine = ['cover', title_page, 'nav'] + chapters
    
    # Write the EPUB file
    try:
        epub.write_epub(output_path, book, {})
        print(f"EPUB created successfully at {output_path}")
    except Exception as e:
        print(f"Error writing EPUB: {e}")



if __name__ == "__main__":
    sutta_ls = sutta_list('theravada.su')
    create_epub(sutta_ls)