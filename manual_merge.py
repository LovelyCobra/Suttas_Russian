import re, os
from parallel_print import parallel_print
from cobraprint import *
from bw_processing import *
from bs4 import BeautifulSoup

# Minor helper functions

def get_sections(text):
    # Find all font or div sections
    sections = re.findall(r'<(?:font|div class="a")[^>]*>.*?</(?:font|div)>', text, re.DOTALL)
    return sections

def get_pure_text(section):
    sect_soup = BeautifulSoup(section, 'lxml')
    text_gen = sect_soup.stripped_strings
    text_ls = [repr(part) for part in text_gen]
    text = ' '.join(text_ls)

    # # Remove HTML tags
    # text = re.sub(r'<[^>]*>', '', section)
    # # Remove all whitespace
    # text = re.sub(r'\s[2:]', '', text)
    # text = text.strip()
    return text

# Manual part for the "merge_main.py"

def add_manually(russ_to_add, eng_to_add, r_sections, e_sections):
    edit_record = []
    outdict = {}

    while r_sections and e_sections:
        parallel_print(get_pure_text(russ_to_add), get_pure_text(eng_to_add))

        fork = input(f'Add Russian chunk: [{col.GREEN}r{col.END}]; Add English chunk: [{col.BLUE}e{col.END}]; One step back: [{col.YELLOW}z{col.END}]; OK: [{col.RED}o{col.END}]; ABORT: [{col.CYAN}A{col.END}]  :::  {col.MAGENTA}')

        if fork == 'r':
            russ_to_add += r_sections.pop(0) + '\n\n'
            edit_record.append('r')
        elif fork == 'e':
            eng_to_add += e_sections.pop(0) + '\n\n'
            edit_record.append('e')
        elif fork == 'z':
            while fork == 'z' and russ_to_add and eng_to_add and edit_record:
                # Pattern for finding the last section; to be returned to sections
                last_section_pattern = r'(?<=\n\n)(?!.*\n\n).*?(?=\n\n$)' 

                if edit_record[-1] == 'r':
                    last_sect = re.search(last_section_pattern, russ_to_add, re.DOTALL)
                    if last_sect: sect_to_return = last_sect.group()
                    else: sect_to_return = russ_to_add[:-2]
                    r_sections.insert(0, sect_to_return)
                    russ_to_add = re.sub(sect_to_return + '\n\n', '', russ_to_add)
                    edit_record.pop()

                elif edit_record[-1] == 'e':
                    last_sect = re.search(last_section_pattern, eng_to_add, re.DOTALL)
                    if last_sect: sect_to_return = last_sect.group()
                    else: sect_to_return = eng_to_add[:-2]
                    e_sections.insert(0, sect_to_return)
                    eng_to_add = re.sub(sect_to_return + '\n\n', '', eng_to_add)
                    edit_record.pop()

                parallel_print(get_pure_text(russ_to_add), get_pure_text(eng_to_add))

                fork = input(f'Still further back? [{col.GREEN}z{col.END}]; Continue forward: [{col.BLUE}o{col.END}] :::  {col.MAGENTA}')
                if fork == 'z': continue
                else: break

        elif fork.upper() == 'A':
            return 'abort'

        else:
            outdict['russ_to_add'] = russ_to_add
            outdict['eng_to_add'] = eng_to_add
            outdict['rsect'] = r_sections
            outdict['esect'] = e_sections
            break
    
    return outdict

############################################
# The MAIN standalone manual merge funtion #
############################################

