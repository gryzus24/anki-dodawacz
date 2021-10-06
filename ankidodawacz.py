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
from notes.notes import available_notes
from src.Dictionaries.ahdictionary import AHDictionary
from src.Dictionaries.dictionary_base import request_session
from src.Dictionaries.diki import get_audio_from_diki
from src.Dictionaries.farlex import FarlexIdioms
from src.Dictionaries.input_fields import sentence_input
from src.Dictionaries.lexico import Lexico
from src.Dictionaries.wordnet import WordNet
from src.colors import \
    R, BOLD, END, YEX, GEX, \
    err_c, input_c, inputtext_c
from src.data import config

if sys.platform.startswith('linux'):
    # For saving command history, this module doesn't work on windows
    import readline
    readline.read_init_file()


commands = {
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
    '-dict': c.set_text_value_commands,
    '-dict2': c.set_text_value_commands,
    '-thes': c.set_text_value_commands,
    '-dupescope': c.set_text_value_commands,
    '-audio': c.set_text_value_commands,
    '-recqual': c.set_text_value_commands,
    '--add-note': anki.create_note,
    '--field-order': c.change_field_order, '-fo': c.change_field_order,
    '-color': c.set_colors, '-c': c.set_colors,
    '-cd': c.config_defaults,
}
no_arguments_commands = {
    '--audio-device': ffmpeg.set_audio_device, '-device': ffmpeg.set_audio_device,
    '-refresh': anki.refresh_notes,
    '--help': h.quick_help, '-help': h.quick_help, '-h': h.quick_help,
    '--help-bulk': h.bulk_help, '--help-defaults': h.bulk_help,
    '--help-commands': h.commands_help, '--help-command': h.commands_help,
    '--help-recording': h.recording_help,
    '-config': c.print_config_representation, '-conf': c.print_config_representation
}


def search_interface() -> str:
    while True:
        word = input(f'{input_c.color}Szukaj ${inputtext_c.color} ').strip()
        if not word:
            continue

        if word in no_arguments_commands:
            no_arguments_commands[word]()
            continue

        args = word.split()
        cmd = args[0]
        if cmd in tuple(data.command_help)[:24]:
            method = c.boolean_commands
            message = data.command_help[cmd]
            usage = '{on|off}'
        elif cmd in commands:
            method = commands[cmd]
            message, usage = data.command_help[cmd]
        else:
            return word

        try:
            first_arg = args[1].lower()
            if first_arg.lstrip('-') in ('h', 'help'):
                raise IndexError

        except IndexError:  # Print help
            print(f'{YEX.color}{message}\n'
                  f'{R}{cmd} {usage}')

            # Print additional information
            if cmd in ('-ap', '--audio-path'):
                print(f'{BOLD}Aktualna ścieżka:\n'
                      f'{END}{config["audio_path"]}\n')
            elif cmd == '--add-note':
                print(f'{BOLD}Dostępne notatki:{END}\n'
                      f'{", ".join(available_notes)}\n')
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


def save_audio(audio_link, audiofile_name):
    try:
        with open(os.path.join(config['audio_path'], audiofile_name), 'wb') as file:
            response = request_session.get(audio_link)
            file.write(response.content)
        return f'[sound:{audiofile_name}]'
    except FileNotFoundError:
        print(f"{err_c.color}Zapisywanie pliku audio {R}{audiofile_name} {err_c.color}nie powiodło się\n"
              f"Aktualna ścieżka zapisu audio to {R}{config['audio_path']}\n"
              f"{err_c.color}Upewnij się, że taki folder istnieje i spróbuj ponownie\n")
        return ''
    except Exception:
        print(f'{err_c.color}Wystąpił nieoczekiwany błąd podczas zapisywania audio')
        raise


def get_flag_from(flags):
    available_flags = (
        'n', 'v', 'adj', 'noun', 'verb', 'adjective'
    )
    try:
        flag = [x for x in flags if x in available_flags][0]
    except IndexError:
        return ''
    else:
        print(flag)


