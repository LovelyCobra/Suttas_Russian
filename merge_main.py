import re, os
from cobraprint import *
from manual_merge import add_manually

###############################
# A bunch of helper functions #
###############################

def get_sections(file_content):
    # Find all font or div sections
    sections = file_content.split('\n\n')
    sects = [sec.strip() for sec in sections]

    return sects

def get_pure_text(section):
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', section)
    # Remove all whitespace
    text = re.sub(r'\s[2:]', '', text)
    text = text.strip()
    return text

def has_ellipsis(section):
    # Check for ellipsis in the cleaned text (with spaces removed)
    text = get_pure_text(section)
    return '…' in text or '...' in text

def make_lines(text: str, width: int) -> list[str]:
    text_words = text.split(' ')
    text_lines = []
    current_line = ''

    while text_words:
        while len(current_line) < width and text_words:
            current_line += (text_words[0] + ' ')
            del text_words[0]
        text_lines.append(current_line)
        current_line = ""
    
    return text_lines
   

def parallel_print(russ_text, eng_text, width=30):

    r_txt = make_lines(russ_text, width)
    max_length = max(len(line) for line in r_txt)

    e_txt = make_lines(eng_text, width+20)

    os.system('cls' if os.name == 'nt' else 'clear')

    print(col.SEP)
    for line in r_txt:
        print(line)
    for i, line in enumerate(e_txt):
        print(f'{cur_pos_abs(i+4, max_length+30)}{line}')
    
    print(f'{cur_down_start(abs(len(r_txt)-len(e_txt)))}{col.SEP}')


############################################################
# The main function to merge Russian and English sections, #
# combining both automatic and manual approches            #
############################################################
'''Uses pre-processed html files saved at "test/" directory
containing core parts with all the paragraphs already having
the desired html tags.'''

def merge_files(russ_file, eng_file, output_file):
    with open(russ_file, 'r', encoding='utf-8') as f:
        russ_text = f.read()
    with open(eng_file, 'r', encoding='utf-8') as f:
        eng_text = f.read()

    r_sections = get_sections(russ_text)
    e_sections = get_sections(eng_text)

    output = []
    outdict = {}

    # Adding opening paragraphs manually

    russ_to_add = r_sections.pop(0) + '\n\n'
    russ_to_add += r_sections.pop(0) + '\n\n'
    eng_to_add = e_sections.pop(0) + '\n\n'

    outdict = add_manually(russ_to_add, eng_to_add, r_sections, e_sections)

    def txt_len(section):
        l = len(get_pure_text(section))
        return l

    while r_sections and e_sections:

        if outdict and outdict != 'abort':
            output.append(outdict['russ_to_add'])
            output.append(outdict['eng_to_add'])
            r_sections = outdict['rsect']
            e_sections = outdict['esect']
            russ_to_add = eng_to_add = ""
        elif outdict == 'abort':
            part_merged_txt = "".join(output)

            with open(f'test/merged/part_{output_file}', 'w', encoding='utf-8') as f:
                f.write(part_merged_txt)
            print(f'{col.SEP}The merging process has been aborted midway. The processed part saved at {col.RED}"test/merged/part_{output_file}"!{col.SEP}')
            return part_merged_txt
        outdict = {}

        russ_to_add += r_sections.pop(0) + '\n\n'
        eng_to_add += e_sections.pop(0) + '\n\n'

        # if ellipsis present, switch to manual matching
        if has_ellipsis(russ_to_add) or has_ellipsis(eng_to_add):
            outdict = add_manually(russ_to_add, eng_to_add, r_sections, e_sections)
            continue
        elif '<b>' in russ_to_add:  # Adding Russian sub-heading straigth away
            output.append(russ_to_add)
            russ_to_add = r_sections.pop(0) + '\n\n'

        r_len = txt_len(russ_to_add)
        e_len = txt_len(eng_to_add)

        if e_len * 1.25 < r_len:
            eng_to_add += e_sections.pop(0) + '\n\n'
            e_len = txt_len(eng_to_add)
            if e_len * 1.25 > r_len and e_len < r_len:
                output.append(russ_to_add)
                output.append(eng_to_add)
                russ_to_add = eng_to_add = ""
                continue
            else: 
                outdict = add_manually(russ_to_add, eng_to_add, r_sections, e_sections)
                continue

        elif r_len < 1.25 * e_len and r_len > 0.96 * e_len:
            output.append(russ_to_add)
            output.append(eng_to_add)
            russ_to_add = eng_to_add = ""
            continue

        elif r_len < 0.97 * e_len:
            russ_to_add += r_sections.pop(0) + '\n\n'
            r_len = txt_len(russ_to_add)
            if r_len < 1.25 * e_len and r_len > 0.96 * e_len:
                output.append(russ_to_add)
                output.append(eng_to_add)
                russ_to_add = eng_to_add = ""
                continue
            else: 
                outdict = add_manually(russ_to_add, eng_to_add, r_sections, e_sections)
                continue
        else:
            outdict = add_manually(russ_to_add, eng_to_add, r_sections, e_sections)
            continue

    # Adding what remains if anything
    if r_sections:
        output.extend([item + '\n\n' for item in r_sections])
    elif e_sections:
        output.extend([item + '\n\n' for item in e_sections])
    merged_txt = "".join(output)

    with open(f'test/merged/{output_file}', 'w', encoding='utf-8') as f:
        f.write(merged_txt)

    print(f'{col.SEP}Merging of the texts has been completed. The result has been saved at {col.RED}"test/merged/{output_file}"!{col.SEP}')

    return merged_txt



if __name__ == '__main__':
    no = '96'
    russ_file = f'test/mn{no}-russ.txt'
    eng_file = f'test/mn{no}-eng.txt'
    output_file = f'mn{no}-bill.txt'

    result = merge_files(russ_file, eng_file, output_file)

    # with open(f'test/mn1-russ.txt', 'r', encoding='utf-8') as f:
    #     russ_file_cont = f.read()
    # with open(f'test/mn1-eng.txt', 'r', encoding='utf-8') as f:
    #     eng_file_cont = f.read()

    # russ_sections = get_sections(russ_file_cont)
    # eng_sections = get_sections(eng_file_cont)
    # russ_text = get_pure_text(russ_sections[6])
    # eng_text = get_pure_text(eng_sections[6])
    # parallel_print(russ_text, eng_text)

    