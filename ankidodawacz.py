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

import os
import os.path
import sys

import src.anki_interface as anki
import src.commands as c
import src.data as data
import src.ffmpeg_interface as ffmpeg
import src.help as h
from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.audio_dictionaries import ahd_audio, lexico_audio, diki_audio, save_audio
from src.Dictionaries.farlex import ask_farlex
from src.Dictionaries.input_fields import sentence_input, ChosenElement
from src.Dictionaries.lexico import ask_lexico
from src.Dictionaries.wordnet import ask_wordnet
from src.colors import \
    R, BOLD, END, YEX, GEX, err_c
from src.data import config

if sys.platform.startswith('linux'):
    # For saving command history, this module doesn't work on windows
    import readline
    readline.read_init_file()

__version__ = 'v1.1.1-1'

required_arg_commands = {
    # commands that take arguments
    '--delete-last': c.delete_cards, '--delete-recent': c.delete_cards,
    '-textwrap': c.set_text_value_commands,
    '-textwidth': c.set_width_settings,
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
    '--add-note': anki.add_note_to_anki,
    '--field-order': c.change_field_order, '-fo': c.change_field_order,
    '-color': c.set_colors, '-c': c.set_colors,
    '-cd': c.config_defaults,
}
no_arg_commands = {
    '--audio-device': ffmpeg.set_audio_device,
    '-refresh': anki.refresh_cached_notes,
    '--help': h.quick_help, '-help': h.quick_help, '-h': h.quick_help,
    '--help-bulk': h.bulk_help,
    '--help-commands': h.commands_help, '--help-command': h.commands_help,
    '--help-recording': h.recording_help,
    '-config': c.print_config_representation, '-conf': c.print_config_representation
}


def search_interface() -> str:
    while True:
        word = input('Szukaj $ ').strip()
        if not word:
            continue

        args = word.split()
        cmd = args[0]
        if cmd in no_arg_commands:
            err = no_arg_commands[cmd]()
            if err is not None:
                print(f'{err_c.color}{err}')
            continue

        if cmd in tuple(data.command_to_help_dict)[:25]:
            method = c.boolean_commands
            message, usage = data.command_to_help_dict[cmd], '{on|off}'
        elif cmd in required_arg_commands:
            method = required_arg_commands[cmd]
            message, usage = data.command_to_help_dict[cmd]
        elif cmd in ('-b', '--browse'):
            anki.gui_browse_cards(query=args[1:])
            continue
        else:
            return word

        try:
            if args[1].strip('-').lower() in ('h', 'help'):
                raise IndexError
        except IndexError:  # Print help
            print(f'{YEX.color}{message}\n'
                  f'{R}{cmd} {usage}')

            # Print additional information
            if cmd in ('-ap', '--audio-path'):
                print(f'{BOLD}Aktualna ścieżka:\n'
                      f'{END}{config["audio_path"]}\n')
            elif cmd == '--add-note':
                anki.show_available_notes()
            elif cmd in ('-fo', '--field-order'):
                c.display_field_order()
            elif cmd in ('-c', '-color'):
                c.color_command()
            elif cmd == '-cd':
                print(f'{BOLD}Dostępne elementy:{END}\n'
                      f'def, exsen, pos, etym, syn, all\n')
        else:
            err = method(*args, message=message)
            if err is not None:
                print(f'{err_c.color}{err}')


def diki_flags(flags):
    for flag in flags:
        if flag in ('n', 'v', 'adj', 'noun', 'verb', 'adjective'):
            return flag
    return ''


def manage_audio(dictionary, flags):
    server = config['audio']
    if server == '-':
        return ''

    _phrase = dictionary.chosen_phrase
    if server == 'auto' or dictionary.name == server:
        audio_url, audiofile_name = dictionary.get_audio()
    elif server == 'ahd':
        audio_url, audiofile_name = ahd_audio(_phrase)
    elif server == 'lexico':
        audio_url, audiofile_name = lexico_audio(_phrase)
    else:  # diki
        audio_url, audiofile_name = diki_audio(_phrase, diki_flags(flags))

    if not audiofile_name:
        return ''
    return save_audio(audio_url, audiofile_name)


def save_card_to_file(field_values):
    try:
        with open('karty.txt', 'a', encoding='utf-8') as f:
            f.write(f'{field_values[config["fieldorder"]["1"]]}\t'
                    f'{field_values[config["fieldorder"]["2"]]}\t'
                    f'{field_values[config["fieldorder"]["3"]]}\t'
                    f'{field_values[config["fieldorder"]["4"]]}\t'
                    f'{field_values[config["fieldorder"]["5"]]}\t'
                    f'{field_values[config["fieldorder"]["6"]]}\t'
                    f'{field_values[config["fieldorder"]["7"]]}\t'
                    f'{field_values[config["fieldorder"]["8"]]}\t'
                    f'{field_values[config["fieldorder"]["9"]]}\n')
    except (NameError, KeyError):
        print(f'{err_c.color}Dodawanie karty do pliku nie powiodło się\n'
              f'Spróbuj przywrócić domyślne ustawienia pól wpisując {R}-fo default\n')
    else:
        print(f'{GEX.color}Karta pomyślnie zapisana do pliku\n')


