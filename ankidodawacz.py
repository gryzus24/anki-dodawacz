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

import binascii
import os
import shutil
import sys
from itertools import chain, repeat
from subprocess import DEVNULL, PIPE, Popen
from typing import Generator, Iterable, NoReturn, Optional, Sequence

import src.anki_interface as anki
import src.commands as c
import src.ffmpeg_interface as ffmpeg
import src.help as h
from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.audio_dictionaries import ahd_audio, diki_audio, lexico_audio
from src.Dictionaries.dictionary_base import Dictionary, stringify_columns
from src.Dictionaries.farlex import ask_farlex
from src.Dictionaries.lexico import ask_lexico
from src.Dictionaries.utils import (ClearScreen, get_width_per_column, hide, http,
                                    wrap_lines)
from src.Dictionaries.wordnet import WordNet, ask_wordnet
from src.__version__ import __version__
from src.colors import BOLD, DEFAULT, R, Color
from src.data import (HORIZONTAL_BAR, LINUX, ROOT_DIR, WINDOWS,
                      boolean_cmd_to_msg, cmd_to_msg_usage, config)
from src.input_fields import sentence_input

if config['curses']:
    from src.curses_interface import curses_init
    USING_CURSES = True  # temporary solution
else:
    USING_CURSES = False

required_arg_commands = {
    # commands that take arguments
    '--delete-last': c.delete_cards, '--delete-recent': c.delete_cards,
    '-textwrap': c.set_text_value_commands,
    '-colviewat': c.set_width_settings,
    '-columns': c.set_width_settings,
    '-indent': c.set_width_settings,
    '-note': c.set_free_value_commands,
    '-deck': c.set_free_value_commands,
    '-tags': c.set_free_value_commands,
    '-hideas': c.set_free_value_commands,
    '--audio-path': c.set_audio_path, '-ap': c.set_audio_path,
    '-tsc': c.set_text_value_commands,
    '-dict': c.set_text_value_commands,
    '-dict2': c.set_text_value_commands,
    '-thes': c.set_text_value_commands,
    '-dupescope': c.set_text_value_commands,
    '-audio': c.set_text_value_commands,
    '-recqual': c.set_text_value_commands,
    '-margin': c.set_numeric_value_commands,
    '--field-order': c.change_field_order, '-fo': c.change_field_order,
    '-color': c.set_colors, '-c': c.set_colors,
    '-cd': c.set_input_field_defaults,
}
no_arg_commands = {
    '--audio-device': ffmpeg.set_audio_device,
    '-refresh': anki.refresh_cached_notes,
    '--add-note': anki.add_note_to_anki,
    '--help': h.quick_help, '-help': h.quick_help, '-h': h.quick_help,
    '--help-bulk': h.bulk_help, '--help-define-all': h.bulk_help,
    '--help-commands': h.commands_help, '--help-command': h.commands_help,
    '--help-config': h.commands_help, '--help-conf': h.commands_help,
    '--help-recording': h.recording_help, '--help-rec': h.recording_help,
    '-config': c.print_config_representation, '-conf': c.print_config_representation
}

# Completer doesn't work on Windows.
# It should work on macOS, but I haven't tested it yet.
if LINUX and USING_CURSES:
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


def search_interface() -> str:
    while True:
        with tab_completion():
            word = input('Search $ ').strip()
            if not word:
                continue

        args = word.split()
        cmd = args[0]
        if cmd in no_arg_commands:
            err = no_arg_commands[cmd]()
            if err is not None:
                print(f'{Color.err}{err}')
            continue
        elif cmd in ('-b', '--browse'):
            err = anki.gui_browse_cards(query=args[1:])
            if err is not None:
                print(f'{Color.err}{err}')
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
            elif cmd in ('-fo', '--field-order'):
                c.display_field_order()
            elif cmd in ('-c', '-color'):
                c.color_command()
            elif cmd == '-cd':
                print(f'{BOLD}Field names:{DEFAULT}\n'
                      f'def, exsen, pos, etym, syn, all\n')
        else:
            err = method(*args, message=message)
            if err is not None:
                print(f'{Color.err}{err}')


DICT_DISPATCH = {
    'ahd': ask_ahdictionary,
    'lexico': ask_lexico, 'l': ask_lexico,
    'idioms': ask_farlex, 'idiom': ask_farlex, 'i': ask_farlex,
    '-': lambda _: None
}
def get_dictionaries(
        query: str, dict_flags: Optional[Sequence[str]] = None
) -> list[Dictionary] | None:
    if dict_flags is None or not dict_flags:
        dict_flags = [config['dict']]

    result = []
    for flag in dict_flags:
        dictionary = DICT_DISPATCH[flag](query)
        if dictionary is not None:
            result.append(dictionary)

    if result:
        return result

    if config['dict2'] == '-':
        return None

    print(f'{Color.YEX}Querying the fallback dictionary...')
    fallback_dict = DICT_DISPATCH[config['dict2']](query)
    if fallback_dict is not None:
        return [fallback_dict]

    if config['dict'] != 'idioms' and config['dict2'] != 'idioms':
        print(f"{Color.YEX}To ask the idioms dictionary use {R}`{query} -i`")
    return None


