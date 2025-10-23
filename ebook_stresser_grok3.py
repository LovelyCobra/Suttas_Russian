import ebooklib, os
from ebooklib import epub
from ebooklib.epub import Link, Section
from cobraprint import col
import time
import logging
import re
import os
import shutil
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
from bs4 import BeautifulSoup
import lxml

# Helper function to get the main text content

def ebook_content(filepath):
    book = epub.read_epub(filepath)
    all_items = list(book.get_items())
    extracted_dir = 'bhavana_ebook'
    stressed_dir = extracted_dir + ' с ударениями'
    os.makedirs(extracted_dir, exist_ok=True)

    print(col.SEP)
    html_items = []
    for item in all_items:
        if isinstance(item, epub.EpubHtml) and not isinstance(item, epub.EpubNav):
            content = item.get_content().decode('utf-8')
            fname = item.get_name()
            save_path = os.path.join(extracted_dir, fname)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            html_items.append(item)
            print(f"Extracted HTML: {fname}")
        else:
            print(item)
    print('The content of the e-book has been processed and extracted!')

    # Process the extracted HTML files
    print(col.SEP)
    print(f"{col.GREY}Processing extracted HTML files in {extracted_dir}{col.END}")
    failed_files = batch_stress_adder(extracted_dir)
    if failed_files:
        print(f"{col.RED}Warning: The following files may have been truncated:{col.END}")
        for f in failed_files:
            print(f"  {f}")
        print(col.SEP)

    # Reconstruct the EPUB
    new_book = epub.EpubBook()
    
    # Copy metadata
    for ns, prop_dict in book.metadata.items():
        for prop, val_list in prop_dict.items():
            for val, attrs in val_list:
                new_book.add_metadata(ns, prop, val, attrs)
    
    # Add non-HTML and Nav items unchanged
    for item in all_items:
        if isinstance(item, epub.EpubHtml) and not isinstance(item, epub.EpubNav):
            continue
        new_book.add_item(item)
    
    # Add stressed HTML items
    for orig_item in html_items:
        fname = orig_item.get_name()
        stressed_path = os.path.join(stressed_dir, fname)
        if os.path.exists(stressed_path):
            with open(stressed_path, 'r', encoding='utf-8') as f:
                stressed_content = f.read()
            new_item = epub.EpubHtml(
                title=orig_item.title or '',
                file_name=fname,
                lang=orig_item.lang
            )
            new_item.set_content(stressed_content.encode('utf-8'))
            # Copy any additional attributes if needed
            new_item.id = orig_item.id
            new_book.add_item(new_item)
        else:
            print(f"{col.RED}Warning: Stressed file not found for {fname}, using original.{col.END}")
            new_book.add_item(orig_item)
    
    # Rebuild spine
    new_spine = []
    for sp in book.spine:
        if isinstance(sp, str):
            new_spine.append(sp)
        else:
            item, linear = sp
            if isinstance(item, str):
                new_spine.append((item, linear))
            else:
                iid = item.id
                new_item = new_book.get_item_with_id(iid)
                if new_item is not None:
                    new_spine.append((new_item, linear))
                else:
                    print(f"{col.YELLOW}Warning: No item for spine id {iid}{col.END}")
                    new_spine.append(sp)
    new_book.spine = new_spine
    
    # Rebuild TOC
    def rebuild_toc(original_toc, new_book):
        if not original_toc:
            return original_toc
        if isinstance(original_toc, (list, tuple)):
            new_toc = type(original_toc)([])
            for elem in original_toc:
                if isinstance(elem, Link):
                    new_toc.append(elem)
                elif isinstance(elem, (epub.EpubHtml, epub.EpubItem)):
                    iid = elem.id
                    new_item = new_book.get_item_with_id(iid)
                    if new_item:
                        new_toc.append(new_item)
                    else:
                        new_toc.append(elem)
                elif isinstance(elem, tuple) and len(elem) == 2:
                    if isinstance(elem[0], Section):
                        section = elem[0]
                        sub = elem[1]
                        new_sub = rebuild_toc(sub, new_book)
                        new_toc.append((section, new_sub))
                    else:
                        new_toc.append(rebuild_toc(elem, new_book))
                else:
                    new_toc.append(elem)
            return new_toc
        return original_toc
    
    new_book.toc = rebuild_toc(book.toc, new_book)
    
    # Set cover if exists
    cover_item = book.get_item_with_id('cover-image')
    if cover_item:
        new_book.set_cover(cover_item.get_name(), cover_item.get_content())
    
    # Write the new EPUB
    output_path = 'Bhavana_The_Art_of_The_Mind_ru_stressed.epub'
    epub.write_epub(output_path, new_book, {})
    
    print(f'{col.GREEN}Stressed EPUB saved as: {output_path}{col.END}')
    print(col.SEP)
    
    # Cleanup extracted dirs if desired (optional)
    # shutil.rmtree(extracted_dir)
    # shutil.rmtree(stressed_dir)
    
    return output_path


