#!/usr/bin/env python3

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

from __future__ import annotations

import functools
import os
import sys
from itertools import chain, repeat
from typing import Generator, NoReturn, Optional, Sequence

import src.ffmpeg_interface as ffmpeg
from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.dictionary_base import Dictionary, filter_dictionary
from src.Dictionaries.farlex import ask_farlex
from src.Dictionaries.lexico import ask_lexico
from src.Dictionaries.utils import http
from src.Dictionaries.utils import less_print
from src.Dictionaries.wordnet import ask_wordnet
from src.__version__ import __version__
from src.colors import BOLD, Color, DEFAULT, R
from src.commands import INTERACTIVE_COMMANDS, HELP_ARG_COMMANDS, NO_HELP_ARG_COMMANDS
from src.console_main import console_ui_entry
from src.data import LINUX, WINDOWS, config
from src.input_fields import ConsoleInputField

# Completer doesn't work on Windows.
# It should work on macOS, but I haven't tested it yet.
if LINUX:
    from src.completer import Completer
    tab_completion = Completer(
        tuple(chain(
            INTERACTIVE_COMMANDS,
            NO_HELP_ARG_COMMANDS,
            HELP_ARG_COMMANDS,
            ('--define-all',)
        ))
    )
else:
    from contextlib import nullcontext as tab_completion


def search_field() -> str:
    # Returns a non-empty string.
    while True:
        try:
            word = input('Search $ ').strip()
        except EOFError:
            sys.stdout.write('\r')
        else:
            if word:
                return word


def dispatch_command(s: str) -> bool:
    # Returns whether command was dispatched or not.
    args = s.split()
    cmd = args[0]
    if cmd in NO_HELP_ARG_COMMANDS:
        result = NO_HELP_ARG_COMMANDS[cmd](*args)
    elif cmd in INTERACTIVE_COMMANDS:
        result = INTERACTIVE_COMMANDS[cmd](ConsoleInputField(), *args)
    elif cmd in HELP_ARG_COMMANDS:
        func, note, usage = HELP_ARG_COMMANDS[cmd]
        if (len(args) == 1 or
           (len(args) == 2 and args[1].strip(' -').lower() in ('h', 'help'))
        ):
            sys.stdout.write(f'{Color.heed}{note}{R}\n{cmd} {usage}\n')
            return True
        else:
            result = func(*args)
    else:
        return False

    if result.error:
        sys.stdout.write(f'{Color.err}{result.error}\n')
    if result.reason:
        sys.stdout.write(result.reason)
        sys.stdout.write('\n')
    if result.output:
        less_print(result.output)

    return True


def search() -> str:
    while True:
        with tab_completion():
            word = search_field()

        dispatched = dispatch_command(word)
        if not dispatched:
            return word


DICT_DISPATCH = {
    'ahd': ask_ahdictionary,
    'lexico': ask_lexico, 'l': ask_lexico,
    'idioms': ask_farlex, 'idiom': ask_farlex, 'i': ask_farlex,
    'wordnet': ask_wordnet, 'wnet': ask_wordnet,
    '-': lambda _: None
}


@functools.lru_cache(maxsize=None)
def query_dictionary(key: str, query: str) -> Dictionary | None:
    return DICT_DISPATCH[key](query)


def get_dictionaries(
        query: str, dict_flags: Optional[Sequence[str]] = None
) -> list[Dictionary] | None:
    if dict_flags is None or not dict_flags:
        dict_flags = [config['-dict']]

    result = []
    for flag in dict_flags:
        ret = query_dictionary(flag, query)
        if ret is not None:
            result.append(ret)

    if result:
        return result

    if config['-dict2'] == '-':
        return None

    print(f'{Color.heed}Querying the fallback dictionary...')
    fallback_dict = query_dictionary(config['-dict2'], query)
    if fallback_dict is not None:
        return [fallback_dict]

    if config['-dict'] != 'idioms' and config['-dict2'] != 'idioms':
        print(f"{Color.heed}To ask the idioms dictionary use {R}`{query} -i`")
    return None


class QuerySettings:
    __slots__ = 'queries', 'user_sentence', 'recording_filename'

    def __init__(self) -> None:
        self.queries: list[tuple[str, list[str], list[str]]] = []
        self.user_sentence = ''
        self.recording_filename = ''

    def flags_for_query(self, n: int) -> list[str]:
        if n < 0:
            raise ValueError('n must be >= 0')
        return self.queries[n][2]

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}('
            f'queries={self.queries}, '
            f'user_sentence={self.user_sentence}, '
            f'recording_filename={self.recording_filename})'
        )


