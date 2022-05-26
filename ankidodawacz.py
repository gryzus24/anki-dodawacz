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

import os
import sys
from itertools import chain, repeat
from typing import Generator, NoReturn, Optional, Sequence

import src.anki_interface as anki
import src.commands as c
import src.ffmpeg_interface as ffmpeg
import src.help as h
from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.farlex import ask_farlex
from src.Dictionaries.lexico import ask_lexico
from src.Dictionaries.utils import http
from src.Dictionaries.wordnet import ask_wordnet
from src.__version__ import __version__
from src.colors import BOLD, Color, DEFAULT, R
from src.console_main import console_ui_entry
from src.data import LINUX, boolean_cmd_to_msg, cmd_to_msg_usage, config

required_arg_commands = {
    # commands that take arguments
    '-textwrap': c.set_text_value_commands,
    '-columns': c.set_width_settings,
    '-indent': c.set_width_settings,
    '-default': c.set_free_value_commands,
    '-note': c.set_free_value_commands,
    '-deck': c.set_free_value_commands,
    '-tags': c.set_free_value_commands,
    '-hideas': c.set_free_value_commands,
    '--audio-path': c.set_audio_path, '-ap': c.set_audio_path,
    '-tsc': c.set_text_value_commands,
    '-dict': c.set_text_value_commands,
    '-dict2': c.set_text_value_commands,
    '-dupescope': c.set_text_value_commands,
    '-audio': c.set_text_value_commands,
    '-recqual': c.set_text_value_commands,
    '-margin': c.set_numeric_value_commands,
    '-color': c.set_colors, '-c': c.set_colors,
}

no_arg_commands = {
    '--audio-device': ffmpeg.user_set_audio_device,
    '-refresh': anki.refresh_cached_notes,
    '--add-note': anki.user_add_custom_note,
    '--help': h.quick_help, '-help': h.quick_help, '-h': h.quick_help,
    '--help-define-all': h.define_all_help,
    '--help-config': h.config_help, '--help-conf': h.config_help,
    '--help-recording': h.recording_help, '--help-rec': h.recording_help,
    '-config': c.print_config_representation, '-conf': c.print_config_representation
}

# Completer doesn't work on Windows.
# It should work on macOS, but I haven't tested it yet.
if LINUX:
    import src.completer as completer
    tab_completion = completer.Completer(
        tuple(chain(
            boolean_cmd_to_msg,
            cmd_to_msg_usage,
            no_arg_commands,
            ('-b', '--browse', '--define-all')
        ))
    )
else:
    from contextlib import nullcontext as tab_completion


def search_field() -> str:
    while True:
        try:
            word = input('Search $ ').strip()
        except EOFError:
            sys.stdout.write('\r')
            continue
        if word:
            return word


def search_interface() -> str:
    while True:
        with tab_completion():
            word = search_field()

        args = word.split()
        cmd = args[0]
        if cmd in no_arg_commands:
            response = no_arg_commands[cmd]()
            if response is not None:
                print(f'{Color.err if response.error else Color.GEX}{response.body}')
            continue
        elif cmd in ('-b', '--browse'):
            response = anki.gui_browse_cards(query=args[1:])
            if response.error:
                print(f'{Color.err}Could not open the card browser:\n{R}{response.body}\n')
            continue

        if cmd in boolean_cmd_to_msg:
            method = c.boolean_commands
            message, usage = boolean_cmd_to_msg[cmd], '{on|off}'
        elif cmd in required_arg_commands:
            method = required_arg_commands[cmd]
            message, usage = cmd_to_msg_usage[cmd]
        else:
            return word

        try:
            if args[1].strip('-').lower() in ('h', 'help'):
                raise IndexError
        except IndexError:  # Print help
            print(f'{Color.YEX}{message}\n'
                  f'{R}{cmd} {usage}')

            # Print additional information
            if cmd in ('-ap', '--audio-path'):
                print(f'{BOLD}Current audio path:\n'
                      f'{DEFAULT}{config["audio_path"]}\n')
            elif cmd in ('-c', '-color'):
                c.color_command()
        else:
            err = method(*args, message=message)
            if err is not None:
                print(f'{Color.err}{err}')


DICT_DISPATCH = {
    'ahd': ask_ahdictionary,
    'lexico': ask_lexico, 'l': ask_lexico,
    'idioms': ask_farlex, 'idiom': ask_farlex, 'i': ask_farlex,
    'wordnet': ask_wordnet, 'wnet': ask_wordnet,
    '-': lambda _: None
}
def get_dictionaries(
        query: str, dict_flags: Optional[Sequence[str]] = None
) -> list[Dictionary] | None:
    if dict_flags is None or not dict_flags:
        dict_flags = [config['-dict']]

    result = []
    for flag in dict_flags:
        dictionary = DICT_DISPATCH[flag](query)
        if dictionary is not None:
            result.append(dictionary)

    if result:
        return result

    if config['-dict2'] == '-':
        return None

    print(f'{Color.YEX}Querying the fallback dictionary...')
    fallback_dict = DICT_DISPATCH[config['-dict2']](query)
    if fallback_dict is not None:
        return [fallback_dict]

    if config['-dict'] != 'idioms' and config['-dict2'] != 'idioms':
        print(f"{Color.YEX}To ask the idioms dictionary use {R}`{query} -i`")
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
            f'{self.queries=}, '
            f'{self.user_sentence=}, '
            f'{self.recording_filename=})'
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

        query_flags = ['f'] if config['-fsubdefs'] else []
        dictionary_flags = []
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
    dictionaries = []
    for query, dictionary_flags, query_flags in settings.queries:
        dicts = get_dictionaries(query, dictionary_flags)
        if dicts is None:
            continue
        for d in dicts:
            d.filter_contents(query_flags)
            assert d.contents, f'{type(d).__name__} for {query} is empty!\n' \
                               'This incident should be reported.'
            dictionaries.append(d)

    if not dictionaries:
        return

    if config['-curses']:
        from src.curses_main import curses_ui_entry
        curses_ui_entry(dictionaries, settings)
    else:
        console_ui_entry(dictionaries, settings)


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

    print(f'{Color.YEX}** {R}"{define_file}"{Color.YEX} has been exhausted **\n')


def main() -> NoReturn:
    sys.stdout.write(
        f'{BOLD}- Ankidodawacz v{__version__} -{DEFAULT}\n'
        f'type -h for usage and configuration\n\n\n'
    )
    while True:
        user_query = search_interface()
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
