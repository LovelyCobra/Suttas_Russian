import asyncio
import platform
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
from cobraprint import col

# Configure logging
logging.basicConfig(
    filename='stress_adder.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def sort(file_path):
    n = float(re.search(r'an[0-9]+[.][0-9]+', file_path.replace('_', '.')).group()[2:])
    return n

def stress_adder(file_path):
    # Preparing the saving dir and file name
    directory, filename = os.path.split(file_path)
    save_dir = directory + ' с ударениями'
    os.makedirs(save_dir, exist_ok=True)
    save_as = os.path.join(save_dir, filename)

    # Read and parse input HTML
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    soup = BeautifulSoup(content, 'lxml')
    td_tags = soup.find_all('td', {'style': 'text-align: justify', 'valign': 'top'})
    if not td_tags:
        logging.error(f"No matching <td> tags found in {file_path}")
        return {'html_content': content, 'saved_as': save_as, 'shorter': False}
    
    td_tag_old = td_tags[-1]
    td_tag_content = td_tag_old.contents
    sections = [str(item) for item in td_tag_content if str(item).strip()]
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
                section_to_upload = "</div>".join((section_to_upload, sections[total_sections - current_sect_number])) if section_to_upload else sections[total_sections - current_sect_number]
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
        for attempt in range(retry_attempts):
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
    if actual_length < expected_length:  # Allow 10% variation for stress marks
        shorter = True
        logging.warning(f"Processed text length ({actual_length}) significantly less than expected ({expected_length})")
        print(f"{col.RED}Warning: Processed text may be incomplete. Expected ~{expected_length} chars, got {actual_length} chars{col.END}")
    else: shorter = False

    # Reconstruct HTML
    try:
        td_tag_old.clear()
        td_tag_old.append(BeautifulSoup(processed_txt_container, 'lxml'))
        page = str(soup.find('html'))
        
        with open(save_as, 'w', encoding='utf-8') as f:
            cont = page.replace('&lt;', '<').replace('&gt;', '>')
            f.write(cont)
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
    file_names.sort(key=lambda x: (int(re.search(r'(?<=an)[0-9]+(?=_[0-9])', x).group()), int(re.search(r'(?<=[0-9]_)[0-9]+(?=-)', x).group())))
    new_dir = dir + ' с ударениями'
    file_path_list = [os.path.join(dir, file_name) for file_name in file_names]
    failed_files = []

    for f in tqdm(file_path_list[180: ], desc='Processing files:', ascii=True, colour='green'):
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
    file_path = 'Ангуттара Никая grouped/an1_394-574.html'
    directory = 'Ангуттара Никая grouped'

    # result = stress_adder(file_path)
    # print(result['shorter'])

    failed_files = batch_stress_adder(directory)
    if failed_files:
        print(f'{col.SEP}The following files may have been truncated:')
        # pprint(sutta_info)
        for item in failed_files:
            print(item)
        print(col.SEP)

        fork = input(f'Should the above listed files be removed? [Y/N]\n').upper()
        if fork == 'Y':
            for file in failed_files:
                os.remove(os.path.join(directory + ' с ударениями', file))
                
    # result = stress_adder(file_path)
    # print(f'\nThe html file {col.RED}{file_path}{col.END} successfully processed\nand saved in a new directory as {col.GREEN}{result['saved_as']}{col.END}.{col.SEP}')
    # # batch_stress_adder(directory)