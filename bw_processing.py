from cobraprint import col
import os, re
from tqdm import tqdm
from bs4 import BeautifulSoup
from pathlib import Path

# /home/soceyya/Desktop/BUDDHA'S WORDS
def sv_sutt_process(file_path, printing=True):
    dir = 'Маджхима Никая с ударениями'
    os.makedirs('test', exist_ok=True)

    with open(file_path, 'r', encoding='utf-8') as f:
        cont = f.read()

    soup = BeautifulSoup(cont, 'lxml')
    core_part = soup.find('td', {'style': 'text-align: justify', 'valign': 'top'})
    contents = [item for item in core_part.contents if item != '\n']
    if len(contents) == 1:
        contents[0].unwrap()
        conts = core_part.contents
    else:
        conts = contents
    core_part_cont = [re.sub(r'\s+', ' ', str(item)).strip() for item in conts]
    core_part_cont = [str(item) for item in core_part_cont if item not in ('\n', '')]

    

    beginning = core_part_cont[0:2]
    merg_start = '\n\n'.join(beginning)
    merg_start = re.sub(r'\n[3:]', '\n\n', merg_start)
    to_save = '\n\n'.join(core_part_cont)
    to_save = re.sub(r'\n[3:]', '\n\n', to_save)

    sutt_num = re.search(r'mn[0-9]+', file_path).group()
    file_name = sutt_num + '-russ.txt'
    save_as = 'test/' + file_name
    merg_save_as = 'test/' + sutt_num + '-merger.txt'

    with open(save_as, 'w', encoding='utf-8') as f:
        f.write(to_save)
    with open(merg_save_as, 'w', encoding='utf-8') as f:
        f.write(merg_start)
    
    if printing:
        print(f'{col.SEP}The given html_file has been processed and the core content saved as {col.GREEN}{save_as}{col.END}.{col.SEP}')    
    return to_save, soup

def bw_sut_process(file_path, printing=True):
    os.makedirs('test', exist_ok=True)

    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'lxml')
    all_notes = soup.find_all('span', class_='note')
    all_notes.extend(soup.find_all('span', class_='parno'))
    all_notes.extend(soup.find_all('a', class_='pts_pn'))
    
    for note in all_notes:
        note.decompose()
    for span in soup.find_all('span', class_='add') + [soup.find('span', class_='evam')]:
        span.unwrap()

    paragraphs = soup.find_all('p')
    txt = ''
    for par in paragraphs:
        # Interrupting when it comes to pali section
        a_tag = par.find('a', class_='wp')
        if a_tag: break

        # Remove excessive whitespace
        par = re.sub(r'\s+', ' ', str(par))
        par = par.replace('\\n', '')
        par = par.strip()
        # Adding needed tags
        par = par.replace('<br/> <br/>', '</p>\n\n<p>')
        par = par.replace('<br/>', '</p>\n\n<p>')
        par = par.replace('<p>', '<div class="a"><font color="#996633" face="Arial, Helvetica, sans-serif" size="2"><i>')
        par = par.replace('</p>', '</i></font></div>')
        
        txt += f'{par}\n\n'

    fp = Path(file_path)    
    file_name = fp.stem
    save_as = f'test/{file_name}-eng.txt'
    with open(save_as, 'w', encoding='utf-8') as f:
        f.write(txt)

    if printing:
        print(f'{col.SEP}The given html_file has been processed and its text content saved as {col.GREEN}{save_as}{col.END}.{col.SEP}')

    return txt

