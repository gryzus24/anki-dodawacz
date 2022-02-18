from colorama import init  # type: ignore

from src.data import POSIX, config, color_name_to_ansi

init(autoreset=True)


# This class provides quick and dynamic access to config colors.
class Color:
    __slots__ = 'color',

    def __init__(self, color: str) -> None:
        self.color = color

    def __str__(self) -> str:
        return color_name_to_ansi[config[self.color]]

    def __len__(self) -> int:
        # For proper formatting
        return len(color_name_to_ansi[config[self.color]])


if POSIX:
    BOLD, DEFAULT = '\033[1m', '\033[0m'
else:
    BOLD = DEFAULT = ''

# Reset all color attributes except BOLD
R = '\033[39m'
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
label_c = Color('label_c')
inflection_c = Color('inflection_c')
etym_c = Color('etym_c')
syngloss_c = Color('syngloss_c')
err_c = Color('error_c')
delimit_c = Color('delimit_c')
