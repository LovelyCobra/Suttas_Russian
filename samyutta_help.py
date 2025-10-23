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
from digha_main_grok_3 import extract_sutta_content, sutta_title_html

# Configuration
BASE_URL = "https://theravada.ru/Teaching/Canon/Suttanta/"
ENCODING = 'windows-1251'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
    }

samyuttas = {
    '1': 'Дэвата Саньютта – Дэвы',
    '2': 'Дэвапутта Саньютта – Молодые дэвы',
    '3': 'Косала Саньютта - Косалы',
    '4': 'Мара Саньютта - Мара',
    '5': 'Бхиккхуни Саньютта - Монахини',
    '6': 'Брахма Саньютта - Брахмы',
    '7': 'Брахмана Саньютта - Брахманы',
    '8': 'Вангиса Саньютта - Вангиса',
    '9': 'Вана Саньютта - Лес',
    '10': 'Яккха Саньютта - Яккхи',
    '11': 'Сакка Саньютта - Сакка',
    '12': 'Нидана Саньютта - Причинность',
    '13': 'Абхисамая Саньютта - Постижение',
    '14': 'Дхату Саньютта - Элементы',
    '15': 'Анаматагга Саньютта - Без постижимого начала',
    '16': 'Кассапа Саньютта - Кассапа',
    '17': 'Лабхасаккара Саньютта - Приобретения и похвала',
    '18': 'Рахула Саньютта - Рахула',
    '19': 'Лаккхана Саньютта - Лаккхана',
    '20': 'Опамма Саньютта - Метафоры',
    '21': 'Бхиккху Саньютта - Монахи',
    '22': 'Кхандха Саньютта - Совокупности',
    '23': 'Радха Саньютта - Радха',
    '24': 'Диттхи Саньютта - Воззрения',
    '25': 'Окканти Саньютта - Вступление',
    '26': 'Уппада Саньютта - Возникновение',
    '27': 'Килеса Саньютта - Загрязнения',
    '28': 'Сарипутта Саньютта - Сарипутта',
    '29': 'Нага Саньютта - Наги',
    '30': 'Супанна Саньютта - Супанны',
    '31': 'Гандхабба Саньютта - Гандхаббы',
    '32': 'Валахака Саньютта - Дэвы облаков',
    '33': 'Ваччхаготта Саньютта - Ваччхаготта',
    '34': 'Самадхи Саньютта - Сосредоточение',
    '35': 'Салаятана Саньютта - Шесть сфер',
    '36': 'Ведана Саньютта - Чувство',
    '37': 'Матугама Саньютта - Женщины',
    '38': 'Джамбукхадака Саньютта - Джамбукхадака',
    '39': 'Самандака Саньютта - Самандака',
    '40': 'Моггаллана Саньютта - Моггаллана',
    '41': 'Читта Саньютта - Домохозяин Читта',
    '42': 'Гамани Саньютта - Начальник',
    '43': 'Асанкхата Саньютта - Необусловленное',
    '44': 'Абьяката Саньютта - Необъявленное',
    '45': 'Магга Саньютта - Путь',
    '46': 'Бодджханга Саньютта - Факторы просветления',
    '47': 'Сатипаттхана Саньютта - Основы осознанности',
    '48': 'Индрия Саньютта - Качества',
    '49': 'Саммаппадхана Саньютта - Правильные старания',
    '50': 'Бала Саньютта - Силы',
    '51': 'Иддхипада Саньютта - Основы сверхъестественных сил',
    '52': 'Ануруддха Саньютта - Ануруддха',
    '53': 'Джхана Саньютта - Джханы',
    '54': 'Анапана Саньютта - Дыхание',
    '55': 'Сотапатти Саньютта - Вступление в поток',
    '56': 'Сачча Саньютта - Истины',
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
    hrefs = [urljoin(BASE_URL, link.get('href')) for link in links if link.get('href') and link.get('href').endswith('.htm') and re.search(r'(samyutta-|an)[0-9]+', link.get('href'))]
    result = [re.sub(r'/Canon/Texts/', '/Canon/Suttanta/Texts/', item) for item in hrefs]

    return result

def samyutta_list(url):
    sn_list_fname = 'samyutta_grand_list.txt'

    if os.path.isfile(sn_list_fname):

        with open(sn_list_fname, 'r', encoding='utf-8') as f:
            content = f.read()

        samyutta_grand_list = []
        content = content[2:-2].split('], [')
        for substr in content:
            samyutta_grand_list.append(substr[1:-1].split("', '"))

    else:
        hrefs = list_maker(url)
        samyutta_grand_list = []
        for an in tqdm(hrefs, desc="Processing links:", ascii=True, colour='cyan'):
            samyutta_grand_list.append(list_maker(an))

        with open('samyutta_grand_list.txt', 'w', encoding='utf-8') as f:
            f.write(str(samyutta_grand_list))
    
    

    return samyutta_grand_list

def subpage_download(samyutta_grand_list, skip=True):
    dir = 'Саньютта Никая'
    os.makedirs( dir, exist_ok=True)

    for subls in tqdm(samyutta_grand_list, desc="Downloading chapter No.:", ascii=True, colour='blue'):
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

def extract_sutta_info(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract sutta title and metadata from BeautifulSoup object."""
    title_elem = soup.find('font', size='5')
    if not title_elem: title_elem = soup.find('font', size='6')

    title = title_elem.get_text().strip() if title_elem else "Untitled"
    title = title.replace('\n', "")
    title = re.sub(r'АН.*$', '', title)
    if title != "Untitled" and ": " in title:
        title_list = title.split(': ')
        if len(title_list) == 2:
            [pali_title, russ_title] = title_list
            russ_title = re.sub(r'АН\s[0-9]+[.][0-9]+', '', russ_title)
        else:
            [pali_title, russ_title] = [title, title]
    else:
        [pali_title, russ_title] = ['', title + ':']

    sutta_num = ""
    if title_elem and title_elem.find_next('font', size='3'):
        sutta_num = title_elem.find_next('font', size='3').get_text().strip()

    return {
        'pali_title': pali_title,
        'russ_title': russ_title,
        'sutta_number': sutta_num,
    }

def single_sutta_title_html(pali_title, russ_title, sutta_number) -> str:
    if pali_title: colon = ':'
    else: colon = ''
    
    return f"""
    <br>
    <div align="center">
        <font size="3" face="Times New Roman, Times, serif"><i>{pali_title}</i>{colon}<br>
            <font size="4" color="brown">{russ_title}</font>
            <br>
            <font size="3">{sutta_number}</font>
        </font>
    </div>
    <br>
    """

def grouping_maker(dir):
    save_dir = dir + ' grouped'
    os.makedirs(save_dir, exist_ok=True)
    files = os.listdir(dir)
    files.sort(key=lambda x: (int(re.search(r'(?<=sn)[0-9]+(?=_[0-9])', x).group()), int(re.search(r'(?<=[0-9]_)[0-9]+(?=-)', x).group())))

    start_digit = 1
    group_content = []
    new_files = []
    initial_num = ''
    removed_divs = 0
    removed_spans = 0
    removed_fonts = 0

    for i, file in tqdm(enumerate(files), desc="File_processing:", ascii=True, colour="cyan"):
        samyutta_num = re.search(r'(?<=sn)[0-9]+(?=_)', file).group()
        sut_num = re.search(r'(?<=[0-9]_)[0-9]+(|-[0-9]+)(?=-[a-z])', file).group()
        upper_num = re.sub(r'^[0-9]+-', '', sut_num)
        if not initial_num: initial_num = re.sub(r'-[0-9]+$', '', sut_num)
        file_path = os.path.join(dir, file)

        with open(file_path, 'r', encoding='utf-8') as f:
            cont = f.read()
        soup = BeautifulSoup(cont, 'lxml')

        # Removing crazy multiple nested identical tags
        span_tags = soup.find_all('span')
        font_tags = soup.find_all('font')

        for span in span_tags:
            while span and span.span and span.span.span:
                span.unwrap()
                removed_spans += 1
        # for font in font_tags:
        #     while font and font.font and font.font.font:
        #         font.font.font.unwrap()
        #         removed_fonts += 1



        sut_info = extract_sutta_info(soup)
        sut_title = single_sutta_title_html(sut_info['pali_title'], sut_info['russ_title'], sut_info['sutta_number'])
        group_content.append(sut_title)
        sut_td_tags = soup.find_all('td', {'style': 'text-align: justify', 'valign': 'top'})
        if not sut_td_tags: 
            print(file)
            return ""
        else: sut_td_tag = sut_td_tags[-1]

        # Removing superfluous div tags
        all_divs = sut_td_tag.find_all('div')
        for div in all_divs:
            if div.div: 
                div.unwrap()
                removed_divs += 1
            p_tags = div.find_all('p')
            if len(p_tags) > 1:
                div.unwrap
                removed_divs += 1


        sut_cont = sut_td_tag.contents
        # sut_cont = extract_sutta_content(soup)
        for tag in sut_cont:
            group_content.append(str(tag))

        if (int(re.sub(r'^[0-9]+-', '', sut_num)) + 1)%10 == start_digit or file == files[-1] or ('-' in sut_num and '-' not in re.search(r'(?<=[0-9]_)[0-9]+(|-[0-9]+)(?=-[a-z])', files[i+1]).group() and int(upper_num)-int(initial_num) > 9) or re.search(r'(?<=sn)[0-9]+(?=_)', files[i+1]).group() != samyutta_num:
            final_cont = "\n".join(group_content)
            # print(final_cont[:1000])
            save_name = 'sn' + samyutta_num + '_' + initial_num + '-' + re.sub(r'^[0-9]+-', '', sut_num) + '.html'
            new_files.append(save_name)
            save_as = os.path.join(save_dir, save_name)
            sut_td_tag.clear()

            # Setting the title for the whole group:
            title_tag = soup.find('font', size="5")
            suttas_numbers = title_tag.font
            br = title_tag.br
            title_tag.string = samyuttas[samyutta_num]

            # suttas_numbers = title_tag.find_next('font', size='3')
            if suttas_numbers:
                suttas_numbers.string = f"Cутты {initial_num}-{re.sub(r'^[0-9]+-', '', sut_num)}"
                title_tag.append(br)
                title_tag.append(suttas_numbers)
            else:
                print(sut_num, str(title_tag), '\n')

            # The following needs to be corrected:
            sut_td_tag.append(BeautifulSoup(final_cont, 'lxml'))
            with open(save_as, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            initial_num = ''
            group_content = []
            if file != files[-1]:
                next_sut_no = re.search(r'(?<=[0-9]_)[0-9]+(|-[0-9]+)(?=-[a-z])', files[i+1]).group()
                start_digit = (int(re.sub(r'^[0-9]+-', '', next_sut_no)))%10

    print(f"{col.SEP}The files in the given directory has been processed and the resulting aggregated files saved at {col.GREEN}{save_dir}{col.END} directory. Number of removed superfluous: <div> tags: {col.RED}{removed_divs}{col.END}; <span> tags: {col.RED}{removed_spans}{col.END}; <font> tags: {col.RED}{removed_fonts}{col.SEP}")


    return new_files

def corrupted_file_remove(source_dir, result_dir):
    
    source_ls = os.listdir(source_dir)
    result_ls = os.listdir(result_dir)
    suspect_files = []

    for file in tqdm(source_ls, desc="Checking files:", ascii=True, colour='cyan'):
        if file in result_ls:
            with open(os.path.join(source_dir, file), 'r', encoding='utf-8')as f:
                source_str = f.read()
            with open(os.path.join(result_dir, file), 'r', encoding='utf-8')as f:
                result_str = f.read()

            if len(result_str) < len(source_str):
                suspect_files.append(file)
    return suspect_files

def html_unwrapper(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    soup = BeautifulSoup(content, 'lxml')
    span_tags = soup.find_all('span')
    font_tags = soup.find_all('font')
    removed_divs = 0
    removed_spans = 0
    removed_fonts = 0

    for span in span_tags:
        while span and span.span and span.span.span:
            span.unwrap()
            removed_spans += 1
    for font in font_tags:
        while font and font.font and font.font.font:
            font.font.font.unwrap()
            removed_fonts += 1

    all_divs = soup.find_all('div')
    for div in all_divs:
        if div.div: 
            div.unwrap()
            removed_divs += 1
        p_tags = div.find_all('p')
        if len(p_tags) > 1:
            div.unwrap

    directory, filename = os.path.split(filepath)
    new_filename = filename
    save_as = os.path.join(directory, new_filename)

    with open(save_as, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    print(f'{col.SEP}{col.GREY}The given file has been processed. The number of removed tags:\n{col.END}<div>: {col.GREEN}{removed_divs}{col.END}\n<span>: {col.GREEN}{removed_spans}{col.END}\n<font>: {col.GREEN}{removed_fonts}{col.SEP}')

    return removed_divs, removed_fonts, removed_spans

def filelist_print(dir):
    filelist = os.listdir(dir)
    print(f'{col.SEP}{filelist}{col.SEP}')

if __name__ == "__main__":

    url = "https://theravada.ru/Teaching/Canon/Suttanta/samyutta.htm"
    directory = 'Саньютта Никая с ударениями'

    source_dir = 'Саньютта Никая grouped'
    result_dir = 'Саньютта Никая grouped с ударениями'
    filepath = 'Саньютта Никая grouped/an1_187-234.html'

    # html_unwrapper(filepath)

    # suspects = corrupted_file_remove(source_dir, result_dir)

    files = grouping_maker(directory)

    # samls = samyutta_list(url)
    # subpage_download(samls)

    # sutta_html = f'Саньютта Никая/an{no}.html'
    # with open(sutta_html, 'r', encoding='utf-8') as f:
    #     cont = f.read()

    # Removing the nonsencical unclose <p> at the beginning
    # pattern = r'<p(?:\s+[^>]*)?>(?!(?:(?!<p|</p>).)*</p>)'
    # clean_cont = re.sub(pattern, '', cont, flags=re.DOTALL)

    # soup = BeautifulSoup(clean_cont, 'lxml')

    
    # sutta_info = extract_sutta_info(soup)
    
    # result = extract_sutta_content(soup)

    print(col.SEP)
    # pprint(sutta_info)
    for item in files:
        print(item)
    print(col.SEP)

    # fork = input(f'Should the above listed files be removed? [Y/N]\n').upper()
    # if fork == 'Y':
    #     for file in suspects:
    #         os.remove(os.path.join(result_dir, file))