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

from src.colors import R, YEX, GEX, err_c
from src.commands import save_config
from src.data import ROOT_DIR, config, config_ac, ankiconnect_base_fields


def save_ac_config(c):
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as f:
        json.dump(c, f, indent=2)


def refresh_notes():
    try:
        save_ac_config({})
        organize_notes(ankiconnect_base_fields, corresp_mf_config={}, print_errors=False)
        print(f'{YEX.color}Notatki przebudowane')
    except URLError:
        return 'Nie udało się połączyć z AnkiConnect\n' \
               'Otwórz Anki i spróbuj ponownie'
    except FileNotFoundError:
        return f'Plik {R}"ankiconnect.json"{err_c.color} nie istnieje'


def create_note(*args, **kwargs) -> str:
    note_name = args[1].lower()

    try:
        with open(os.path.join(ROOT_DIR, f'notes/{note_name}.json'), 'r') as f:
            note_config = json.load(f)

        response = invoke('modelNames')
        if response == 'out of reach':
            return 'Wybierz profil, aby dodać notatkę'
    except FileNotFoundError:
        return f'Notatka {R}"{note_name}"{err_c.color} nie została znaleziona'
    except URLError:
        return 'Włącz Anki, aby dodać notatkę'

    if note_config['modelName'] in response:
        return f'{YEX.color}Notatka {R}"{note_config["modelName"]}"{YEX.color} już znajduje się w bazie notatek'

    try:
        response = invoke('createModel',
                          modelName=note_config['modelName'],
                          inOrderFields=note_config['fields'],
                          css=note_config['css'],
                          cardTemplates=[{'Name': note_config['cardName'],
                                          'Front': note_config['front'],
                                          'Back': note_config['back']}])
        if response == 'out of reach':
            raise URLError
    except URLError:
        return 'Nie można nawiązać połączenia z Anki\n' \
               'Notatka nie została utworzona'

    print(f'{GEX.color}Notatka dodana pomyślnie')

    note_ok = input(f'Czy chcesz ustawić "{note_config["modelName"]}" jako -note? [T/n]: ')
    if note_ok.lower() in ('', 't', 'y', 'tak', 'yes', '1'):
        config['note'] = note_config['modelName']
        save_config(config)


def ankiconnect_request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def invoke(action, **params):
    requestjson = json.dumps(ankiconnect_request(action, **params)).encode('utf-8')
    # Using 127.0.0.1 as Windows is very slow to resolve "localhost" for some reason
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765', requestjson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is None:
        return response['result']
    if response['error'].startswith('model was not found:'):
        return 'no note'
    if response['error'].startswith('cannot create note because it is empty'):
        return 'empty'
    if response['error'].startswith('cannot create note because it is a duplicate'):
        return 'duplicate'
    if response['error'].startswith('collection is not available'):
        return 'out of reach'
    if response['error'].startswith('deck was not found'):
        return 'no deck'
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def organize_notes(base_fields, corresp_mf_config, print_errors):
    usable_fields = invoke('modelFieldNames', modelName=config['note'])

    if usable_fields == 'no note':
        if print_errors:
            print(f'{err_c.color}Karta nie została dodana\n'
                  f'Nie znaleziono notatki {R}{config["note"]}{err_c.color}\n'
                  f'Aby zmienić notatkę użyj {R}-note [nazwa notatki]')
        return 'no note'

    if usable_fields == 'out of reach':
        if print_errors:
            print(f'{err_c.color}Karta nie została dodana\n'
                  f'Kolekcja jest nieosiągalna\n'
                  f'Sprawdź czy Anki jest w pełni otwarte')
        return 'out of reach'
    # tries to recognize familiar fields and arranges them
    for ufield in usable_fields:
        for base_field in base_fields:
            if base_field in ufield.lower().split(' ')[0]:
                corresp_mf_config[ufield] = base_fields[base_field]
                break
    # So that blank notes are not saved in ankiconnect.json
    if not corresp_mf_config:
        if print_errors:
            print(f'{err_c.color}Karta nie została dodana\n'
                  f'Sprawdź czy notatka {R}{config["note"]}{err_c.color} zawiera wymagane pola\n'
                  f'lub jeżeli nazwy pól aktualnej notatki zostały zmienione, wpisz {R}-refresh')
        return 'all fields empty'

    config_ac[config['note']] = corresp_mf_config
    save_ac_config(config_ac)