def russ_eng_stats(merger_path):
    with open(merger_path, 'r', encoding='utf-8') as f:
        cont = f.read()

    soup = BeautifulSoup(cont, 'lxml')
    core = soup.find('td', {'style': 'text-align: justify', 'valign': 'top'})
    conts = core.contents
    contents = [re.sub(r'\s+', ' ', str(item)).strip() for item in conts if not str(item) == '\n']
    par_num = len(contents)
    eng_par_num = 0
    # Setting counters
    russ_len = 1
    eng_len = 0
    pairs_list = []
    triple_dot = False

    for i, p in enumerate(contents[1:]): # Skipping the first, which is usually just one letter
        chunk = BeautifulSoup(p, 'lxml').body
        if '…' in chunk.get_text(): 
            triple_dot = True  # Checking for the presence of abbreviation sign '…' 
        
        # Get next chunk for lookahead
        if i < (par_num - 2):
            next_chunk = BeautifulSoup(contents[i+2], 'lxml').body  # Fixed indexing
        else: 
            next_chunk = None

        # Counting Russian chunk
        if not chunk.find('i') and not chunk.find('b'): # Russian text (no italic, no bold)
            # Clean text: remove tabs, newlines, and normalize whitespace
            clean_text = re.sub(r'\s+', ' ', chunk.get_text()).strip()
            chunk_length = len(clean_text)
            russ_len += chunk_length
            
        elif not chunk.find('b'): # English text (italic but not bold) - skipping Russian subheadings
            eng_par_num += 1
            # Clean text: remove tabs, newlines, and normalize whitespace
            clean_text = re.sub(r'\s+', ' ', chunk.get_text()).strip()
            chunk_length = len(clean_text)
            eng_len += chunk_length
            
            # Only append and reset when transitioning from English to Russian OR at the end
            if (next_chunk and not next_chunk.find('b') and not next_chunk.find('i')) or not next_chunk:
                pairs_list.append([russ_len, eng_len])
                if triple_dot: 
                    pairs_list[-1].append(True)
                russ_len = 1  # Reset to 1 for next Russian section
                eng_len = 0   # Reset English counter
                triple_dot = False

    russ_par_num = par_num - eng_par_num

    print(
        f'''{col.SEP}Number of paragraphs: {col.BLUE}{par_num}{col.END}\n
        ...in Russian: {col.GREEN}{russ_par_num}{col.END}
        ...in English: {col.GREEN}{eng_par_num}{col.END}

        {col.YELLOW}Alternating sections lengths comparison (Russian/English){col.END}:
        
        '''
        )
    for sect in pairs_list:
        rus = sect[0]
        eng = sect[1]
        diff = int(100 * ((rus - eng)/rus))
        if len(sect) == 3: 
            print(f'     {rus}/{eng}/{sect[2]}     {diff}%')
        else: 
            print(f'     {rus}/{eng}     {diff}%')
    print(col.SEP)
    
def merger_finish(html_file_path, mergertxt_fpath):
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_cont = f.read()
        html_cont = html_cont.replace('TEXT-INDENT: 2em', 'TEXT-INDENT: 2em; margin-bottom: 15px;')
    with open(mergertxt_fpath, 'r', encoding='utf-8') as f:
        merged_cont = f.read()

    soup = BeautifulSoup(html_cont, 'lxml')
    replacement_soup = BeautifulSoup(merged_cont, 'lxml')

    core_td = soup.find('td', {'style': 'text-align: justify', 'valign': 'top'})
    core_td.clear()
    core_td.append(replacement_soup)

    save_as = f'MN bilingual/html_merged_final/{re.search(r'mn[0-9]+', mergertxt_fpath).group()}_bilingual.html'
    content = soup.find('html')
    with open(save_as, 'w', encoding='utf-8') as f:
        f.write(str(content))

    print(f'{col.SEP}The files have been merged and the result saved as {col.GREEN}{save_as}!{col.SEP}')

def batch_processing(russ_dir, eng_dir):
    # Listing sutta files and sorting them in the right order
    russ_files = os.listdir(russ_dir)
    russ_files.sort(key=lambda x: int(re.search(r'mn[0-9]+', x).group()[2:]))
    eng_files = [file for file in os.listdir(eng_dir) if re.search(r'mn[0-9]+', file)]
    eng_files.sort(key=lambda x: int(re.search(r'mn[0-9]+', x).group()[2:]))

    for i, file in enumerate(tqdm(russ_files, desc="Batch processing:", ascii=True, colour='yellow')):
        sv_sutt_process(os.path.join(russ_dir, file), False)
        bw_sut_process(os.path.join(eng_dir, eng_files[i]), False)

    print(f'{col.SEP}{col.GREY}The files in the given directories have been processed and the results saved in the {col.RED}Buddha_words{col.GREY} directory!!{col.SEP}')


if __name__ == '__main__':
    no = '63'

    eng = '/home/soceyya/Desktop/BUDDHA\'S WORDS/mn/mn3.html'
    russ = f'Маджхима Никая с ударениями/mn{no}-sv.html'
    output_file_name = f'MN bilingual/html_merged_final/mn{no}_bilingual.html'

    russ_dir = 'Маджхима Никая с ударениями/'
    eng_dir = '/home/soceyya/Desktop/BUDDHA\'S WORDS/mn/'

    merg_txt = f'MN bilingual/merger edited/mn{no}_bilingual.txt'

    merger_finish(russ, merg_txt)

    # batch_processing(russ_dir, eng_dir)
    # russ_fpath = russ_dir + 'mn17-sv.html'
    # sv_sutt_process(russ_fpath)
    # bw_sut_process(file_path)
    
    russ_eng_stats(output_file_name)