def stress_adder(file_path):
    # Preparing the saving dir and file name
    directory, filename = os.path.split(file_path)
    save_dir = directory + ' с ударениями'
    os.makedirs(save_dir, exist_ok=True)
    save_as = os.path.join(save_dir, filename)

    # Read and parse input HTML
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    soup = BeautifulSoup(content, 'html.parser')
    # soup = BeautifulSoup(content, features='xml')
    main_content = soup.body
    if not main_content:
        logging.error(f"No matching <td> tags found in {file_path}")
        return {'html_content': content, 'saved_as': save_as, 'shorter': False}
    
    
    body_content = main_content.contents
    sections = [str(item).replace('\xad', '') for item in body_content if str(item) != '\n']
    total_sections = len(sections)
    current_sect_number = total_sections
    processed_txt_container = ""
    failed_sections = []

    logging.info(f"Processing file: {file_path}, Total sections: {total_sections}")
    print(f"{col.SEP}{col.GREY}The processed file: {col.GREEN}{file_path}\n")
    print(f"{col.GREY}Total paragraphs to be annotated: {col.RED}{total_sections}{col.SEP}")

    # Check if annotated file already exists
    if os.path.exists(save_as):
        with open(save_as, 'r', encoding='utf-8') as f:
            page = f.read()
        logging.info(f"Using existing annotated file: {save_as}")
        return {'html_content': page, 'saved_as': save_as, 'shorter': False}

    # Process sections in batches
    section_to_upload = ""
    max_chars = 7700
    retry_attempts = 3
    retry_delay = 5

    while current_sect_number > 0 or section_to_upload:
        driver = None
        try:
            # Initialize browser
            options = Options()
            options.add_argument("--disable-blink-features=AutomationControlled")
            driver = webdriver.Chrome(options=options)

            # Concatenate sections up to max_chars
            while len(section_to_upload) < max_chars and current_sect_number > 0:
                if len(section_to_upload) + len(sections[total_sections - current_sect_number]) > 9900: break
                section_to_upload = "\n\n".join((section_to_upload, sections[total_sections - current_sect_number])) if section_to_upload else sections[total_sections - current_sect_number]
                current_sect_number -= 1
            print(f"\n{col.GREY}Number of unprocessed sections: {col.BLUE}{current_sect_number}{col.END}")

            if not section_to_upload:
                break

            logging.info(f"Processing section batch, length: {len(section_to_upload)}")

            # Try annotating the section
            for attempt in range(retry_attempts):
                try:
                    # Navigate to website
                    driver.get("https://russiangram.com/")
                    input_field = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.ID, "MainContent_UserSentenceTextbox"))
                    )

                    # Set input value
                    driver.execute_script(
                        "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));",
                        input_field,
                        section_to_upload
                    )
                    time.sleep(2)  # Add delay to ensure input is processed

                    # Click annotate button
                    annotate_button = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.ID, "MainContent_SubmitButton"))
                    )
                    driver.execute_script("arguments[0].click();", annotate_button)

                    # Store original URL
                    original_url = driver.current_url
                    annotated_text = WebDriverWait(driver, 30, poll_frequency=0.5).until(
                        lambda d: d.execute_script('return document.getElementById("MainContent_UserSentenceTextbox").value')
                        if d.execute_script('return document.getElementById("MainContent_UserSentenceTextbox").value') != section_to_upload
                        else False
                    )

                    if driver.current_url != original_url:
                        print(f"{col.RED}Redirect detected to {driver.current_url}. Attempting to recover...{col.END}")
                        logging.warning(f"Redirect detected to {driver.current_url}")
                        # Try fallback parsing
                        soup_sub = BeautifulSoup(driver.page_source, 'lxml')
                        containers = [
                            soup_sub.find('textarea', {'id': 'MainContent_UserSentenceTextbox'}),
                            soup_sub.find('div', {'class': 'lesson-content'}),
                            soup_sub.find('div', {'id': 'annotated-text'}),
                            soup_sub.find('p', {'class': 'result-text'})
                        ]
                        for container in containers:
                            if container and (container.get('value') or container.get_text()):
                                annotated_text = container.get('value') or container.get_text()
                                break
                        else:
                            print(f"{col.RED}No annotated text found on {driver.current_url}. Retrying...{col.END}")
                            logging.error(f"No annotated text found on {driver.current_url}")
                            time.sleep(retry_delay)
                            continue

                    processed_txt_container += annotated_text
                    logging.info(f"Successfully annotated section, length: {len(annotated_text)}")
                    break  # Success, exit retry loop

                except (TimeoutException, StaleElementReferenceException) as e:
                    print(f"{col.RED}Attempt {attempt + 1} failed: {str(e)}{col.END}")
                    logging.error(f"Attempt {attempt + 1} failed for section: {section_to_upload[:100]}... Error: {str(e)}")
                    if attempt < retry_attempts - 1:
                        time.sleep(retry_delay)
                        driver.get("https://russiangram.com/")
                    else:
                        print(f"{col.RED}All retries failed for section. Adding to failed sections.{col.END}")
                        logging.error(f"All retries failed for section: {section_to_upload[:100]}...")
                        failed_sections.append(section_to_upload)
                        break

            section_to_upload = ""
            print(f"Length of processed text: {col.GREEN}{len(processed_txt_container)} characters{col.END}")

        except Exception as e:
            print(f"{col.SEP}Annotation of {col.RED}{file_path}{col.END} failed. Error: {str(e)}")
            logging.error(f"Unexpected error processing {file_path}: {str(e)}")
            failed_sections.append(section_to_upload)
            section_to_upload = ""
        finally:
            if driver:
                driver.quit()

    # Retry failed sections
    for section in failed_sections:
        logging.info(f"Retrying failed section: {section[:100]}...")
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        for attempt in range(retry_attempts):
            driver = None
            try:
                driver = webdriver.Chrome(options=options)
                driver.get("https://russiangram.com/")
                input_field = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.ID, "MainContent_UserSentenceTextbox"))
                )
                driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input'));",
                    input_field,
                    section
                )
                time.sleep(2)
                annotate_button = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.ID, "MainContent_SubmitButton"))
                )
                driver.execute_script("arguments[0].click();", annotate_button)
                annotated_text = WebDriverWait(driver, 30, poll_frequency=0.5).until(
                    lambda d: d.execute_script('return document.getElementById("MainContent_UserSentenceTextbox").value')
                    if d.execute_script('return document.getElementById("MainContent_UserSentenceTextbox").value') != section
                    else False
                )
                processed_txt_container += annotated_text
                logging.info(f"Successfully retried section, length: {len(annotated_text)}")
                break
            except Exception as e:
                print(f"{col.RED}Retry attempt {attempt + 1} failed for section: {str(e)}{col.END}")
                logging.error(f"Retry attempt {attempt + 1} failed for section: {section[:100]}... Error: {str(e)}")
                time.sleep(retry_delay)
            finally:
                if driver:
                    driver.quit()

    # Verify all sections processed
    expected_length = sum(len(s) for s in sections)
    actual_length = len(processed_txt_container)
    if actual_length < expected_length:  
        shorter = True
        logging.warning(f"Processed text length ({actual_length}) significantly less than expected ({expected_length})")
        print(f"{col.RED}Warning: Processed text may be incomplete. Expected ~{expected_length} chars, got {actual_length} chars{col.END}")
    else: shorter = False

    # Reconstruct HTML
    try:
        processed_bs = BeautifulSoup(re.sub(r'l. [0-9]+', '', processed_txt_container), 'html.parser')
        main_content.clear()
        if processed_bs.body:
            main_content.extend(processed_bs.body.contents)
        else:
            main_content.append(processed_bs)
        page = str(soup.find('html'))
        
        with open(save_as, 'w', encoding='utf-8') as f:
            # cont = page.replace('&lt;', '<').replace('&gt;', '>')
            f.write(page)

    except Exception as e:
        print(f"{col.RED}Failed to write output file: {str(e)}. Copying original file.{col.END}")
        logging.error(f"Failed to write output file {save_as}: {str(e)}")
        shutil.copy(file_path, save_as)
        page = content

    return {
        'html_content': page,
        'saved_as': save_as,
        'shorter': shorter
    }

