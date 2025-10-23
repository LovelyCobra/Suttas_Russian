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


def subpage_download(url, save_dir, skip=True):
    os.makedirs( save_dir, exist_ok=True)
        
    parsed_link = urlparse(url)
    link_path = parsed_link.path
    subpage_name = os.path.basename(link_path)
    if not subpage_name.endswith('.html'): subpage_name += '.html'
    if skip and subpage_name in os.listdir(save_dir):
        print(f'{col.SEP}The page has already been dowloaded earlier') 
        return ""
    resp = requests.get(url, headers=headers, stream=True)
    resp.encoding = 'utf-8'
    with open(f'{save_dir}/{subpage_name}', 'w', encoding='utf-8') as f:
        content = resp.text.replace('windows-1251', 'utf-8')
        f.write(content)

    print(f'{col.SEP}The requested page succesfully downloaded and saved at {col.GREEN}{save_dir}.{col.SEP}')

def html_edit(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    soup = BeautifulSoup(content, 'lxml')
    eng_pars = soup.find_all('font', color="brown")
    br_tags = soup.find_all('br')

    for par in eng_pars:
        text = par.string 
        if text: 
            text.wrap(soup.new_tag('i'))
        else: continue

    for br in br_tags:
        br.decompose()

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    print(f'{col.SEP}The requested page succesfully edited and saved as {col.GREEN}{filepath}.{col.SEP}')

if __name__ == "__main__":
    save_dir = 'Top_sutta_pages'
    url = "https://probud.narod.ru/sutra/DN15.html"
    filepath = 'Top_sutta_pages/DN15.html'

    # subpage_download(url, save_dir, False)
    html_edit(filepath)