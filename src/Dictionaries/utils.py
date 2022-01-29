# Copyright 2021-2022 Gryzus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import subprocess
import sys
from shutil import get_terminal_size

import urllib3
from bs4 import BeautifulSoup
from urllib3.exceptions import NewConnectionError, ConnectTimeoutError

from src.colors import err_c
from src.data import config, USER_AGENT, POSIX, WINDOWS, ON_WINDOWS_CMD

PREPOSITIONS = (
    'beyond', 'of', 'outside', 'upon', 'with', 'within',
    'behind', 'from', 'like', 'opposite', 'to', 'under',
    'after', 'against', 'around', 'near', 'over', 'via',
    'among', 'except', 'for', 'out', 'since', 'through',
    'about', 'along', 'beneath', 'underneath', 'unlike',
    'below', 'into', 'on', 'onto', 'past', 'than', 'up',
    'across', 'by', 'despite', 'inside', 'off', 'round',
    'at', 'beside', 'between', 'in', 'towards', 'until',
    'above', 'as', 'before', 'down', 'during', 'without'
)

http = urllib3.PoolManager(timeout=10, headers=USER_AGENT)


def handle_connection_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if isinstance(e.__context__, NewConnectionError):
                print(f'{err_c}Could not establish a connection,\n'
                      'check your Internet connection and try again.')
            elif isinstance(e.__context__, ConnectTimeoutError):
                print(f'{err_c}Connection timed out.')
            else:
                print(f'{err_c}An unexpected error occurred in {func.__qualname__}.')
                raise
    return wrapper


@handle_connection_exceptions
def request_soup(url, fields=None, **kw):
    r = http.request_encode_url('GET', url, fields=fields, **kw)
    # At the moment only WordNet uses other than utf-8 encoding (iso-8859-1),
    # so as long as there are no decoding problems we'll use utf-8.
    return BeautifulSoup(r.data.decode(), 'lxml')


class ClearScreen:
    def __enter__(self):
        if WINDOWS:
            # There has to exist a less hacky way of doing `clear -x` on Windows.
            # I'm not sure if it works on terminals other than cmd and WT
            height = get_terminal_size().lines
            if ON_WINDOWS_CMD:
                # Move cursor up and down
                h = height * '\n'
                sys.stdout.write(f'{h}\033[{height}A')
            else:
                # Use Windows ANSI sequence to clear the screen
                sys.stdout.write((height - 1) * '\n' + '\033[2J')
            sys.stdout.flush()
        elif POSIX:
            # Even though `clear -x` is slower than using
            # ANSI escapes it doesn't have flickering issues.
            sys.stdout.write('\033[?25l')  # Hide cursor
            sys.stdout.flush()
            subprocess.run(['clear', '-x'])  # I hope the `-x` option works on macOS.
        else:
            sys.stdout.write(f'\033[39m`-top on`{err_c} command unavailable on {sys.platform!r}\n')

    def __exit__(self, tp, inst, tb):
        if POSIX:
            sys.stdout.write('\033[?25h')  # Show cursor
            sys.stdout.flush()


def hide(content, phrase):
    def case_replace(a, b):
        nonlocal content
        content = content.replace(a, b).replace(a.capitalize(), b).replace(a.upper(), b.upper())

    three_dots = config['hideas']
    nonoes = (
        'the', 'and', 'a', 'is', 'an', 'it',
        'or', 'be', 'do', 'does', 'not', 'if', 'he'
    )

    words_in_phrase = phrase.lower().split()
    for word in words_in_phrase:
        if word in nonoes:
            continue

        if not config['upreps']:
            if word in PREPOSITIONS:
                continue

        # "Ω" is a placeholder
        case_replace(word, f"{three_dots}Ω")
        if word.endswith('e'):
            case_replace(word[:-1] + 'ing', f'{three_dots}Ωing')
            if word.endswith('ie'):
                case_replace(word[:-2] + 'ying', f'{three_dots}Ωying')
        elif word.endswith('y'):
            case_replace(word[:-1] + 'ies', f'{three_dots}Ωies')
            case_replace(word[:-1] + 'ied', f'{three_dots}Ωied')

    if config['keependings']:
        return content.replace('Ω', '')
    else:
        # e.g. from "We weren't ...Ωed for this." -> "We weren't ... for this."
        split_content = content.split('Ω')
        temp = [split_content[0].strip()]
        for elem in split_content[1:]:
            for letter in elem:
                if letter in (' ', '.', ':'):
                    break
                elem = elem.replace(letter, '', 1)
            temp.append(elem.strip())
        return ' '.join(temp)


def get_config_terminal_size():
    term_width, term_height = get_terminal_size()
    config_width, flag = config['textwidth']

    if flag == '* auto' or config_width > term_width:
        # cmd always reports wrong width by 1 cell.
        if ON_WINDOWS_CMD:
            term_width -= 1
        return term_width, term_height
    return config_width, term_height


def wrap_lines(string, textwidth=79, gap=0, indent=0):
    # gap: space left for characters before the start of the
    #        first line and indent for the subsequent lines.
    # indent: additional indent for the remaining lines.
    # This comment is wrapped with `gap=5, indent=2`.

    def _indent_and_connect(_lines):
        for i in range(1, len(_lines)):
            _lines[i] = (gap + indent) * ' ' + _lines[i]
        return _lines

    def no_wrap(string_):
        line = string[:textwidth - gap]
        if line.endswith(' '):
            line = line.replace(' ', '  ', 1)

        lines = [line.strip()]
        string_ = string_[textwidth - gap:].strip()
        while string_:
            llen = textwidth - indent - gap
            line = string_[:llen]
            if line.endswith(' '):
                line = line.replace(' ', '  ', 1)

            lines.append(line.strip())
            string_ = string_[llen:].strip()
        return _indent_and_connect(lines)

    def trivial_wrap():
        lines = []
        line = []
        current_llen = gap
        for word in string.split():
            # >= for one character right-side padding
            word_len = len(word)
            if current_llen + word_len >= textwidth:
                lines.append(' '.join(line))
                current_llen = gap + indent
                line = []

            line.append(word)
            current_llen += word_len + 1

        lines.append(' '.join(line))
        return _indent_and_connect(lines)

    def justification_wrap():
        lines = []
        line = []
        current_llen = gap
        for word in string.split():
            word_len = len(word)
            if current_llen + word_len >= textwidth:
                nwords = len(line)
                if nwords > 1:
                    i = 0
                    filling = textwidth - current_llen
                    # filling shouldn't be negative but just in case.
                    while filling > 0:
                        if i > nwords - 2:
                            # go back to the first word
                            i = 0
                        line[i] += ' '
                        filling -= 1
                        i += 1

                lines.append(' '.join(line))
                line = []
                current_llen = gap + indent

            line.append(word)
            current_llen += word_len + 1

        lines.append(' '.join(line))
        return _indent_and_connect(lines)

    # Gap is the gap between indexes and strings
    if len(string) <= textwidth - gap:
        return [string]

    if config['textwrap'] == 'regular':
        textwidth += 1
        return trivial_wrap()
    elif config['textwrap'] == 'justify':
        return justification_wrap()
    return no_wrap(string)


def wrap_and_pad(lines, textwidth, gap=0, indent=0):
    # Wraps and adds right side padding that matches `textwidth`.
    fl, *rest = wrap_lines(lines, textwidth, gap, indent)
    result = [fl + (textwidth - len(fl) - gap) * ' ']
    for line in rest:
        result.append(line + (textwidth - len(line)) * ' ')
    return result