def manage_dictionaries(_phrase, flags):
    first_dicts = {
        'ahd': ask_ahdictionary,
        'lexico': ask_lexico, 'l': ask_lexico,
        'idioms': ask_farlex, 'idiom': ask_farlex, 'i': ask_farlex
    }

    dictionary = None
    if flags:
        for f in flags:
            try:
                dict_to_call = first_dicts[f]
            except KeyError:
                continue
            else:
                # If we don't break out of the for loop, we can query multiple
                # dictionaries by specifying more than one dictionary flag
                dictionary = dict_to_call(_phrase, flags=flags)
                if dictionary is None:
                    return None

    if dictionary is None:
        dictionary = first_dicts[config['dict']](_phrase, flags=flags)

    if dictionary is not None:
        return dictionary

    second_dicts = {
        'ahd': ask_ahdictionary,
        'lexico': ask_lexico,
        'idioms': ask_farlex,
        '-': None
    }
    dict_to_call = second_dicts[config['dict2']]
    if dict_to_call is not None:
        print(f'{YEX.color}Szukam w drugim słowniku...')
        return dict_to_call(_phrase, flags=flags)


def format_definitions(definitions):
    styles = (
        ('<span style="opacity: 1;">', '</span>'),
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


def main():
    if not os.path.exists('Karty_audio') and config['audio_path'] == 'Karty_audio':
        os.mkdir('Karty_audio')

    print(f'{BOLD}- Dodawacz kart do Anki {__version__} -{END}\n'
          'Wpisz "--help", aby wyświetlić pomoc\n\n')

    while True:
        field_values = {
            'definicja': '',
            'synonimy': '',
            'przyklady': '',
            'phrase': '',
            'zdanie': '',
            'czesci_mowy': '',
            'etymologia': '',
            'audio': '',
            'recording': ''
        }

        link_word = search_interface()
        search_query, *flags = link_word.split(' -')
        flags = [x.strip('-') for x in flags]

        if search_query in ('-rec', '--record'):
            ffmpeg.capture_audio()
            continue

        if '<' in search_query and '>' in search_query:
            phrase = search_query.split('<', 1)[-1].rsplit('>', 1)[0]
            if not phrase:
                continue
            zdanie = ChosenElement(search_query)
        else:
            phrase, zdanie = search_query, ChosenElement()

        if 'rec' in flags or 'record' in flags:
            recording = ffmpeg.capture_audio(phrase)
        else:
            recording = ''

        dictionary = manage_dictionaries(phrase, flags)
        if dictionary is None:
            continue
        # temporarily set phrase to the first element from phrases
        # to always get the correct query, e.g. preferred -> prefer
        phrase = dictionary.phrases[0]

        if not config['createcards']:
            ask_wordnet(phrase)
            continue

        if not zdanie:  # If the phrase wasn't passed with the sentence
            zdanie = sentence_input()
            if zdanie is None:
                continue

        if config['upz']:
            zdanie.hide(phrase)
        zdanie = zdanie.content

        dictionary_contents = dictionary.input_cycle()
        if dictionary_contents is None:
            continue

        phrase = dictionary.chosen_phrase
        audio = manage_audio(dictionary, flags)

        thesaurus_contents = {'synonimy': ''}
        if dictionary.allow_thesaurus:
            thesaurus = ask_wordnet(phrase)
            if thesaurus is not None:
                thesaurus_contents = thesaurus.input_cycle()
                if thesaurus_contents is None:
                    continue

        # populate fields
        field_values = {
            **field_values, **thesaurus_contents, **dictionary_contents,
            'phrase': phrase, 'audio': audio, 'recording': recording
        }
        if zdanie:
            field_values['zdanie'] = zdanie
        else:
            if config['tsc'] != '-':
                if field_values['przyklady']:
                    field_values['zdanie'] = field_values['przyklady']
                    field_values['przyklady'] = ''
                else:
                    if config['tsc'] == 'strict':
                        field_values['zdanie'] = phrase
                        field_values['phrase'] = ''

        if config['displaycard']:
            if dictionary.display_card(field_values) == 1:
                continue
        print()

        # format card content
        for key, val in field_values.items():
            field_values[key] = val.replace("'", "&#39;").replace('"', '&quot;')

        if config['formatdefs']:
            field_values['definicja'] = format_definitions(field_values['definicja'])
        if '<br>' not in field_values['zdanie']:
            field_values['zdanie'] = field_values['zdanie']\
                .replace('>', '</b>').replace('<', '<b style="color: #91cb7d;">', 1)

        if config['ankiconnect']:
            anki.add_card_to_anki(field_values)
        if config['savecards']:
            save_card_to_file(field_values)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        raise SystemExit(print('\nUnicestwiony'))