def batch_stress_adder(dir):
    start = time.time()
    file_names = os.listdir(dir)
    # file_names.sort(key=lambda x: (int(re.search(r'(?<=an)[0-9]+(?=_[0-9])', x).group()), int(re.search(r'(?<=[0-9]_)[0-9]+(?=-)', x).group())))
    new_dir = dir + ' с ударениями'
    file_path_list = [os.path.join(dir, file_name) for file_name in file_names]
    failed_files = []

    for f in tqdm(file_path_list, desc='Processing files:', ascii=True, colour='green'):
        reslt = stress_adder(f)
        if reslt['shorter']: failed_files.append(f)

    end = time.time()
    duration = end - start
    secs = int(duration % 60)
    mins = duration // 60
    hours = int(mins // 60)
    mins = int(mins % 60)

    print(f'\nThe html files in the given directory {col.RED}{dir}{col.END} successfully processed\nand saved in a new directory {col.GREEN}{new_dir}{col.END}.\n\nThe processing took {col.BLUE}{hours}:{mins}:{secs}{col.END}[hours:min:sec].{col.SEP}')
    logging.info(f"Batch processing completed for {dir}. Duration: {hours}:{mins}:{secs}")

    return failed_files

if __name__ == '__main__':
    bookpath = 'Bhavana_The_Art_of_The_Mind_ru.epub'

    output_path = ebook_content(bookpath)
    print(f"Final output: {output_path}")