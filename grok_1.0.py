import requests, os
from bs4 import BeautifulSoup
import re
from ebooklib import epub
from tqdm import tqdm
from cobraprint import col

# Assume hrefs is your list of URLs, e.g.,
# hrefs = ['https://theravada.ru/Teaching/Canon/Suttanta/Texts/mn1-mulapariyaya-sutta-sv.htm', ...]

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
    }

def clean_content(sub_soup):
    pass


def create_epub(hrefs):
    book = epub.EpubBook()
    book.set_identifier('majjhima-nikaya-ru')
    book.set_title('Маджхима Никая - «Средние проповеди Будды»')
    book.set_language('ru')
    book.add_author('Buddha')

    # Add cover image
    with open('Russ_suttas/Маджхима Никая.png', 'rb') as cover_file:
        cover_content = cover_file.read()
    book.set_cover('cover.png', cover_content)

    # Create title page
    title_chapter = epub.EpubHtml(title='Title Page', file_name='title.xhtml', lang='ru')
    title_chapter.content = (
        '<div style="text-align: center; margin-top: 20%;">'
        '<h2>Маджхима Никая</h2>'
        '<h1>«Средние проповеди Будды»</h1>'
        '<h3>Перевод с английского: SV</h3>'
        '<p><i>источник: Majjhima Nikaya by Bodhi & Nyanamoli</i></p>'
        '<div style="text-align: center; margin-top: 30%;">'
        '<h2>www.theravada.ru</h2>'
        '</div>'
        '</div>'
    )
    book.add_item(title_chapter)

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
                url = hrefs[num - 1]
                resp = requests.get(url, headers=headers, stream=True)
                resp.encoding = 'windows-1251'
                soup = BeautifulSoup(resp.text, 'lxml')

                # Extract main content between the two '◄' links
                back_links = soup.find_all('a', string=re.compile('◄'))
                main_html = ''
                if len(back_links) >= 2:
                    current_elem = back_links[0].next_element
                    while current_elem and current_elem != back_links[1]:
                        main_html += str(current_elem)
                        current_elem = current_elem.next_element
                else:
                    # Fallback to body if navigation links not found
                    main_html = str(soup.body) if soup.body else ''

                sub_soup = BeautifulSoup(main_html, 'lxml')

                # Extract Pali title for TOC (e.g., "Саччавибханга сутта")
                sub_text = re.sub(r'\s+', ' ', sub_soup.get_text())
                title_match = re.search(r'([а-яА-ЯёЁ\- ]+сутта: [а-яА-ЯёЁ\- ]+)', sub_text)
                pali_title = title_match.group(1).split(':')[0].strip() if title_match else f'Сутта {num}'
                toc_title = f"{num}. {pali_title}"

                # Create chapter
                chapter = epub.EpubHtml(title=toc_title, file_name=f'sutta_{num}.xhtml', lang='ru')
                chapter.content = f'<h1>{toc_title}</h1>{str(sub_soup)}'
                book.add_item(chapter)
                chapters.append(chapter)
                sub_toc_entries.append(chapter)

            big_toc_entries.append((epub.Section(sub_name), sub_toc_entries))
            current_num += size

        toc.append((epub.Section(big_name), big_toc_entries))

    # Set TOC and spine
    book.toc = toc
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['cover', title_chapter, 'nav'] + chapters

    # Write the EPUB file
    epub.write_epub('Russ_suttas/majjhima_nikaya_ru.epub', book, {})
    print(f"{col.SEP}{col.RED}The ebook successfuly created!!!{col.SEP}")

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

# Example usage
if __name__ == "__main__":
    nikaya_name = 'мадджхима-hикая'
    sutta_links  = sutta_list(nikaya_name)
    sutta_links.insert(70, "https://theravada.ru/Teaching/Canon/Suttanta/Texts/mn71-tevijja-vacchagotta-sutta.htm")
    sutta_links.insert(72, "https://theravada.ru/Teaching/Canon/Suttanta/Texts/mn73-maha-vacchagotta-sutta.htm")
    sutta_links.insert(73, "https://theravada.ru/Teaching/Canon/Suttanta/Texts/mn74-dighanakha-sutta.htm")

    # print(col.SEP)
    # print(f"Number of the suttas: {col.GREEN}{len(sutta_links)}{col.END}")
    # for i, item in enumerate(sutta_links):
    #     print(item)
    #     if (i+1)%10 == 0:
    #         print()
    
    # print(col.SEP)

    # Call the function with your hrefs list
    create_epub(sutta_links)