import sys

from src.data import str_colors_to_color, config, WINDOWS

# Reset all color attributes except BOLD
R = '\033[39m'

if WINDOWS:
    from colorama import init

    init(autoreset=True)

    BOLD = ''
    DEFAULT = ''
else:
    BOLD = '\033[1m'
    # Use default foreground color
    DEFAULT = '\033[0m'

    class Autoreset:
        def __init__(self, fp):
            self.fp = fp

        def write(self, a):
            self.fp.write(a + R)

        def writelines(self, a):
            for line in a:
                self.fp.write(line)

        def flush(self):
            self.fp.flush()

    sys.stdout = Autoreset(sys.stdout)


class Color:
    def __init__(self, color):
        self.color = color

    def __str__(self):
        return str_colors_to_color[config[self.color]]

    def __len__(self):
        # For proper formatting
        return len(str_colors_to_color[config[self.color]])


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
