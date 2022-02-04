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
import os.path
from itertools import chain
from shutil import get_terminal_size
from typing import Generator, NoReturn, Optional, Sequence

import src.anki_interface as anki
import src.commands as c
import src.ffmpeg_interface as ffmpeg
import src.help as h
from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.audio_dictionaries import ahd_audio, diki_audio, lexico_audio
from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.farlex import ask_farlex
from src.Dictionaries.lexico import ask_lexico
from src.Dictionaries.utils import ClearScreen, hide, http, wrap_lines
from src.Dictionaries.wordnet import WordNet, ask_wordnet
from src.__version__ import __version__
from src.colors import (BOLD, DEFAULT, GEX, R, YEX, def1_c, delimit_c, err_c, etym_c,
                        exsen_c, phrase_c, pos_c, syn_c)
from src.data import (HORIZONTAL_BAR, LINUX, ON_WINDOWS_CMD, ROOT_DIR, boolean_cmd_to_msg,
                      cmd_to_msg_usage, config)
from src.input_fields import sentence_input

required_arg_commands = {
    # commands that take arguments
    '--delete-last': c.delete_cards, '--delete-recent': c.delete_cards,
    '-textwrap': c.set_text_value_commands,
    '-textwidth': c.set_width_settings,
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
if LINUX:
    from src.completer import Completer
    tab_completion = Completer(
        tuple(chain(boolean_cmd_to_msg, cmd_to_msg_usage, no_arg_commands))
    )
else:
    from contextlib import nullcontext
    tab_completion = nullcontext


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
                print(f'{err_c}{err}')
            continue

        if cmd in boolean_cmd_to_msg:
            method = c.boolean_commands
            message, usage = boolean_cmd_to_msg[cmd], '{on|off}'
        elif cmd in required_arg_commands:
            method = required_arg_commands[cmd]
            message, usage = cmd_to_msg_usage[cmd]
        elif cmd in ('-b', '--browse'):
            anki.gui_browse_cards(query=args[1:])
            continue
        else:
            return word

        try:
            if args[1].strip('-').lower() in ('h', 'help'):
                raise IndexError
        except IndexError:  # Print help
            print(f'{YEX}{message}\n'
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
                print(f'{err_c}{err}')


def manage_dictionaries(
        query: str, dict_flags: Sequence[str], filter_flags: Sequence[str]
) -> Dictionary | None:
    first_dicts = {
        'ahd': ask_ahdictionary,
        'lexico': ask_lexico, 'l': ask_lexico,
        'idioms': ask_farlex, 'idiom': ask_farlex, 'i': ask_farlex
    }

    if dict_flags:
        dictionary = None
        for flag in dict_flags:
            dictionary = first_dicts[flag](query)
            # If we don't break out of the for loop, we can query multiple
            # dictionaries by specifying more than one dictionary flag
            if dictionary is not None:
                display_dictionary(dictionary, filter_flags)
        return dictionary
    else:
        dictionary = first_dicts[config['dict']](query)
        if dictionary is not None:
            display_dictionary(dictionary, filter_flags)
            return dictionary

    # fallback dictionary section
    if config['dict2'] == '-':
        return None

    second_dicts = {
        'ahd': ask_ahdictionary,
        'lexico': ask_lexico,
        'idioms': ask_farlex
    }
    print(f'{YEX}Querying the fallback dictionary...')
    dictionary = second_dicts[config['dict2']](query)
    if dictionary is not None:
        display_dictionary(dictionary, filter_flags)
        return dictionary
    if config['dict'] != 'idioms' and config['dict2'] != 'idioms':
        print(f"{YEX}To ask the idioms dictionary use {R}`{query} -i`")
    return None


def manage_thesauri(query: str) -> dict[str, str] | None:
    if config['thes'] == '-':
        # Calling WordNet just for the input_cycle.
        return WordNet().input_cycle()
    else:
        thesaurus = ask_wordnet(
            query.split()[0] if 'also' in query.split() else query
        )
        if thesaurus is None:
            return None

        display_dictionary(thesaurus)
        return thesaurus.input_cycle()


def save_audio_url(audio_url: str) -> str | NoReturn:
    filename = audio_url.rsplit('/', 1)[-1]
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
        print(f"{err_c}Saving audio {R}{filename}{err_c} failed\n"
              f"Current audio path: {R}{audio_path}\n"
              f"{err_c}Make sure the directory exists and try again\n")
        return ''
    except Exception:
        print(f'{err_c}Unexpected error occurred while saving audio')
        raise


def manage_audio(
        dictionary_name: str, audio_url: str, phrase: str, flags: Sequence[str]
) -> str:
    def from_diki() -> str:
        flag = ''
        for f in flags:
            if f in ('n', 'v', 'a', 'adj', 'noun', 'verb', 'adjective'):
                flag = '-' + f[0]
                break
        url = diki_audio(phrase, flag)
        return save_audio_url(url) if url else ''

    server = config['audio']
    if server == '-':
        return ''

    # Farlex has no audio, so we try to get it from diki.
    if server == 'diki' or dictionary_name == 'farlex':
        return from_diki()

    if server == 'auto' or dictionary_name == server:
        if audio_url:
            return save_audio_url(audio_url)
        print(f'{err_c}The dictionary does not have the pronunciation for {R}{phrase}\n'
              f'{YEX}Querying diki...')
        return from_diki()

    if server == 'ahd':
        audio_url = ahd_audio(phrase)
    elif server == 'lexico':
        audio_url = lexico_audio(phrase)
    else:
        assert False, 'unreachable'

    if audio_url:
        return save_audio_url(audio_url)
    return ''


def display_card(field_values: dict[str, str]) -> None:
    # field coloring
    color_of = {
        'def': def1_c, 'syn': syn_c, 'exsen': exsen_c,
        'phrase': phrase_c, 'pz': '', 'pos': pos_c,
        'etym': etym_c, 'audio': '', 'recording': '',
    }
    textwidth, _ = get_config_terminal_size()
    delimit = textwidth * HORIZONTAL_BAR
    textwidth, padding = round((textwidth - 1) * 0.92) + 1,\
                         round((textwidth - 1) * 0.04) * " "

    print(f'\n{delimit_c}{delimit}')
    for field_number, field in enumerate(config['fieldorder']):
        if field == '-':
            continue

        for line in field_values[field].split('<br>'):
            for subline in wrap_lines(line, config['textwrap'], textwidth, 0, 0):
                print(f'{color_of[field]}{padding}{subline}')

        if field_number + 1 == config['fieldorder_d']:  # d = delimitation
            print(f'{delimit_c}{delimit}')

    print(f'{delimit_c}{delimit}')


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
    print(f'{GEX}Card successfully saved to a file\n')


def parse_flags(flags: Sequence[str]) -> tuple[list[str], ...]:
    dict_flags, rec_flags, filter_flags = [], [], []
    for flag in flags:
        flag = flag.strip('-')
        if flag in ('ahd', 'i', 'idiom', 'idioms', 'farlex', 'l', 'lexico'):
            dict_flags.append(flag)
        elif flag in ('rec', 'record'):
            rec_flags.append(flag)
        else:
            filter_flags.append(flag)

    if config['fnolabel']:
        filter_flags.append('')
    if config['fsubdefs']:
        filter_flags.append('f')

    return dict_flags, rec_flags, filter_flags


def get_config_terminal_size() -> tuple[int, int]:
    term_width, term_height = get_terminal_size()
    config_width, flag = config['textwidth']

    if flag == '* auto' or config_width > term_width:
        # cmd always reports wrong width by 1 cell.
        if ON_WINDOWS_CMD:
            term_width -= 1
        return term_width, term_height
    return config_width, term_height


def display_dictionary(
        dictionary: Dictionary, filter_flags: Optional[Sequence[str]] = None
) -> None:
    if filter_flags is None:
        filter_flags = []

    dictionary.filter_contents(filter_flags)
    if not dictionary.contents:
        return

    width, height = get_config_terminal_size()
    ncols, state = config['columns']
    if state == '* auto':
        ncols = None

    if ncols == 1:
        colwidth, last_col_fill = width, 0
    else:
        colwidth, ncols, last_col_fill = dictionary.get_display_parameters(
            width,
            0.01 * height * config['colviewat'][0],
            ncols
        )

    columns = dictionary.prepare_to_print(
        colwidth, ncols, config['textwrap'], config['indent'][0]
    )
    if config['top']:
        with ClearScreen():
            dictionary.print_dictionary(columns, colwidth, last_col_fill)
    else:
        dictionary.print_dictionary(columns, colwidth, last_col_fill)


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

    dict_query, *flags = query.split(' -')
    if dict_query in ('-rec', '--record'):
        ffmpeg.capture_audio()
        return

    if '<' in dict_query and '>' in dict_query:
        searched_phrase = dict_query.split('<', 1)[-1].rsplit('>', 1)[0]
        if not searched_phrase:
            return
        sentence: Optional[str] = dict_query
    else:
        searched_phrase, sentence = dict_query, ''

    dict_flags, rec_flags, filter_flags = parse_flags(flags)
    if rec_flags:
        field_values['recording'] = ffmpeg.capture_audio(searched_phrase)

    dictionary = manage_dictionaries(searched_phrase, dict_flags, filter_flags)
    if dictionary is None:
        return

    if not config['createcards']:
        if config['thes'] == 'wordnet':
            # Use the first phrase to always make the correct query.
            # e.g. preferred -> prefer
            t = ask_wordnet(dictionary.phrases[0])
            if t is not None:
                display_dictionary(t)
        return

    if not sentence and config['pz']:
        sentence = sentence_input()
        if sentence is None:
            return

    dictionary_contents = dictionary.input_cycle()
    if dictionary_contents is None:
        return
    else:
        field_values.update(dictionary_contents)

    phrase = field_values['phrase']
    if dictionary.allow_thesaurus:
        thesaurus_content = manage_thesauri(phrase)
        if thesaurus_content is None:
            return
        else:
            field_values.update(thesaurus_content)

    field_values['audio'] = manage_audio(
        dictionary.name, field_values['audio'], phrase, flags
    )
    # Format card content.
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

    # hide phrase in content
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

    # format card content
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
        print(f'{err_c}Could not find {R}"define_all.txt"{err_c} file.\n'
              f'Create one and paste your list of queries there.')
        return None

    _, _, sep = _input.partition(' ')
    sep = sep.strip()
    if not sep:
        sep = '\n'

    with open(define_file) as f:
        lines = [x.strip().strip(sep) for x in f if x.strip().strip(sep)]

    if not lines:
        print(f'{R}"{define_file}"{err_c} file is empty.')
        return None

    for line in lines:
        for _input in line.split(sep):
            _input = _input.strip()
            if _input:
                yield _input

    print(f'{YEX}** {R}"{define_file}"{YEX} has been exhausted **\n')


def main() -> NoReturn:
    if config['audio_path'] == 'Cards_audio':
        # Providing the absolute path solves an occasional PermissionError on Windows.
        t = os.path.join(ROOT_DIR, 'Cards_audio')
        if not os.path.exists(t):
            os.mkdir(t)

    print(f'{BOLD}- Ankidodawacz v{__version__} -{DEFAULT}\n'
          'type -h for usage and configuration\n\n')

    while True:
        users_query = search_interface()
        if users_query.startswith('--define-all'):
            for query in from_define_all_file(users_query):
                main_loop(query)
        else:
            main_loop(users_query)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        print()
