import requests
from sutta_list import sutta_list
from bs4 import BeautifulSoup
import chardet, re, html, os
from urllib.parse import urljoin
from typing import List, Dict, Tuple, Optional
from cobraprint import col
from tqdm import tqdm
from ebooklib import epub
from time import time

# Configuration
BASE_URL = "https://theravada.ru/Teaching/Canon/Suttanta/Texts/"
ENCODING = 'utf-8'
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
        # with open("Russ_suttas/theravada.su_table1508.html", 'w', encoding='utf-8') as f:
        #     f.write(content)
        
        # print(f'{col.SEP}Success!! The page fetched and saved!!!{col.SEP}')

        return content
    
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""
    
def page_processing(content):
    soup = BeautifulSoup(content, 'lxml')

    form = soup.find('form')
    text = form.get_text()
    return text

if __name__ == "__main__":
    url = 'https://tipitaka.theravada.su/node/table/1508'

    sutta_ls = sutta_list('theravada.su')
    trans_list = []
    syrkin = 0
    walsh = 0
    for link in tqdm(sutta_ls, desc="Sutta processing:", ascii=True, colour='yellow'):

        session = create_session()
        cont = fetch_page_content(session, link)
        text = page_processing(cont)
        trans_list.append(text)
        if 'Сыркин А.Я., 2020' in text: syrkin += 1
        if 'Морис Уолш' in text: 
            walsh += 1
        else:
            print(f'{col.SEP}{text}')


    print(f'{col.SEP}Walsh translations: {col.GREEN}{walsh}{col.END}')
    print(f'{col.SEP}Syrkin translations: {col.GREEN}{syrkin}{col.SEP}') 