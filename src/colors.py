from colorama import init  # type: ignore[import]

from src.data import POSIX

init(autoreset=True)

# `R` resets all color attributes except BOLD
R = '\033[39m'
if POSIX:
    BOLD, DEFAULT = '\033[1m', '\033[0m'
else:
    BOLD = DEFAULT = ''

ERR = '\033[91m'
HEED = '\033[93m'
SUCCESS = '\033[92m'
