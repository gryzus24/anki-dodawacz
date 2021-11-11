import sys

import colorama
from colorama import Fore

from src.data import str_colors_to_color, config

colorama.init(autoreset=True)

if sys.platform.startswith('linux'):
    # cmd on Windows or even whole Windows can't display proper bold font in terminal
    # mac can be problematic too.
    BOLD = '\033[1m'
    END = '\033[0m'
else:
    BOLD = ''
    END = ''


class Color:
    def __init__(self, color_name):
        self.color_name = color_name

    @property
    def color(self):
        return str_colors_to_color[config[self.color_name]]

    # not sure whether I should use __repr__ or @property to update colors
    # The best would be a single class that holds colors, but I'm not sure
    # how to dynamically update individual color's state


R = Fore.RESET
GEX = Color('success_c')
YEX = Color('attention_c')

syn_c = Color('syn_c')
exsen_c = Color('exsen_c')
def1_c = Color('def1_c')
def2_c = Color('def2_c')
defsign_c = Color('defsign_c')
index_c = Color('index_c')
phrase_c = Color('phrase_c')
phon_c = Color('phon_c')
pos_c = Color('pos_c')
poslabel_c = Color('poslabel_c')
inflection_c = Color('inflection_c')
etym_c = Color('etym_c')
syngloss_c = Color('syngloss_c')
err_c = Color('error_c')
delimit_c = Color('delimit_c')