def get_thesaurus(query: str) -> Dictionary | None:
    if config['thes'] == '-':
        # Returning WordNet just for its input_cycle.
        return WordNet()

    return ask_wordnet(
        query.split()[0] if 'also' in query.split() else query
    )


def save_audio_url(audio_url: str) -> str | NoReturn:
    _, _, filename = audio_url.rpartition('/')
    audio_content = http.urlopen('GET', audio_url).data
    audio_path = config['audio_path']

    # Use AnkiConnect to save audio files if 'collection.media' path isn't given.
    # However, specifying the audio_path is preferred as it's way faster.
    if config['ankiconnect'] and os.path.basename(audio_path) != 'collection.media':
        response = anki.invoke('storeMediaFile',
                               filename=filename,
                               data=binascii.b2a_base64(  # convert to base64 string
                                    audio_content, newline=False).decode())
        if not response.error:
            return f'[sound:{filename}]'

    try:
        with open(os.path.join(audio_path, filename), 'wb') as file:
            file.write(audio_content)
        return f'[sound:{filename}]'
    except FileNotFoundError:
        print(f"{Color.err}Saving audio {R}{filename}{Color.err} failed\n"
              f"Current audio path: {R}{audio_path}\n"
              f"{Color.err}Make sure the directory exists and try again\n")
        return ''
    except Exception:
        print(f'{Color.err}Unexpected error occurred while saving audio')
        raise


def _from_diki(phrase: str, flags: Optional[Iterable[str]] = None) -> str:
    if flags is None:
        flags = []
    flag = ''
    for f in flags:
        if f in {'n', 'v', 'a', 'adj', 'noun', 'verb', 'adjective'}:
            flag = '-' + f[0]
            break
    url = diki_audio(phrase, flag)
    return save_audio_url(url) if url else ''


def save_audio(
        dictionary_name: str,
        audio_url: str,
        phrase: str,
        flags: Optional[Iterable[str]] = None
) -> str:
    server = config['audio']
    if server == '-':
        return ''

    # Farlex has no audio, so we try to get it from diki.
    if server == 'diki' or dictionary_name == 'farlex':
        return _from_diki(phrase, flags)

    if server == 'auto' or dictionary_name == server:
        if audio_url:
            return save_audio_url(audio_url)
        else:
            print(f'{Color.err}This dictionary does not have the pronunciation for {R}{phrase}\n'
                  f'{Color.YEX}Querying diki...')
            return _from_diki(phrase, flags)

    if server == 'ahd':
        audio_url = ahd_audio(phrase)
    elif server == 'lexico':
        audio_url = lexico_audio(phrase)
    else:
        raise AssertionError('unreachable')

    return save_audio_url(audio_url) if audio_url else ''


def format_definitions(definitions: str) -> str:
    styles = (
        ('', ''),
        ('<span style="opacity: .6;">', '</span>'),
        ('<small style="opacity: .4;">', '</small>'),
        ('<small style="opacity: .2;"><sub>', '</sub></small>')
    )
    formatted = []
    style_no = len(styles)
    for i, item in enumerate(definitions.split('<br>'), start=1):
        style_i = style_no - 1 if i > style_no else i - 1
        prefix, suffix = styles[style_i]

        prefix += f'<small style="color: #4EAA72;">{i}.</small>  '
        formatted.append(prefix + item + suffix)

    return '<br>'.join(formatted)


def save_card_to_file(field_values: dict[str, str]) -> None:
    with open('cards.txt', 'a', encoding='utf-8') as f:
        f.write('\t'.join(field_values[field] for field in config['fieldorder']) + '\n')
    print(f'{Color.GEX}Card successfully saved to a file\n')


