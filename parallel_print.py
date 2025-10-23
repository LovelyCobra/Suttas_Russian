import os, re
from cobraprint import col, cur_down_start, cur_pos_abs

def make_lines(text: str, width: int) -> list[str]:
    text_len = len(text)
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
   

def parallel_print(russ_text, eng_text, width=50):

    r_txt = make_lines(russ_text, width)
    max_length = max(len(line) for line in r_txt)

    e_txt = make_lines(eng_text, width)

    os.system('cls' if os.name == 'nt' else 'clear')

    print(col.SEP)
    for line in r_txt:
        print(line)
    for i, line in enumerate(e_txt):
        print(f'{cur_pos_abs(i+4, 75)}{line}')
    
    print(f'{cur_down_start(abs(len(r_txt)-len(e_txt))+5)}{col.SEP}')

if __name__ == '__main__':
    russ = 'Buddha_words/mn5-russ.txt'
    eng = 'Buddha_words/mn5-eng.txt'
    
    parallel_print(russ, eng)