def manual_merge(russ_text, eng_text, output_file_name, html_soup):
    sutt_no = re.search(r'mn[0-9]+', output_file_name)
    russ_filepath = f'test/{sutt_no}-russ.txt'
    eng_filepath = f'test/{sutt_no}-eng.txt'

    r_sections = [sect.strip() for sect in russ_text.split('\n\n')]
    e_sections = [sect.strip() for sect in eng_text.split('\n\n')]

    # Preparing the original html outer wrap for the new merged content
    td_tag = html_soup.find('td', {'style': 'text-align: justify', 'valign': 'top'})
    td_tag.clear()

    # Removing sections that has already been previously processed
    merge_name = output_file_name.replace('_bilingual.html', '-merger.txt')
    if merge_name in os.listdir('test'):
        with open(f'test/{merge_name}', 'r', encoding='utf-8') as f:
            merge_cont = f.read()
        output = [sect.strip() for sect in merge_cont.split('\n\n')]
        if len(output) > 2:
            while r_sections[0] in output:
                r_sections.pop(0)
            while e_sections[0] in output:
                e_sections.pop(0)
            russ_to_add = r_sections.pop(0) + '\n\n'
            output = [sect + '\n\n' for sect in output]
        else:
            output = []
            russ_to_add = r_sections.pop(0) + '\n\n'
            russ_to_add += r_sections.pop(0) + '\n\n'
    else:
        output = []
        russ_to_add = r_sections.pop(0) + '\n\n'
        russ_to_add += r_sections.pop(0) + '\n\n'


    eng_to_add = e_sections.pop(0) + '\n\n'
    edit_record = []

    while r_sections and e_sections:
        parallel_print(get_pure_text(russ_to_add), get_pure_text(eng_to_add))

        fork = input(f'Add Russian chunk: [{col.GREEN}r{col.END}]; Add English chunk: [{col.BLUE}e{col.END}]; One step back: [{col.YELLOW}z{col.END}]; OK: [{col.RED}o{col.END}]; ABORT: [{col.CYAN}A{col.END}]  :::  {col.MAGENTA}')

        if fork == 'r':
            russ_to_add += r_sections.pop(0) + '\n\n'
            edit_record.append('r')
        elif fork == 'e':
            eng_to_add += e_sections.pop(0) + '\n\n'
            edit_record.append('e')
        elif fork == 'z':
            while fork == 'z' and russ_to_add and eng_to_add and edit_record:
                # Pattern for finding the last section; to be returned to sections
                last_section_pattern = r'(?<=\n\n)(?!.*\n\n).*?(?=\n\n$)' 

                if edit_record[-1] == 'r':
                    last_sect = re.search(last_section_pattern, russ_to_add, re.DOTALL)
                    if last_sect: sect_to_return = last_sect.group()
                    else: sect_to_return = russ_to_add[:-2]
                    r_sections.insert(0, sect_to_return)
                    russ_to_add = re.sub(sect_to_return + '\n\n', '', russ_to_add)
                    edit_record.pop()

                elif edit_record[-1] == 'e':
                    last_sect = re.search(last_section_pattern, eng_to_add, re.DOTALL)
                    if last_sect: sect_to_return = last_sect.group()
                    else: sect_to_return = eng_to_add[:-2]
                    e_sections.insert(0, sect_to_return)
                    eng_to_add = re.sub(sect_to_return + '\n\n', '', eng_to_add)
                    edit_record.pop()

                parallel_print(get_pure_text(russ_to_add), get_pure_text(eng_to_add))

                fork = input(f'Still further back? [{col.GREEN}z{col.END}]; Continue forward: [{col.BLUE}o{col.END}] :::  {col.MAGENTA}')
                if fork == 'z': continue
                else: break

        elif fork.upper() == 'A':
            # Inserting 2 empty line after the last merged sections
            last_eng = output[-1]
            last_russ = output[-2]
            r_text = russ_text.replace(last_russ, last_russ + '\n\n\n\n')
            e_text = eng_text.replace(last_eng, last_eng + '\n\n\n\n')
            with open(russ_filepath, 'w', encoding='utf-8') as f:
                f.write(r_text)
            with open(eng_filepath, 'w', encoding='utf-8') as f:
                f.write(e_text)

            part_merged_txt = "".join(output)

            # Saving the partial merged texts in temporary file at "test/mn**-merger.txt" file
            file_name = output_file_name.replace('_bilingual.html', '-merger.txt')
            with open(f'test/{file_name}', 'w', encoding='utf-8') as f:
                f.write(part_merged_txt)

            part_merge_soup = BeautifulSoup(part_merged_txt, 'lxml')
            td_tag.append(part_merge_soup)

            with open(f'test/full_html_merge/part_{output_file_name}', 'w', encoding='utf-8') as f:
                f.write(str(html_soup))
            print(f'{col.SEP}The merging process has been aborted midway. The processed part saved at {col.RED}"test/full_html_merge/part_{output_file_name}"!{col.SEP}')
            return part_merged_txt
        
        else:
            output.append(russ_to_add)
            output.append(eng_to_add)
            russ_to_add = r_sections.pop(0) + '\n\n'
            eng_to_add = e_sections.pop(0) + '\n\n'
            edit_record = []

    # Adding whatever remains
    output.append(russ_to_add)
    output.append(eng_to_add)
    if r_sections:
        output.extend(r_sections)
    if e_sections:
        output.extend(e_sections)

    # Write to output with empty lines between sections
    merged_content = '\n\n'.join(output)
    with open(f'MN bilingual/merger edited/{output_file_name[:-4]}txt', 'w', encoding='utf-8') as f:
        f.write(merged_content)

    html_content = BeautifulSoup(merged_content, 'lxml')
    
    td_tag.append(html_content)

    with open(f'MN bilingual/html_merged_final/{output_file_name}', 'w', encoding='utf-8') as f:
        cont = str(html_soup).replace('TEXT-INDENT: 2em', 'TEXT-INDENT: 2em; margin-bottom: 15px;')
        f.write(cont)

    print(f'{col.SEP}The end of the sutta has been reached. The merged content has been saved at {col.GREEN}MN bilingual/html_merged_final/{output_file_name} !!!{col.SEP}')



if __name__ == '__main__':
    directory = '/home/soceyya/Desktop/BUDDHA\'S WORDS/mn'
    no = "96"

    # Russian translation with stress marks
    russ_filepath = f'Маджхима Никая с ударениями/mn{no}-sv.html'
    # English translation 
    eng_filepath = f'/home/soceyya/Desktop/BUDDHA\'S WORDS/mn/mn{no}.html'
    # Final html file of the merged translations, in "test/full_html_merge" for now
    output_file_name = f'mn{no}_bilingual.html'

    if f'mn{no}-russ.txt' in os.listdir('test'):
        with open(russ_filepath, 'r', encoding='utf-8') as f:
            cont = f.read()
        html_soup = BeautifulSoup(cont, 'lxml')
        with open(f'test/mn{no}-russ.txt', 'r', encoding='utf-8') as f:
            russ_text = f.read()
    else:
        russ_text, html_soup = sv_sutt_process(russ_filepath)

    if f'mn{no}-eng.txt' in os.listdir('test'):
        with open(f'test/mn{no}-eng.txt', 'r', encoding='utf-8') as f:
            eng_text = f.read()
    else:
        eng_text = bw_sut_process(eng_filepath)

    manual_merge(russ_text, eng_text, output_file_name, html_soup)


    # russ = 'Buddha_words/mn5-russ.txt'
    # eng = 'Buddha_words/mn5-eng.txt'
    # merger = 'Buddha_words/mn5-merger.txt'