def _display_in_less(s: str) -> None:
    executable = shutil.which('less')
    if executable is None:
        if WINDOWS:
            print(
                f"'less'{Color.err} is not available in %PATH% or in the current directory.\n"
                f"You can grab the latest Windows executable from:\n"
                f"{R}https://github.com/jftuga/less-Windows/releases\n"
            )
        else:
            print(f"{Color.err}Could not find the 'less' executable.\n")
        return

    # r - accept escape sequences. `-R` does not produce desirable results on Windows.
    # F - do not open the pager if output fits on the screen.
    # K - exit on SIGINT. *This is important not to break keyboard input.
    # Q - be quiet.
    # X - do not clear the screen after exiting from the pager.
    if WINDOWS:
        env = {'LESSCHARSET': 'UTF-8'}
        options = '-rFKQX'
    else:
        env = None
        options = '-RFKQX'
    with Popen((executable, options), stdin=PIPE, stderr=DEVNULL, env=env) as process:
        try:
            process.communicate(s.encode())
        except:
            process.kill()

        # less returns 2 on SIGINT.
        return_code = process.poll()
        if return_code and return_code != 2:
            print(f"{Color.err}Could not open the pager as: 'less {options}'\n")


def display_dictionary(dictionary: Dictionary) -> None:
    if not dictionary.contents:
        return

    width, height = shutil.get_terminal_size()
    ncols, state = config['columns']
    if state == '* auto':
        ncols = None

    columns, col_width, last_col_fill =\
        dictionary.prepare_to_print(
            ncols, width, height - 3,
            config['colviewat'][0],
            config['textwrap'],
            config['indent'][0],
            config['showsign']
        )
    raw_str = stringify_columns(columns, col_width, last_col_fill)
    if config['less']:
        with ClearScreen():
            _display_in_less(raw_str + '\n')
    else:
        with ClearScreen():
            sys.stdout.write(raw_str + '\n')


def display_many_dictionaries(dictionaries: list[Dictionary]) -> None:
    width, height = shutil.get_terminal_size()
    col_width, last_col_fill = get_width_per_column(width, len(dictionaries))

    columns = []
    for d in dictionaries:
        formatted = d.format_dictionary(
            col_width, config['textwrap'], config['indent'][0], config['showsign']
        )
        columns.append([line.lstrip('$!') for line in formatted])

    raw_str = stringify_columns(columns, col_width, last_col_fill, ('║', '╥'))
    if config['less']:
        with ClearScreen():
            _display_in_less(raw_str + '\n')
    else:
        with ClearScreen():
            sys.stdout.write(raw_str + '\n')


def display_card(field_values: dict[str, str]) -> None:
    # field coloring
    color_of = {
        'def': Color.def1, 'syn': Color.syn, 'exsen': Color.exsen,
        'phrase': Color.phrase, 'pz': '', 'pos': Color.pos,
        'etym': Color.etym, 'audio': '', 'recording': '',
    }
    textwidth, _ = shutil.get_terminal_size()
    delimit = textwidth * HORIZONTAL_BAR
    adjusted_textwidth = int(0.95 * textwidth)
    padding = (textwidth - adjusted_textwidth) // 2 * " "

    print(f'\n{Color.delimit}{delimit}')
    for field_number, field in enumerate(config['fieldorder']):
        if field == '-':
            continue

        for line in field_values[field].split('<br>'):
            for subline in wrap_lines(line, config['textwrap'], adjusted_textwidth, 0, 0):
                print(f'{color_of[field]}{padding}{subline}')

        if field_number + 1 == config['fieldorder_d']:  # d = delimitation
            print(f'{Color.delimit}{delimit}')

    print(f'{Color.delimit}{delimit}')


def parse_query(full_query: str) -> tuple[list[tuple[str, str]], str]:
    # Returns:
    #   - list of queries and not-parsed flags,
    #   - sentence (if provided)

    query_separators = (',', ';', '==')
    chars_to_strip = ' ' + ''.join(query_separators)

    full_query = full_query.strip(chars_to_strip)
    if not full_query:
        return [('', '')], ''

    if '<' in full_query and '>' in full_query:
        _query, _, flag_str = full_query.partition(' -')
        left, _, temp = full_query.partition('<')
        _query, _, right = temp.rpartition('>')
        return (
            [(_query.strip(), flag_str.strip())], left + _query + right
        )

    queries_flags = []
    for field in max(map(str.split, repeat(full_query), query_separators), key=len):
        field = field.strip(chars_to_strip)
        if field:
            _query, _, flag_str = field.partition(' -')
            queries_flags.append((_query.strip(), flag_str.strip()))

    return queries_flags, ''


def parse_flags(s: str) -> tuple[list[str], list[str], list[str]]:
    dict_flags, rec_flags, other_flags = [], [], []
    for flag in filter(None, s.split(' -')):
        flag = flag.strip(' -')
        if flag in {'ahd', 'i', 'idiom', 'idioms', 'farlex', 'l', 'lexico'}:
            dict_flags.append(flag)
        elif flag in {'c', 'compare'}:
            dict_flags.extend((config['dict'], config['dict2']))
        elif flag in {'rec', 'record'}:
            rec_flags.append(flag)
        else:
            other_flags.append(flag)

    if config['fsubdefs']:
        other_flags.append('f')

    return dict_flags, rec_flags, other_flags


