import requests
from bs4 import BeautifulSoup
import re, os
from urllib.parse import urljoin
from cobraprint import col
from tqdm import tqdm

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
    }

# Configuration
BASE_URL = "https://theravada.ru/Teaching/Canon/Suttanta/Texts/"
ENCODING = 'utf-8'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'


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
        # print(f"Error fetching {url}: {e}")
        return None

def sutta_list(nikaya_name: str):
    suttanta_url = 'https://тхеравада.рф/palicanon/суттанта/'
    if nikaya_name == 'theravada.su':
        nikaya_url = "https://tipitaka.theravada.su/toc/translations/1098"
    elif nikaya_name == "digha":
        nikaya_url = "https://www.theravada.ru/Teaching/Canon/Suttanta/digha.htm"

    else:
        nikaya_url = suttanta_url + nikaya_name
    raw_html = os.path.join('Russ_suttas', f'{nikaya_name}.html')

    # Send a GET request to the URL
    response = requests.get(nikaya_url, headers=headers, stream=True)
    if nikaya_name == 'digha':
        response.encoding = 'windows-1251'

    # Check if the request was successful
    if response.status_code == 200:
        # Get the content of the page as a Unicode string

        page_content = response.text
            
        # with open(raw_html, 'w', encoding='utf-8') as file:
        #     file.write(page_content)

        soup = BeautifulSoup(page_content, features='lxml')
        links = soup.find_all('a')

        if nikaya_name == 'мадджхима-hикая':
            hrefs = [link.get('href') for link in links if re.search(r'mn\d+', link.get('href')) and not re.search(r'dhamma.ru', link.get('href'))]
            final_links = [hrefs[0]]

            i = 0
            for link in hrefs[1:]:
                i += 1
                sutta_no = re.search(r'mn[0-9]+', link).group()[2:]
                if sutta_no in hrefs[i-1]:
                    continue
                final_links.append(link)
            # Supplying a misleading link manually
            final_links.insert(139, "https://theravada.ru/Teaching/Canon/Suttanta/Texts/mn140-dhatuvibhanga-sutta-sv.htm")
            final_links.insert(144, "https://theravada.ru/Teaching/Canon/Suttanta/Texts/mn145-punnovada-sutta-sv.htm")

        elif nikaya_name == 'дигха-hикая':
            final_links = [link.get('href') for link in links if link.get('href') and (re.search(r'dn[0-9]+', link.get('href'), re.IGNORECASE) or "тхеравада.рф/palicanon/суттанта/дигха-hикая" in link.get('href') or "node/translation" in link.get('href'))]

        elif nikaya_name == 'theravada.su':
            pre_links = ["https://tipitaka.theravada.su" + link.get('href') for link in links if link.get('href') and ("node/translation" in link.get('href') or "node/table" in link.get('href'))]
            final_links = [link.replace('translation', 'table') for link in pre_links]

        elif nikaya_name == 'digha':
            pre_links = ['https://www.theravada.ru/Teaching/Canon/Suttanta/' + link.get('href') for link in links if link.get('href') and 'Texts/dn' in link.get('href')]
            final_links = pre_links

        return final_links
    else:
        # logger.info(f"Failed to retrieve the page. Status code: {response.status_code}")
        print(f"Failed to retrieve the page. Status code: {response.status_code}")

def probudnarod_list():
    base_url = 'https://probud.narod.ru/sutra/'
    save_dir = 'probud_narod'
    os.makedirs(save_dir, exist_ok=True)
    sutta_list = []

    def url_loop(nikaya: str, sesion):
        nikaya_url = base_url + nikaya
        partial_list = []
        if nikaya == 'DN':
            limit = 35
        elif nikaya == 'MN':
            limit = 153

        for n in tqdm(range(1, limit), desc='Testing the addresses:', ascii=True, colour='green'):
            current_url = nikaya_url + str(n) + '.html'
            content = fetch_page_content(session, current_url)
            if content:

                if nikaya == 'DN':
                    save_as = re.search('DN[0-9]+[.]html$', current_url).group()
                elif nikaya == 'MN':
                    save_as = re.search('MN[0-9]+[.]html$', current_url).group()
                with open(f'{save_dir}/{save_as}', 'w', encoding='utf-8')as f:
                    f.write(content)
                partial_list.append(current_url)
        return partial_list
    
    session = create_session()
    sutta_list.append(url_loop('DN', session))
    sutta_list.append(url_loop('MN', session))

    return sutta_list




if __name__ == "__main__":
    pro_nar_list = probudnarod_list()
    print(f'\n\nThe website {col.BLUE}probud.narod.ru{col.END} offers these suttas {col.RED}from Dīgha Nikāya:\n')
    for sutta in pro_nar_list[0]:
        print(col.YELLOW + sutta)
    print(f'\n{col.END}And these suttas from {col.RED}Majjhima Nikāya:\n')
    for sutta in pro_nar_list[1]:
        print(col.YELLOW + sutta)
    print(col.SEP)


    # session = create_session()
    # url = 'https://probud.narod.ru/sutra/MN11.html'

    # content = fetch_page_content(session, url)
    # print(content)


    # output_filename = "Маджхима Никая.epub"
    # nikaya_name = 'digha'

    # sutta_links  = sutta_list(nikaya_name)

    # print(f"{col.SEP}")
    # print(f"{col.GREY}Number of links: {col.GREEN}{len(sutta_links)}{col.END}")
    # for link in sutta_links:
    #     print(link)
    # print(f"{col.SEP}")

    # дигха-hикая, мадджхима-hикая, theravada.su, digha, https://www.theravada.ru/Teaching/Canon/Suttanta/Texts/dn1-brahmajala-sutta-01-sirkin.htm
    