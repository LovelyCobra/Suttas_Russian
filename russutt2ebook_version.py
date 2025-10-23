import requests
import os, re, io, logging, shutil, wget
from PIL import Image
from tqdm import tqdm
import mechanicalsoup as ms
from cobraprint import col
from bs4 import BeautifulSoup

str_const = {
    'root_url': 'https://theravada.ru/Teaching/Canon/Suttanta/Texts/',
    'subpages': ['дигха-hикая', 'мадджхима-hикая', 'самьютта-hикая', 'aнгуттаpа-hикая', 'кхуддака-hикая'],
    'page_opening': "<!DOCTYPE html><html xmlns='http://www.w3.org/1999/xhtml' xmlns:epub='http://www.idpf.org/2007/ops' epub:prefix='z3998: http://www.daisy.org/z3998/2012/vocab/structure/#' lang='en' xml:lang='en'><head><title>Title_placeholder</title><link href='style/nav.css' rel='stylesheet' type='text/css'/></head><body>",
    'html_attrs': {'xmlns': 'http://www.w3.org/1999/xhtml', 'xmlns:epub': 'http://www.idpf.org/2007/ops', 'epub:prefix': 'z3998: http://www.daisy.org/z3998/2012/vocab/structure/#', 'lang':'en', 'xml:lang': 'en'},
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
    }

def fetch_sutta(sutta_page):
    sutta_url = str_const['root_url'] + sutta_page
    raw_html = os.path.join('Russ_suttas', f'{sutta_page}l')

    # Send a GET request to the URL
    response = requests.get(sutta_url, headers=headers, stream=True)



    # Check if the request was successful
    if response.status_code == 200:
        # Get the content of the page as a Unicode string

        page_content = response.content.decode('windows-1251')
            
        with open(raw_html, 'w', encoding='utf-8') as file:
            file.write(page_content)
        return page_content
    else:
        # logger.info(f"Failed to retrieve the page. Status code: {response.status_code}")
        print(f"Failed to retrieve the page. Status code: {response.status_code}")

    
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

# def make_chapter(page_content):
#     soup = BeautifulSoup(page_content, features='lxml')

#     print(soup.get_text())

if __name__ == '__main__':
    sutta = 'mn1-mulapariyyaya-sutta-sv.htm'
    nikaya_name = 'мадджхима-hикая'

    # odkazy = sutta_list(nikaya_name)
    # print(col.SEP)
    # for odkaz in odkazy:
    #     print(odkaz)
    # print(col.SEP)

    page_cont = fetch_sutta(sutta)

    # with open(f'Russ_suttas/{sutta}l', 'r', encoding='windows-1251') as f:
    #     page_content = f.read()

    # make_chapter(page_cont)
    


# russutt2ebook/1.0 (https://github.com/LovelyCobra/Russian_sutta_ebook_build) Python-Requests/2.32.3