def main_loop(query: str) -> None:
    field_values = {
        'def': '',
        'syn': '',
        'exsen': '',
        'phrase': '',
        'pz': '',
        'pos': '',
        'etym': '',
        'audio': '',
        'recording': '',
        '-': '',
    }

    _query_and_flags_list, sentence = parse_query(query)

    # Parse flags
    record_query = ''
    query_and_flags_list = []
    for _query, _flag_str in _query_and_flags_list:
        dict_flags, rec, other = parse_flags(_flag_str)
        if rec and not record_query:
            record_query = _query
        query_and_flags_list.append((_query, dict_flags, other))

    if record_query:
        field_values['recording'] = ffmpeg.capture_audio(record_query)

    # Retrieve dictionaries,
    # keep `other_flags` of current_dictionary for the `save_audio` function.
    dictionaries = []
    other_flags = None
    for _query, _dict_flags, _other_flags in query_and_flags_list:
        if other_flags is None:
            other_flags = _other_flags
        dicts = get_dictionaries(_query, _dict_flags)
        if dicts is not None:
            for d in dicts:
                d.filter_contents(_other_flags)
                assert d.contents, f'{type(d).__name__} for {query} is empty!\n' \
                                   'This incident should be reported.'
                dictionaries.append(d)

    if not dictionaries:
        return

    if USING_CURSES:
        r = curses_init(dictionaries)
        return

    # Display dictionaries
    current_dict = dictionaries[0]
    if len(dictionaries) > 1:
        display_many_dictionaries(dictionaries)
    else:
        display_dictionary(current_dict)

    if not config['createcards']:
        if config['thes'] == 'wordnet':
            # Use the first phrase to always make the correct query.
            # e.g. preferred -> prefer
            d = ask_wordnet(current_dict.phrases[0])
            if d is not None:
                display_dictionary(d)
        return

    # Ask for inputs
    if config['pz'] and not sentence:
        sentence = sentence_input()  # type: ignore[assignment]
        if sentence is None:
            return

    dictionary_contents = current_dict.input_cycle()
    if dictionary_contents is None:
        return

    field_values.update(dictionary_contents)

    phrase = field_values['phrase']
    if current_dict.allow_thesaurus:
        thesaurus = get_thesaurus(phrase)
        if thesaurus is None:
            return
        display_dictionary(thesaurus)
        thesaurus_contents = thesaurus.input_cycle()
        if thesaurus_contents is not None:
            field_values.update(thesaurus_contents)

    field_values['audio'] = save_audio(
        current_dict.name, field_values['audio'], phrase, other_flags
    )
    # Format card content
    if sentence:
        field_values['pz'] = sentence
    else:
        if config['tsc'] != '-':
            if field_values['exsen']:
                field_values['pz'] = field_values['exsen']
                field_values['exsen'] = ''
            else:
                if config['tsc'] == 'strict':
                    field_values['pz'] = phrase
                    field_values['phrase'] = ''

    # Hide chosen phrase in content
    for elem in ('pz', 'def', 'exsen', 'syn'):
        content = field_values[elem]
        if content and config[f'u{elem}']:
            field_values[elem] = hide(
                content, phrase, config['hideas'],
                hide_prepositions=config['upreps'],
                keep_endings=config['keependings']
            )

    if config['cardpreview']:
        display_card(field_values)

    # Format card content
    for key, val in field_values.items():
        field_values[key] = val.replace("'", "&#39;").replace('"', '&quot;')

    if config['formatdefs']:
        field_values['def'] = format_definitions(field_values['def'])
    if '<br>' not in field_values['pz']:
        field_values['pz'] = field_values['pz'] \
            .replace('>', '</b>').replace('<', '<b style="color: #91cb7d;">', 1)

    print()
    if config['ankiconnect']:
        anki.add_card_to_anki(field_values)
    if config['savecards']:
        save_card_to_file(field_values)


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
    if config['audio_path'] == 'Cards_audio':
        # Providing the absolute path solves an occasional PermissionError on Windows.
        t = os.path.join(ROOT_DIR, 'Cards_audio')
        if not os.path.exists(t):
            os.mkdir(t)

    sys.stdout.write(
        f'{BOLD}- Ankidodawacz v{__version__} -{DEFAULT}\n'
        'type -h for usage and configuration\n\n\n'
    )

    while True:
        users_query = search_interface()
        if users_query.startswith(('-rec', '--record')):
            ffmpeg.capture_audio()
        elif users_query.startswith('--define-all'):
            for query in from_define_all_file(users_query):
                main_loop(query)
        else:
            main_loop(users_query)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        sys.stdout.write('\n')
    finally:
        http.pools.clear()
