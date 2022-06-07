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
from functools import lru_cache
from itertools import chain, repeat, compress
from typing import Generator, NoReturn, Optional, Sequence, TypedDict

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
}

help_commands = {
    '-config': c.print_config_representation, '-conf': c.print_config_representation,
    '--help': h.quick_help, '-help': h.quick_help, '-h': h.quick_help,
    '--help-config': h.config_help, '--help-conf': h.config_help,
    '--help-define-all': h.define_all_help,
    '--help-recording': h.recording_help, '--help-rec': h.recording_help,
}

# Completer doesn't work on Windows.
# It should work on macOS, but I haven't tested it yet.
if LINUX:
    from src.completer import Completer
    tab_completion = Completer(
        tuple(chain(
            boolean_cmd_to_msg,
            cmd_to_msg_usage,
            no_arg_commands,
            help_commands,
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
        if cmd in help_commands:
            help_commands[cmd]()
            continue
        elif cmd in no_arg_commands:
            response = no_arg_commands[cmd]()
            if response is not None:
                print(f'{Color.err if response.error else Color.success}{response.body}')
            continue
        elif cmd in ('-b', '--browse'):
            query_args = args[1:]
            if query_args:
                response = anki.gui_browse_cards(' '.join(query_args))
            else:
                response = anki.gui_browse_cards('added:1')
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
            print(f'{Color.heed}{message}\n'
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


@lru_cache(maxsize=None)
def _query(key: str, query: str) -> Dictionary | None:
    return DICT_DISPATCH[key](query)


def get_dictionaries(
        query: str, dict_flags: Optional[Sequence[str]] = None
) -> list[Dictionary] | None:
    if dict_flags is None or not dict_flags:
        dict_flags = [config['-dict']]

    result = []
    for flag in dict_flags:
        ret = _query(flag, query)
        if ret is not None:
            result.append(ret)

    if result:
        return result

    if config['-dict2'] == '-':
        return None

    print(f'{Color.heed}Querying the fallback dictionary...')
    fallback_dict = _query(config['-dict2'], query)
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


def multi_split(string: str, splits: set[str]) -> list[str]:
    # Splits a string at multiple places discarding redundancies just like `.split()`.
    result = []
    elem = ''
    for letter in string:
        if letter in splits:
            if elem:
                result.append(elem)
                elem = ''
        else:
            elem += letter
    if elem:
        result.append(elem)
    return result


def should_skip(label: str, flags: tuple[str, ...]) -> bool:
    labels = tuple(multi_split(label, {' ', '.', '&'}))
    for label in labels:
        if label.startswith(flags):
            return False
    for flag in flags:
        if flag.startswith(labels):
            return False
    return True


class EntryGroup(TypedDict):
    after: list[Sequence[str]]
    before: list[Sequence[str]]
    contents: list[Sequence[str]]
    header: Sequence[str] | None


def new_filtered_dictionary(dictionary: Dictionary, flags: Sequence[str]) -> Dictionary:
    for flag in flags:
        if flag.startswith('/'):
            look_for = flag[1:]
            break
    else:
        look_for = None

    if look_for is not None:
        flags = [x for x in flags if not x.startswith('/')]
    flags = tuple(map(str.lower, flags))

    added: set[str] = set()
    last_header = None
    header_contents = []
    result = []
    for entry in dictionary.contents:
        op = entry[0]
        if op in added:
            # We could use some salvaging methods like copying previous header's
            # contents or restructuring the original list of contents to make
            # later retrieval more consistent or something like that.
            # But to be completely honest, the "ask_dictionary" functions
            # should be more compliant, i.e. adding only one entry like:
            # NOTE, AUDIO, ETYM, POS and HEADER per PHRASE. Currently,
            # Lexico has some problems with this compliance when it comes to
            # words that have different pronunciations depending on whether
            # they are nouns, verb or adjectives (e.g. concert).
            continue
        elif op == 'HEADER':
            last_header = entry
            if entry[1]:  # header with title
                added.clear()
                group: EntryGroup = {
                    'after': [],
                    'before': [],
                    'contents': [],
                    'header': entry,
                }
                header_contents.append(group)
        elif op == 'PHRASE':
            added.clear()
            if last_header is None:
                group: EntryGroup = {  # type: ignore[no-redef]
                    'after': [],
                    'before': [entry],
                    'contents': [],
                    'header': None,
                }
                header_contents.append(group)
            else:
                if last_header[1]:
                    header_contents[-1]['before'].append(entry)
                else:
                    group: EntryGroup = {  # type: ignore[no-redef]
                        'after': [],
                        'before': [entry],
                        'contents': [],
                        'header': last_header,
                    }
                    header_contents.append(group)
                last_header = None
        elif op in {'LABEL', 'DEF', 'SUBDEF'}:
            header_contents[-1]['contents'].append(entry)
        elif op in {'PHRASE', 'NOTE', 'AUDIO'}:
            header_contents[-1]['before'].append(entry)
            added.add(op)
        elif op in {'POS', 'ETYM', 'SYN'}:
            header_contents[-1]['after'].append(entry)
            added.add(op)
        else:
            raise AssertionError(f'unreachable {op!r}')

    last_titled_header = None
    for header in header_contents:
        header_entry = header['header']
        if header_entry is not None and header_entry[1]:
            # If not looking for any specific word narrow search down to labels only.
            if look_for is None and header_entry[1].lower() in ('synonyms', 'idioms'):
                break
            last_titled_header = header_entry

        last_label_skipped = last_def_skipped = False
        last_label_i = last_def_i = None
        skips = []
        for i, entry in enumerate(header['contents']):
            op = entry[0]
            if op == 'LABEL':
                last_label_i = i
                if not entry[1]:
                    _skip_label = True
                else:
                    _skip_label = should_skip(entry[1].lower(), flags)
                skips.append(_skip_label)
                last_label_skipped = _skip_label
            elif 'DEF' in op:
                if op == 'DEF':
                    last_def_i = i

                if not last_label_skipped or not flags:
                    _skip_def = False
                elif not entry[3]:
                    if op == 'DEF':
                        _skip_def = True
                    elif op == 'SUBDEF':
                        _skip_def = last_def_skipped
                    else:
                        raise AssertionError(f'unreachable {op!r}')
                else:
                    _skip_def = should_skip(entry[3].lower(), flags)

                if look_for is not None:
                    for word in entry[1].split():
                        if look_for in word:
                            break
                    else:
                        if not _skip_def:
                            _skip_def = True
                            # needs testing
                            #if not last_label_skipped:
                            #    skips[last_label_i] = True

                skips.append(_skip_def)
                if not _skip_def:
                    if last_label_i is not None:
                        skips[last_label_i] = False
                    if op == 'SUBDEF' and last_def_i is not None:
                        skips[last_def_i] = False
                if op == 'DEF':
                    last_def_skipped = _skip_def
            else:
                raise AssertionError(f'unreachable {op!r}')

        if False not in skips:
            continue

        if last_titled_header is not None:
            result.append(last_titled_header)
            last_titled_header = None
        elif header_entry is not None:
            result.append(header_entry)

        result.extend(header['before'])
        result.extend(compress(header['contents'], map(lambda x: not x, skips)))
        result.extend(header['after'])

    if result:
        return Dictionary(result)
    else:
        return dictionary


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
            dictionaries.extend(
                map(new_filtered_dictionary, dicts, repeat(query_flags))
            )
        else:
            dictionaries.extend(dicts)

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

    print(f'{Color.heed}** {R}"{define_file}"{Color.heed} has been exhausted **\n')


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
