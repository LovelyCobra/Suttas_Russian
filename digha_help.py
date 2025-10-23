#!/usr/bin/env python3
"""
Helper functions for EPUB generator for Russian sutta translations from theravada.ru
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

def check_url(session, url):
    try:
        # Send a HEAD request to check the URL (lighter than GET)
        response = session.get(url, timeout=10)
        # Check if status code is 200 (OK)
        if response.status_code == 200:
            return True #, "URL exists and is accessible"
        else:
            return False #, f"URL returned status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False #, f"URL does not exist or is inaccessible: {str(e)}"
    

# Fetching the list of links to sutta subpages
def list_maker(url):
    session = create_session()
    page_cont = fetch_page_content(session, url)

    soup = BeautifulSoup(page_cont, 'lxml')
    links = soup.find_all('a')
    hrefs = [urljoin(BASE_URL, link.get('href')) for link in links if link.get('href') and link.get('href').endswith('.htm') and re.search(r'dn[0-9]+', link.get('href'))]

    return hrefs

def sublist(hrefs):
    subls = [item for item in hrefs if re.search(r'-01-', item)]
    result = [item.replace('-01-', '-02-') for item in subls]
    add_ls = []
    index = 2
    session = create_session()
    for link in tqdm(result, desc='Finding links:', ascii=True, colour='yellow'):
        next_link = link.replace(f'-0{str(index)}-', f'-0{str(index+1)}-')

        while check_url(session, next_link):
            add_ls.append(next_link)
            index += 1
            next_link = next_link.replace(f'-0{str(index)}-', f'-0{str(index+1)}-')
        index = 2
    result.extend(add_ls)

    return result

def subpage_download(hrefs, skip=True):
    dir = 'Дигха Никая'
    os.makedirs( dir, exist_ok=True)

    for link in tqdm(hrefs, desc="Downloading subpages:", ascii=True, colour='blue'):
        
        parsed_link = urlparse(link)
        link_path = parsed_link.path
        subpage_name = os.path.basename(link_path) + 'l'
        if skip and subpage_name in os.listdir(dir): continue
        resp = requests.get(link, headers=headers, stream=True)
        resp.encoding = 'windows-1251'
        with open(f'{dir}/{subpage_name}', 'w', encoding='utf-8') as f:
            content = resp.text.replace('windows-1251', 'utf-8')
            f.write(content)

    print(f'{col.SEP}Sutta pages succesfully downloaded and saved at {col.GREEN}{dir}.{col.SEP}')

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

    return html_parts

def html_list(dir):
    htmls = os.listdir(dir)
    htmls.sort(key=lambda x: float(re.search(r'dn.+[.]html$', x).group()[2:-5]))

    return htmls


if __name__ == "__main__":
    no = '6.1'
    url = "https://theravada.ru/Teaching/Canon/Suttanta/digha.htm"
    directory = 'Дигха Никая'

    sutta_html = f'Дигха Никая/dn{no}.html'
    with open(sutta_html, 'r', encoding='utf-8') as f:
        cont = f.read()

    # Removing the nonsencical unclose <p> at the beginning
    pattern = r'<p(?:\s+[^>]*)?>(?!(?:(?!<p|</p>).)*</p>)'
    clean_cont = re.sub(pattern, '', cont, flags=re.DOTALL)

    soup = BeautifulSoup(clean_cont, 'lxml')



    # hrefs = list_maker(url)
    # sublst = sublist(hrefs)

    # subpage_download(sublst)
    # sutta_info = extract_sutta_info(soup)
    
    result = extract_sutta_content(soup)
    # result = html_list(directory)

    print(col.SEP)
    # pprint(sutta_info)
    for item in  result[:10]:
        print(str(item))
    print(col.SEP)