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
from typing import Generator, NoReturn, Optional, Sequence, NamedTuple, TypeVar

import src.ffmpeg_interface as ffmpeg
from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.dictionary_base import Dictionary, filter_dictionary
from src.Dictionaries.farlex import ask_farlex
from src.Dictionaries.lexico import ask_lexico
from src.Dictionaries.utils import http
from src.Dictionaries.wordnet import ask_wordnet
from src.__version__ import __version__
from src.colors import BOLD, Color, DEFAULT, R
from src.commands import INTERACTIVE_COMMANDS, HELP_ARG_COMMANDS, NO_HELP_ARG_COMMANDS
from src.console_main import console_ui_entry
from src.data import LINUX, WINDOWS, STRING_TO_BOOL, config
from src.term_utils import less_print

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


T = TypeVar('T')
class InteractiveCommandHandler:
    @staticmethod
    def writeln(s: str) -> None:
        print(s)

    @staticmethod
    def choose_item(prompt: str, seq: Sequence[T], *, default: int = 1) -> T | None:
        i = input(f"{prompt} [{default}]: ").strip()
        try:
            choice = int(i) if i else default
        except ValueError:
            return None
        if 0 < choice <= len(seq):
            return seq[choice - 1]
        return None

    @staticmethod
    def ask_yes_no(prompt: str, *, default: bool) -> bool:
        d = 'Y/n' if default else 'y/N'
        i = input(f'{prompt} [{d}]: ').strip().lower()
        return STRING_TO_BOOL.get(i, default)


def dispatch_command(s: str) -> bool:
    # Returns whether command was dispatched or not.
    args = s.split()
    cmd = args[0]
    if cmd in NO_HELP_ARG_COMMANDS:
        result = NO_HELP_ARG_COMMANDS[cmd](*args)
    elif cmd in INTERACTIVE_COMMANDS:
        result = INTERACTIVE_COMMANDS[cmd](InteractiveCommandHandler(), *args)
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
            typed = search_field()

        dispatched = dispatch_command(typed)
        if not dispatched:
            return typed


class QueryNotFound(Exception):
    pass


DICT_FLAG_TO_QUERY_KEY = {
    'ahd': 'ahd',
    'i': 'farlex', 'farlex': 'farlex',
    'l': 'lexico', 'lexico': 'lexico',
    'wnet': 'wordnet', 'wordnet': 'wordnet',
}
# Every dictionary has its individual key to avoid cluttering cache
# with identical dictionaries that were called with the same query
# but different "dictionary flag", which acts as nothing more but
# an alias.
DICTIONARY_LOOKUP = {
    'ahd': ask_ahdictionary,
    'farlex': ask_farlex,
    'lexico': ask_lexico,
    'wordnet': ask_wordnet,
}
@functools.lru_cache(maxsize=None)
def query_dictionary(key: str, query: str) -> Dictionary | NoReturn:
    # raises "QueryNotFound" instead of returning to avoid caching None values.
    # Caching them is hardly useful, because:
    # - it is unlikely that user wants to lookup again the word that
    #   they misspelled or that is not in the dictionary.
    # - also, it helps avoid a nasty bug that prevents the user to re-lookup
    #   a query after they lost the Internet connection.
    result = DICTIONARY_LOOKUP[key](query)
    if result is None:
        raise QueryNotFound
    return result


def get_dictionaries(
        query: str, flags: Optional[Sequence[str]] = None
) -> list[Dictionary] | None:
    if flags is None or not flags:
        flags = [config['-dict']]

    # Ideally `none_keys` would be static and kept throughout searches like
    # "phrase1, phrase1, phrase1", but in normal, non-malicious (źdź,źdź,źdź...),
    # usage it is never needed, because nobody really queries the same thing
    # multiple times that is also not in the dictionary.
    none_keys = set()
    result = []
    for flag in flags:
        key = DICT_FLAG_TO_QUERY_KEY[flag]
        if key not in none_keys:
            try:
                result.append(query_dictionary(key, query))
            except QueryNotFound:
                none_keys.add(key)

    if result:
        return result
    if config['-dict2'] == '-':
        return None
    fallback_key = DICT_FLAG_TO_QUERY_KEY[config['-dict2']]
    if fallback_key in none_keys:
        return None

    print(f'{Color.heed}Querying the fallback dictionary...')
    try:
        result.append(query_dictionary(fallback_key, query))
    except QueryNotFound:
        return None
    else:
        return result


class Query(NamedTuple):
    query:       str
    sentence:    str
    dict_flags:  list[str]
    query_flags: list[str]
    record:      bool


class QuerySettings:
    __slots__ = 'queries', 'user_sentence', 'recording_filename'

    def __init__(self, queries: list[Query], user_sentence: str, recording_filename: str) -> None:
        self.queries = queries
        self.user_sentence = user_sentence
        self.recording_filename = recording_filename

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}('
            f'queries={self.queries!r}, '
            f'user_sentence={self.user_sentence!r}, '
            f'recording_filename={self.recording_filename!r})'
        )


