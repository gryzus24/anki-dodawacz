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

import json
import os
import urllib.request
from urllib.error import URLError

from src.Dictionaries.input_fields import ask_yes_no
from src.colors import R, BOLD, END, YEX, GEX, index_c, err_c
from src.commands import save_command
from src.data import ROOT_DIR, config, config_ac, AC_BASE_FIELDS, number_to_note_dict

# Module global configuration allows for hard refresh
# of saved notes without restarting the program and
# takes care of some edge cases
_config_ac = config_ac


def save_ac_config(c):
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as f:
        json.dump(c, f, indent=2)


def refresh_cached_notes():
    global _config_ac
    _config_ac = {}

    err = cache_current_note(refresh=True)
    if err is not None:
        try:
            save_ac_config(_config_ac)
        except FileNotFoundError:
            return f'Plik {R}"ankiconnect.json"{err_c.color} nie istnieje'
    print(f'{YEX.color}Notatki przebudowane')


def show_available_notes():
    print(f'{BOLD}Dostępne notatki:{END}')
    for i, note in number_to_note_dict.items():
        print(f'{index_c.color}{i} {R}{note}')
    print()


def ankiconnect_request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def invoke(action, **params):
    request_json = json.dumps(ankiconnect_request(action, **params)).encode('utf-8')

    try:
        # Using 127.0.0.1 as Windows is very slow to resolve "localhost" for some reason
        response = json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765', request_json)))
    except URLError:
        return None, '  Nie udało się nawiązać połączenia z Anki:\n' \
                     '    Otwórz Anki i spróbuj ponownie.'

    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')

    err = response['error']
    if err is None:
        return response['result'], None

    err = err.lower()
    if err.startswith('model was not found:'):
        msg = f'  Nie znaleziono notatki: {R}{config["note"]}{err_c.color}\n' \
              f'  Aby zmienić notatkę użyj: {R}-note {{nazwa notatki}}'
    elif err.startswith('deck was not found'):
        msg = f'  Nie znaleziono talii: {R}{config["deck"]}{err_c.color}\n' \
              f'  Aby zmienić talię użyj: {R}-deck {{nazwa talii}}\n' \
              f'  {err_c.color}Jeżeli nazwa talii wydaje się być prawidłowa zmień\n' \
              f'  nazwę talii w Anki, aby używała pojedynczych spacji.'
    elif err.startswith('cannot create note because it is empty'):
        msg = f'  Pierwsze pole notatki nie zostało wypełnione.\n' \
              f'  Sprawdź czy notatka {R}{config["note"]}{err_c.color} zawiera wymagane pola\n' \
              f'  lub jeżeli nazwy pól notatki były zmieniane, użyj {R}-refresh'
    elif err.startswith('cannot create note because it is a duplicate'):
        msg = f'  Duplikat.\n' \
              f'  Aby zezwolić na duplikaty użyj: {R}-duplicates {{on|off}}{err_c.color}\n' \
              f'  lub zmień zakres ich sprawdzania: {R}-dupescope {{deck|collection}}'
    elif err.startswith('model name already exists'):
        msg = '  Notatka już znajduje się w bazie notatek.'
    elif err.startswith('collection is not available'):
        msg = '  Sprawdź czy Anki jest w pełni otwarte.'
    elif err.startswith("'nonetype' object has no attribute"):
        msg = '  Sprawdź czy Anki jest w pełni otwarte.'
    else:
        raise Exception(response['error'])

    return None, msg  # error


def gui_browse_cards(query):
    q = ' '.join(query) if query else 'added:1'
    _, err = invoke('guiBrowse', query=q)
    if err is not None:
        print(f'{err_c.color}Nie udało się otworzyć wyszukiwarki kart:\n{err}\n')


def add_note_to_anki(*args, **kwargs) -> str:
    arg = args[1].lower()
    note_name = number_to_note_dict.get(arg, arg)

    try:
        with open(os.path.join(ROOT_DIR, f'notes/{note_name}.json'), 'r') as f:
            note_config = json.load(f)
    except FileNotFoundError:
        return f'Notatka {R}"{note_name}"{err_c.color} nie została znaleziona'

    model_name = note_config['modelName']
    _, err = invoke('createModel',
                    modelName=model_name,
                    inOrderFields=note_config['fields'],
                    css=note_config['css'],
                    cardTemplates=[{'Name': note_config['cardName'],
                                    'Front': note_config['front'],
                                    'Back': note_config['back']}])
    if err is not None:
        return f'{err_c.color}Notatka nie została dodana:\n{err}\n'

    print(f'{GEX.color}Notatka dodana pomyślnie')
    if ask_yes_no(f'Czy chcesz ustawić "{model_name}" jako -note?', default=True):
        save_command('note', model_name)


def cache_current_note(*, refresh=False):
    model_name = config['note']
    model_fields, err = invoke('modelFieldNames', modelName=model_name)
    if err is not None:
        return err

    # tries to recognize familiar fields and arranges them
    organized_fields = {}
    for mfield in model_fields:
        for scheme, base in AC_BASE_FIELDS:
            if scheme in mfield.lower().split(' ')[0]:
                organized_fields[mfield] = base
                break

    # So that blank notes are not saved in ankiconnect.json
    if not organized_fields:
        if refresh:
            return None
        return f'  Sprawdź czy notatka {R}{model_name}{err_c.color} zawiera wymagane pola\n' \
               f'  lub jeżeli nazwy pól aktualnej notatki zostały zmienione, wpisz {R}-refresh'

    _config_ac[model_name] = organized_fields
    save_ac_config(_config_ac)


def add_card_to_anki(field_values) -> None:
    note_name = config['note']

    # So that familiar notes aren't reorganized
    if note_name not in _config_ac:
        err = cache_current_note()
        if err is not None:
            print(f'{err_c.color}Nie udało się rozpoznać notatki:\n{err}\n')
            return None

    # When note is not found return an empty dict so that
    # there's no attribute error in the try block below
    fields_to_add = {}
    note_from_config = _config_ac.get(note_name, {})
    try:
        for anki_field_name, base in note_from_config.items():
            fields_to_add[anki_field_name] = field_values[base]
    except KeyError:  # shouldn't happen if ankiconnect.json isn't tampered with
        print(f'{err_c.color}Karta nie została dodana:\n'
              f'  Sprawdź czy notatka {R}{note_name}{err_c.color} zawiera wymagane pola\n'
              f'  lub jeżeli nazwy pól aktualnej notatki zostały zmienione, wpisz {R}-refresh\n')
        return None

    tags = config['tags'].lstrip('-')
    _, err = invoke('addNote',
                    note={
                        'deckName': config['deck'],
                        'modelName': note_name,
                        'fields': fields_to_add,
                        'options': {
                            'allowDuplicate': config['duplicates'],
                            'duplicateScope': config['dupescope']
                        },
                        'tags': tags.split(', ')
                    })
    if err is not None:
        print(f'{err_c.color}Karta nie została dodana do Anki:\n{err}\n')
        return None

    print(f'{GEX.color}Karta pomyślnie dodana do Anki\n'
          f'{YEX.color}Talia: {R}{config["deck"]}\n'
          f'{YEX.color}Notatka: {R}{note_name}\n'
          f'{YEX.color}Wykorzystane pola:')

    for anki_field_name, content in fields_to_add.items():
        if content.strip():
            print(f'- {anki_field_name}')
    print(f'{YEX.color}Etykiety: {R}{tags}\n'
          f'> podgląd: "-b"\n')
