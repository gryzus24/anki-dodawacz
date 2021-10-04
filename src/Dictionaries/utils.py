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

from requests.exceptions import ConnectionError as RqConnectionError
from requests.exceptions import Timeout

from src.colors import err_c
from src.data import config


def valid_index_or_zero(list_of_ints: list) -> int:
    try:
        fc = list_of_ints[0]
    except IndexError:
        return 0
    if fc < 1:
        return 0
    return fc - 1


def handle_connection_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
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
        else:
            return result

    return wrapper


def wrap_lines(string: str, term_width=79, index_width=0, indent=0, gap=0):
    def no_wrap(string_):
        lines = [string_[:real_width].strip()]
        string_ = string_[real_width:].strip()
        while string_:
            lines.append(string_[:term_width - indent_plus_index_width].strip())
            string_ = string_[term_width - indent_plus_index_width:].strip()

        connector = '\n' + indent_plus_index_width * ' '
        return connector.join(lines)

    def trivial_wrap():
        lines = []
        current_llen = 0
        line = ''
        for word in string_divided:
            # >= for one character right-side padding
            word_len = len(word)
            if current_llen + word_len >= real_width:
                lines.append(line.strip())
                current_llen = indent - gap
                line = ''

            line += word + ' '
            current_llen += word_len + 1

        lines.append(line)
        connector = '\n' + indent_plus_index_width * ' '
        return connector.join(lines)

    def justification_wrap():
        # I feel like this implementation is horrible
        lines = []
        line = ''
        # -1 because last space before wrapping is ignored in justification
        spaces_between_words = -1
        current_llen = 0
        for word in string_divided:
            if current_llen + len(word) >= real_width:
                line = line.rstrip()
                filling = real_width - current_llen
                if spaces_between_words > 0:
                    set_spaces = ' '
                    while filling > 0:
                        if filling <= spaces_between_words:
                            line = line.replace(set_spaces, set_spaces + ' ', filling)
                            break

                        line = line.replace(set_spaces, set_spaces + ' ', spaces_between_words)
                        filling -= spaces_between_words
                        set_spaces += ' '

                lines.append(line.strip())
                line = ''
                spaces_between_words = -1
                current_llen = indent - gap

            spaces_between_words += 1
            line += word + ' '
            current_llen += len(word) + 1

        lines.append(line.strip())
        connector = '\n' + indent_plus_index_width * ' '
        return connector.join(lines)

    # Gap is the gap between indexes and strings
    real_width = term_width - index_width - gap
    if len(string) <= real_width:
        return string

    indent_plus_index_width = indent + index_width
    if config['textwrap'] == '-':
        return no_wrap(string)

    if term_width < 67:
        # mitigate the one character right-side padding
        real_width += 1

    string_divided = string.split()
    if config['textwrap'] == 'regular':
        return trivial_wrap()
    return justification_wrap()