def parse_query(full_query: str) -> list[Query] | None:
    separators = ',;'
    chars_to_strip = ' ' + separators

    full_query = full_query.strip(chars_to_strip)
    if not full_query:
        return None

    result = []
    for field in max(map(str.split, repeat(full_query), separators), key=len):
        field = field.strip(chars_to_strip)
        if not field:
            continue

        query, *flags = field.split(' -')
        emph_start = query.find('<')
        emph_stop = query.rfind('>')
        if ~emph_start and ~emph_stop and emph_start < emph_stop:
            sentence = (
                query[:emph_start]
                + '{{' + query[emph_start + 1:emph_stop] + '}}'
                + query[emph_stop + 1:]
            )
            query = query[emph_start + 1:emph_stop]
        else:
            sentence = ''

        dict_flags = []
        query_flags = []
        record = False
        for flag in flags:
            flag = flag.strip(' -')
            if not flag:
                continue

            if flag in {'rec', 'record'}:
                record = True
            elif flag in DICT_FLAG_TO_QUERY_KEY:
                dict_flags.append(flag)
            elif flag in {'c', 'compare'}:
                d1, d2 = config['-dict'], config['-dict2']
                if d1 in DICT_FLAG_TO_QUERY_KEY:
                    dict_flags.append(d1)
                if d2 in DICT_FLAG_TO_QUERY_KEY:
                    dict_flags.append(d2)
            else:
                query_flags.append(flag)

        result.append(
            Query(query.strip(), sentence, dict_flags, query_flags, record)
        )

    return result


def main_dispatch(s: str) -> None:
    parsed = parse_query(s)
    if parsed is None:
        return

    dictionaries: list[Dictionary] = []
    recorded = False
    user_sentence = recording_filename = ''
    valid_queries = []
    for query in parsed:
        if query.sentence and not user_sentence:
            user_sentence = query.sentence
        if query.record and not recorded:
            recording_filename = ffmpeg.capture_audio(query.query)
            recorded = True

        dicts = get_dictionaries(query.query, query.dict_flags)
        if dicts is not None:
            valid_queries.append(query)
            if query.query_flags:
                dictionaries.extend(
                    map(filter_dictionary, dicts, repeat(query.query_flags))
                )
            else:
                dictionaries.extend(dicts)

    if dictionaries:
        settings = QuerySettings(valid_queries, user_sentence, recording_filename)
    else:
        return

    if config['-curses']:
        try:
            from src.curses_main import curses_ui_entry
        except ImportError:
            if WINDOWS:
                sys.stdout.write(
                    f'{Color.err}The curses module could not be imported:{R}\n'
                    f'to use the console front-end type: -curses off\n'
                    f'Windows is not officially supported,\n'
                    f'but there are a few things you can try:\n'
                    f' - install CygWin or MinGW32,\n'
                    f' - install WSL and run it from there,\n'
                    f' - pip install windows-curses (works, but broken),\n'
                    f' - install Linux or some other Unix-like OS\n'
                    f'   (changing an entire operating system just to run\n'
                    f'   this program is a chad move for sure :^)\n\n'
                )
                return
            else:
                raise

        curses_ui_entry(dictionaries, settings)
    else:
        console_ui_entry(dictionaries, settings)


def from_define_all_file(s: str) -> Generator[str, None, None]:
    # Search for the "define_all" like file.
    for file in os.listdir():
        if file.lower().startswith('define') and 'all' in file.lower():
            define_file = file
            break
    else:
        print(f'{Color.err}Could not find {R}"define_all.txt"{Color.err} file.\n'
              f'Create one and paste your list of queries there.')
        return None

    _, _, sep = s.partition(' ')
    sep = sep.strip()
    if not sep:
        sep = ','

    with open(define_file) as f:
        lines = [x.strip().strip(sep) for x in f if x.strip().strip(sep)]

    if not lines:
        print(f'{R}"{define_file}"{Color.err} file is empty.')
        return None

    for line in lines:
        for query in line.split(sep):
            query = query.strip()
            if query:
                yield query

    print(f'{Color.heed}** {R}"{define_file}"{Color.heed} has been exhausted **')


def main() -> NoReturn:
    sys.stdout.write(
        f'{BOLD}- Ankidodawacz v{__version__} -{DEFAULT}\n'
        f'type -h for usage and configuration\n\n\n'
    )
    while True:
        typed = search()
        if typed.startswith(('-rec', '--record')):
            ffmpeg.capture_audio()
        elif typed.startswith('--define-all'):
            for query in from_define_all_file(typed):
                main_dispatch(query)
        else:
            main_dispatch(typed)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        sys.stdout.write('\n')
    finally:
        http.pools.clear()