def manage_audio(dictionary, *flags):
    server = config['audio']
    if server == '-':
        return ''

    _phrase = dictionary.chosen_phrase
    if server == 'auto' or dictionary.name == server:
        audio_url, audiofile_name = dictionary.get_audio()
    elif server == 'ahd':
        audio_url, audiofile_name = AHDictionary().get_audio(_phrase)
    elif server == 'lexico':
        audio_url, audiofile_name = Lexico().get_audio(_phrase.replace(' ', '_'))
    else:  # diki
        flag = get_flag_from(flags)
        audio_url, audiofile_name = get_audio_from_diki(_phrase, flag)

    if not audiofile_name:
        return ''
    return save_audio(audio_url, audiofile_name)


def save_card_to_file(field_vals):
    # replace sensitive characters with hard coded html escapes
    field_values = {key: val.replace("'", "&#39;").replace('"', '&quot;')
                    for key, val in field_vals.items()}
    try:
        with open('karty.txt', 'a', encoding='utf-8') as twor:
            twor.write(f'{field_values[config["fieldorder"]["1"]]}\t'
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
        'ahd': AHDictionary,
        'lexico': Lexico, 'l': Lexico,
        'idioms': FarlexIdioms, 'idiom': FarlexIdioms, 'i': FarlexIdioms
    }

    dictionary = None
    if flags:
        for f in flags:
            try:
                dict_to_call = first_dicts[f]
            except KeyError:
                continue
            else:
                dictionary = dict_to_call().get_dictionary(_phrase, flags=flags)
                if dictionary is None:
                    return None

    if dictionary is None:
        dictionary = first_dicts[config['dict']]().get_dictionary(_phrase, flags=flags)

    if dictionary is not None:
        return dictionary

    second_dicts = {
        'ahd': AHDictionary,
        'lexico': Lexico,
        'idioms': FarlexIdioms,
        '-': None
    }
    dict_to_call = second_dicts[config['dict2']]
    if dict_to_call is None:
        return None
    print(f'{YEX.color}Szukam w drugim słowniku...')
    return dict_to_call().get_dictionary(_phrase, flags=flags)


def main():
    if not os.path.exists('Karty_audio') and config['audio_path'] == 'Karty_audio':
        os.mkdir('Karty_audio')

    __version__ = 'v1.0.1-1'
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
            'sentence_audio': ''
        }

        link_word = search_interface()
        phrase, *flags = link_word.split(' -')
        flags = [x.strip('-') for x in flags]

        if phrase in ('-rec', '--record'):
            ffmpeg.capture_audio()
            continue

        if 'rec' in flags or 'record' in flags:
            sentence_audio = ffmpeg.capture_audio(phrase)
        else:
            sentence_audio = ''

        dictionary = manage_dictionaries(phrase, flags)
        if dictionary is None:
            continue
        # temporarily set phrase to the first element from phrases
        # to always get the correct query, e.g. preferred -> prefer
        phrase = dictionary.phrases[0]

        if not config['createcards']:
            WordNet().get_thesaurus(phrase)
            continue

        zdanie = sentence_input()
        if zdanie is None:
            continue
        if config['upz']:
            zdanie.hide(phrase)

        dictionary_contents = dictionary.input_cycle()
        if dictionary_contents is None:
            continue

        phrase = dictionary.chosen_phrase
        audio = manage_audio(dictionary, flags)

        thesaurus_contents = {'synonimy': ''}
        if dictionary.allow_thesaurus:
            thesaurus = WordNet().get_thesaurus(phrase)
            if thesaurus is not None:
                thesaurus_contents = thesaurus.input_cycle()
                if thesaurus_contents is None:
                    continue

        field_values = {
            **field_values, **thesaurus_contents, **dictionary_contents,
            'zdanie': zdanie.content, 'audio': audio, 'sentence_audio': sentence_audio
        }

        if config['displaycard']:
            if dictionary.display_card(field_values) == 1:
                continue
        print()

        if config['ankiconnect']:
            anki.add_card(field_values)
        if config['savecards']:
            save_card_to_file(field_values)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        # R so that color from "inputtext" isn't displayed
        print(f'{R}\nUnicestwiony')
