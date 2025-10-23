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
    hrefs = [urljoin(BASE_URL, link.get('href')) for link in links if link.get('href') and link.get('href').endswith('.htm') and re.search(r'(samyutta-|sn)[0-9]+', link.get('href'))]

    return hrefs

def samyutta_list():
    with open('samyutta_grand_list.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'/Canon/Texts/', '/Canon/Suttanta/Texts/', content)
    
    samyutta_grand_list = []
    content = content[2:-2].split('], [')
    for substr in content:
        samyutta_grand_list.append(substr[1:-1].split("', '"))

    return samyutta_grand_list

def subpage_download(samyutta_grand_list, skip=True):
    dir = 'Саньютта Никая'
    os.makedirs( dir, exist_ok=True)

    for subls in tqdm(samyutta_grand_list, desc="Downloading samyutta No.:", ascii=True, colour='blue'):
        for link in tqdm(subls, desc="Downloading suttas:", ascii=True, colour='green'):
        
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



if __name__ == "__main__":
    no = '6.1'
    url = "https://theravada.ru/Teaching/Canon/Suttanta/samyutta.htm"
    directory = 'Саньютта Никая'

    samls = samyutta_list()
    subpage_download(samls)

    # sutta_html = f'Саньютта Никая/dn{no}.html'
    # with open(sutta_html, 'r', encoding='utf-8') as f:
    #     cont = f.read()

    # Removing the nonsencical unclose <p> at the beginning
    # pattern = r'<p(?:\s+[^>]*)?>(?!(?:(?!<p|</p>).)*</p>)'
    # clean_cont = re.sub(pattern, '', cont, flags=re.DOTALL)

    # soup = BeautifulSoup(clean_cont, 'lxml')

    # hrefs = list_maker(url)
    # samyutta_grand_list = []
    # for sn in tqdm(hrefs, desc="Processing links:", ascii=True, colour='green'):
    #     samyutta_grand_list.append(list_maker(sn))


    # sublst = sublist(hrefs)

    # sutta_info = extract_sutta_info(soup)
    
    # result = extract_sutta_content(soup)
    # result = html_list(directory)

    # print(col.SEP)
    # print(len(content))
    # pprint(sutta_info)
    # for item in  samyutta_grand_list[55]:
    #     print(item)
    # print(col.SEP)