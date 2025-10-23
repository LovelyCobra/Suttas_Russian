from pprint import pprint

'''
A simple module for clear and easy-to-read printing in a console.
Essentially just assembling ANSI escape sequences under easy-to-remember names

'''

# Movement of the cursor, both relative to its current position and to an absolute position, positioning starts with 1, not 0
def cur_up(n=1):
    return f"\033[{n}A"
    
def cur_down(n=1):
    return f"\033[{n}B"
    
def cur_forward(n=1):
    return f"\033[{n}C"
    
def cur_back(n=1):
    return f"\033[{n}D"
    
def cur_down_start(n=1):
    return f"\033[{n}E"
    
def cur_up_start(n=1):
    return f"\033[{n}F"
    
def cur_hor_abs(n=1):
    return f"\033[{n}G"
    
def cur_pos_abs(n=1, m=1):
    return f"\033[{n};{m}H"


# Clearing of a line or part of a line or the screen or part of it:
def clr_line_from_cur(where="end"):
    if where == "end": n = 0
    elif where == "start": n = 1
    elif where == "all": n = 2
    return f"\033[{n}K"

def clr_screen_from_cur(where="end"):
    if where == "end": n = 0
    elif where == "start": n = 1
    elif where == "all": n = 2
    elif where == "ALL": n = 3
    return f"\033[{n}J"

# Colors:
class col:
    GREY = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    END = '\033[0m'
    SEP = '\n\033[93m----------------------------------------------\033[0m\n'
    
# Background colors    
class bgr:
    GREY = '\033[100m'
    RED = '\033[101m'
    GREEN = '\033[102m'
    YELLOW = '\033[103m'
    BLUE = '\033[104m'
    MAGENTA = '\033[105m'
    CYAN = '\033[106m'
    WHITE = '\033[107m'
    END = '\033[0m'
    
res_all = '\033[0m'


# Styles
class style:
    bold = '\033[1m'
    dim = '\033[2m'
    it = '\033[3m'
    undr = '\033[4m'
    slow_blink = '\033[5m'
    rapid_blink = '\033[6m'
    
        
# Printing with pprint plus empty line before and after

def cprint(obj):
    print('')
    pprint(obj)
    print('')