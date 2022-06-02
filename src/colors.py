from colorama import init  # type: ignore[import]

from src.data import POSIX, config

init(autoreset=True)

# `R` resets all color attributes except BOLD
R = '\033[39m'
if POSIX:
    BOLD, DEFAULT = '\033[1m', '\033[0m'
else:
    BOLD = DEFAULT = ''

# Color values are updated dynamically with `setattr(Color, ..., config[..._c])`
class _Color:
    success    = config['success_c']
    heed       = config['heed_c']

    syn        = config['syn_c']
    exsen      = config['exsen_c']
    def1       = config['def1_c']
    def2       = config['def2_c']
    sign       = config['sign_c']
    index      = config['index_c']
    phrase     = config['phrase_c']
    phon       = config['phon_c']
    pos        = config['pos_c']
    label      = config['label_c']
    inflection = config['inflection_c']
    etym       = config['etym_c']
    syngloss   = config['syngloss_c']
    err        = config['err_c']
    delimit    = config['delimit_c']

Color = _Color()

