# Copyright 2021 Gryzus
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

from shutil import get_terminal_size

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError as RqConnectionError
from requests.exceptions import Timeout

from src.colors import err_c
from src.data import config, USER_AGENT, PREPOSITIONS

request_session = requests.Session()
request_session.headers.update(USER_AGENT)


def handle_connection_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Timeout:
            print(f'{err_c.color}Słownik nie odpowiada.')
        except RqConnectionError:
            print(f'{err_c.color}Połączenie ze słownikiem zostało zerwane.')
        except ConnectionError:
            print(f'{err_c.color}Nie udało się połączyć ze słownikiem,\n'
                  f'sprawdź swoje połączenie i spróbuj ponownie.')
        except Exception:
            print(f'{err_c.color}Wystąpił nieoczekiwany błąd w {func.__qualname__}.')
            raise
    return wrapper


@handle_connection_exceptions
def request_soup(url):
    reqs = request_session.get(url, timeout=10)
    reqs.encoding = 'UTF-8'
    return BeautifulSoup(reqs.text, 'lxml')


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


def get_term_size():
    term_width, term_height = get_terminal_size()
    config_width, flag = config['textwidth']

    if flag == '* auto' or config_width > term_width:
        return term_width, term_height
    return config_width, term_height


def wrap_lines(string, term_width=79, index_width=0, indent=0, gap=0):
    def _indent_and_connect(_lines):
        for i in range(1, len(_lines)):
            _lines[i] = (indent + index_width) * ' ' + _lines[i]
        return _lines

    def no_wrap(string_):
        line = string[:real_width]
        if line.endswith(' '):
            line = line.replace(' ', '  ', 1)

        lines = [line.strip()]
        string_ = string_[real_width:].strip()
        while string_:
            llen = term_width - indent - index_width
            line = string_[:llen]
            if line.endswith(' '):
                line = line.replace(' ', '  ', 1)

            lines.append(line.strip())
            string_ = string_[llen:].strip()
        return _indent_and_connect(lines)

    def trivial_wrap():
        lines = []
        line = []
        current_llen = 0
        for word in string.split():
            # >= for one character right-side padding
            word_len = len(word)
            if current_llen + word_len >= real_width:
                lines.append(' '.join(line))
                current_llen = indent - gap
                line = []

            line.append(word)
            current_llen += word_len + 1

        lines.append(' '.join(line))
        return _indent_and_connect(lines)

    def justification_wrap():
        lines = []
        line = []
        current_llen = 0
        for word in string.split():
            word_len = len(word)
            if current_llen + word_len >= real_width:
                nwords = len(line)
                if nwords > 1:
                    i = 0
                    filling = real_width - current_llen
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
                current_llen = indent - gap

            line.append(word)
            current_llen += word_len + 1

        lines.append(' '.join(line))
        return _indent_and_connect(lines)

    # Gap is the gap between indexes and strings
    real_width = term_width - index_width - gap
    if len(string) <= real_width:
        return [string]

    if config['textwrap'] == 'regular':
        real_width += 1
        return trivial_wrap()
    elif config['textwrap'] == 'justify':
        return justification_wrap()
    return no_wrap(string)
