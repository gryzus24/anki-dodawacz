import sys

import colorama
from colorama import Fore

from src.data import color_data, config

colorama.init(autoreset=True)

if sys.platform.startswith('linux'):
    # cmd on Windows or even whole Windows can't display proper bold font
    # mac can be problematic too. Input_c and inputtext_c same story
    BOLD = '\033[1m'
    END = '\033[0m'
else:
    BOLD = ''
    END = ''


class Color:
    def __init__(self, color_name):
        if not sys.platform.startswith('linux') and color_name in ('input_c', 'inputtext_c'):
            self.color_name = ''
        else:
            self.color_name = color_name

    @property
    def color(self):
        try:
            return color_data['colors'][config[self.color_name]]
        except KeyError:
            return ''

    # not sure whether I should use __repr__ or @property to update colors
    # The best would be a single class that holds colors, but I'm not sure
    # how to dynamically update individual color's state


R = Fore.RESET
GEX = Color('success_c')
YEX = Color('attention_c')

syn_c = Color('syn_c')
psyn_c = Color('psyn_c')
pidiom_c = Color('pidiom_c')
def1_c = Color('def1_c')
def2_c = Color('def2_c')
index_c = Color('index_c')
phrase_c = Color('phrase_c')
phon_c = Color('phon_c')
pos_c = Color('pos_c')
poslabel_c = Color('poslabel_c')
etym_c = Color('etym_c')
synpos_c = Color('synpos_c')
syngloss_c = Color('syngloss_c')
err_c = Color('error_c')
delimit_c = Color('delimit_c')
inputtext_c = Color('inputtext_c')
input_c = Color('input_c')