def parse_query(full_query: str) -> QuerySettings | None:
    query_separators = (',', ';')
    chars_to_strip = ' ' + ''.join(query_separators)

    full_query = full_query.strip(chars_to_strip)
    if not full_query:
        return None

    settings = QuerySettings()
    for field in max(map(str.split, repeat(full_query), query_separators), key=len):
        field = field.strip(chars_to_strip)
        if not field:
            continue

        query, *flags = field.split(' -')
        emph_start = query.find('<')
        emph_stop = query.rfind('>')
        if ~emph_start and ~emph_stop:
            settings.user_sentence = (
                query[:emph_start]
                + '{{' + query[emph_start + 1:emph_stop] + '}}'
                + query[emph_stop + 1:]
            )
            query = query[emph_start + 1:emph_stop]

        dictionary_flags = []
        query_flags = []
        recorded = False
        for flag in flags:
            flag = flag.strip(' -')
            if not flag:
                continue

            if flag in {'rec', 'record'}:
                if not recorded:
                    settings.recording_filename = ffmpeg.capture_audio(query)
                    recorded = True
            elif flag in DICT_DISPATCH:
                dictionary_flags.append(flag)
            elif flag in {'c', 'compare'}:
                dictionary_flags.extend((config['-dict'], config['-dict2']))
            else:
                query_flags.append(flag)

        settings.queries.append((query, dictionary_flags, query_flags))

    return settings


def main_loop(query: str) -> None:
    settings = parse_query(query)
    if settings is None:
        return

    # Retrieve dictionaries,
    dictionaries: list[Dictionary] = []
    for query, dictionary_flags, query_flags in settings.queries:
        dicts = get_dictionaries(query, dictionary_flags)
        if dicts is None:
            continue
        elif query_flags:
            dictionaries.extend(map(filter_dictionary, dicts, repeat(query_flags)))
        else:
            dictionaries.extend(dicts)

    if not dictionaries:
        return

    if not config['-curses']:
        return console_ui_entry(dictionaries, settings)

    try:
        from src.curses_main import curses_ui_entry
    except ImportError:
        if WINDOWS:
            sys.stdout.write(
                f'{Color.err}The curses module could not be imported:{R}\n'
                f'Curses support on Windows is close to non-existent,\n'
                f'but there are a few things you can try:\n'
                f' - install CygWin or MinGW32,\n'
                f' - install WSL,\n'
                f' - pip install windows-curses (not recommended),\n'
                f' - use the console backend: -curses off,\n'
                f' - install Linux or some other Unix-like OS\n\n'
            )
            return
        else:
            raise

    curses_ui_entry(dictionaries, settings)


def from_define_all_file(_input: str) -> Generator[str, None, None]:
    # Search for the "define_all" like file.
    for file in os.listdir():
        if file.lower().startswith('define') and 'all' in file.lower():
            define_file = file
            break
    else:
        print(f'{Color.err}Could not find {R}"define_all.txt"{Color.err} file.\n'
              f'Create one and paste your list of queries there.')
        return None

    _, _, sep = _input.partition(' ')
    sep = sep.strip()
    if not sep:
        sep = ','

    with open(define_file) as f:
        lines = [x.strip().strip(sep) for x in f if x.strip().strip(sep)]

    if not lines:
        print(f'{R}"{define_file}"{Color.err} file is empty.')
        return None

    for line in lines:
        for _input in line.split(sep):
            _input = _input.strip()
            if _input:
                yield _input

    print(f'{Color.heed}** {R}"{define_file}"{Color.heed} has been exhausted **\n')


def main() -> NoReturn:
    sys.stdout.write(
        f'{BOLD}- Ankidodawacz v{__version__} -{DEFAULT}\n'
        f'type -h for usage and configuration\n\n\n'
    )
    while True:
        user_query = search()
        if user_query.startswith(('-rec', '--record')):
            ffmpeg.capture_audio()
        elif user_query.startswith('--define-all'):
            for query in from_define_all_file(user_query):
                main_loop(query)
        else:
            main_loop(user_query)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        sys.stdout.write('\n')
    finally:
        http.pools.clear()