def add_card(field_values) -> None:
    try:
        corresp_model_fields = {}
        fields_ankiconf = config_ac.get(config['note'])
        # When organizing_notes returns an error, card shouldn't be created
        organize_err = None
        # So that familiar notes aren't reorganized
        if fields_ankiconf is None or config['note'] not in config_ac:
            organize_err = organize_notes(ankiconnect_base_fields, corresp_mf_config={}, print_errors=True)

        if organize_err is not None:
            return None
        # When note is not found return an empty dict so that
        # there's no attribute error in the try block below
        config_note = config_ac.get(config['note'], {})
        # Get note fields from ankiconnect.json
        try:
            for ankifield, value in config_note.items():
                corresp_model_fields[ankifield] = field_values[value]
        except KeyError:
            print(f'{err_c.color}Karta nie została dodana\n'
                  f'Sprawdź czy notatka {R}{config["note"]}{err_c.color} zawiera wymagane pola\n'
                  f'lub jeżeli nazwy pól aktualnej notatki zostały zmienione, wpisz {R}-refresh')
            return None
        # r represents card id or an error
        r = invoke('addNote',
                   note={'deckName': config['deck'],
                         'modelName': config['note'],
                         'fields': corresp_model_fields,
                         'options': {
                             'allowDuplicate': config['duplicates'],
                             'duplicateScope': config['dupescope']
                         },
                         'tags': config['tags'].replace('-', '', 1).split(', ')}
                   )
        if r == 'empty':
            print(f'{err_c.color}Karta nie została dodana\n'
                  f'Pierwsze pole notatki nie zostało wypełnione\n'
                  f'Sprawdź czy notatka {R}{config["note"]}{err_c.color} zawiera wymagane pola\n'
                  f'lub jeżeli nazwy pól aktualnej notatki zostały zmienione, wpisz {R}-refresh')
            return None
        elif r == 'duplicate':
            print(f'{err_c.color}Karta nie została dodana, bo jest duplikatem\n'
                  f'Zezwól na dodawanie duplikatów wpisując {R}-duplicates on\n'
                  f'{err_c.color}lub zmień zasięg sprawdzania duplikatów {R}-dupescope {{deck|collection}}')
            return None
        elif r == 'out of reach':
            print(f'{err_c.color}Karta nie została dodana, bo kolekcja jest nieosiągalna\n'
                  f'Sprawdź czy Anki jest w pełni otwarte')
            return None
        elif r == 'no deck':
            print(f'{err_c.color}Karta nie została dodana, bo talia {R}{config["deck"]}{err_c.color} nie istnieje\n'
                  f'Aby zmienić talię wpisz {R}-deck [nazwa talii]\n'
                  f'{err_c.color}Jeżeli nazwa talii wydaje się być prawidłowa\n'
                  f'to spróbuj zmienić nazwę talii w Anki tak,\n'
                  f'aby używała pojedynczych spacji')
            return None
        elif r == 'no note':
            print(f'{err_c.color}Karta nie została dodana\n'
                  f'Nie znaleziono notatki {R}{config["note"]}{err_c.color}\n'
                  f'Aby zmienić notatkę użyj {R}-note [nazwa notatki]')
            return None

        print(f'{GEX.color}Karta pomyślnie dodana do Anki\n'
              f'{YEX.color}Talia: {R}{config["deck"]}\n'
              f'{YEX.color}Notatka: {R}{config["note"]}\n'
              f'{YEX.color}Wykorzystane pola:')

        added_fields = (x for x in corresp_model_fields if corresp_model_fields[x].strip())
        for added_field in added_fields:
            print(f'- {added_field}')
        print(f'{YEX.color}Etykiety: {R}{config["tags"]}\n')

    except URLError:
        print(f'{err_c.color}Nie udało się połączyć z AnkiConnect\n'
              f'Otwórz Anki i spróbuj ponownie\n')
    except AttributeError:
        save_ac_config({})
        print(f'{err_c.color}Karta nie została dodana, bo plik {R}"ankiconnect.json"{err_c.color} był pusty\n'
              f'Zrestartuj program i spróbuj dodać ponownie')
