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

import json
import os.path
from typing import Any, NamedTuple, Sequence

from urllib3.exceptions import NewConnectionError

from src.Dictionaries.utils import http
from src.colors import BOLD, DEFAULT, GEX, R, YEX, err_c, index_c
from src.commands import save_command
from src.data import ROOT_DIR, config
from src.input_fields import ask_yes_no, choose_item

# Module global configuration allows for hard refresh
# of saved notes without restarting the program and
# takes care of some edge cases
try:
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json')) as af:
        config_ac = json.load(af)
except (FileNotFoundError, json.JSONDecodeError):
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as af:
        af.write('{}')
    config_ac = json.loads('{}')

CUSTOM_NOTES = sorted(os.listdir(os.path.join(ROOT_DIR, 'notes')))

# fields used for Anki note recognition
AC_BASE_FIELDS = (
    # The most common field name schemes
    ('def',         'def'),
    ('syn',         'syn'),
    ('disamb',      'syn'),
    ('sent',        'pz'),
    ('zdanie',      'pz'),
    ('przykładowe', 'pz'),
    ('target',      'phrase'),
    ('phras',       'phrase'),
    ('słowo',       'phrase'),
    ('example',     'exsen'),
    ('usage',       'exsen'),
    ('przykłady',   'exsen'),
    ('part',        'pos'),
    ('pos',         'pos'),
    ('części',      'pos'),
    ('etym',        'etym'),
    ('audio',       'audio'),
    ('rec',         'recording'),
    ('nagr',        'recording'),

    # Others
    ('gloss', 'def'),
    ('wyjaś', 'def'),
    ('wyjas', 'def'),

    ('usunięcie', 'syn'),
    ('usuniecie', 'syn'),
    ('ujedn',     'syn'),

    ('przyklady', 'exsen'),
    ('illust',    'exsen'),
    ('exsen',     'exsen'),

    ('slowo', 'phrase'),
    ('fraz',  'phrase'),
    ('word',  'phrase'),
    ('vocab', 'phrase'),
    ('idiom', 'phrase'),

    ('przykladowe', 'pz'),
    ('pz',          'pz'),

    ('czesci', 'pos'),

    ('wymowa', 'audio'),
    ('pron',   'audio'),
    ('dźwięk', 'audio'),
    ('dzwiek', 'audio'),
    ('sound',  'audio'),
    ('media',  'audio'),

    ('sentence_a',    'recording'),
    ('sentenceaudio', 'recording'),
    ('sentence_r',    'recording'),
    ('sentencerec',   'recording'),
)


def save_ac_config(c: dict[str, str | int | tuple[str, int]]) -> None:
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as f:
        json.dump(c, f, indent=2)


def refresh_cached_notes() -> str | None:
    global config_ac
    config_ac = {}

    err = cache_current_note(refresh=True)
    if err is not None:
        try:
            save_ac_config(config_ac)
        except FileNotFoundError:
            return f'{R}"ankiconnect.json"{err_c} file does not exist'
    print(f'{YEX}Notes refreshed')
    return None


class AnkiResponse(NamedTuple):
    body: str
    error: bool


def invoke(action: str, **params: Any) -> AnkiResponse:
    request_json = json.dumps(
        {'action': action, 'params': params, 'version': 6}
    ).encode()

    try:
        response = json.loads(
            http.urlopen(
                'POST',
                'http://127.0.0.1:8765',
                retries=False,
                body=request_json
            ).data.decode()
        )
    except NewConnectionError:
        return AnkiResponse(
            '  Could not connect with Anki:\n'
            '    Open Anki and try again.',
            error=True)

    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')

    err = response['error']
    if err is None:
        return AnkiResponse(response['result'], error=False)

    err = err.lower()
    if err.startswith('model was not found:'):
        msg = f'  Could not find note: {R}{config["note"]}{err_c}\n' \
              f'  To change the note use {R}`-note {{note name}}`'
    elif err.startswith('deck was not found'):
        msg = f'  Could not find deck: {R}{config["deck"]}{err_c}\n' \
              f'  To change the deck use {R}`-deck {{deck name}}`\n' \
              f'  {err_c}If deck name seems correct, change its name in Anki\n' \
              f'  to use single spaces.'
    elif err.startswith('cannot create note because it is empty'):
        msg = f'  First field empty.\n' \
              f'  Check if {R}{config["note"]}{err_c} contains required fields\n' \
              f'  or if field names have been changed, use {R}`-refresh`'
    elif err.startswith('cannot create note because it is a duplicate'):
        msg = f'  Duplicate.\n' \
              f'  To allow duplicates use {R}`-duplicates {{on|off}}`{err_c}\n' \
              f'  or change the scope of checking for them {R}`-dupescope {{deck|collection}}`'
    elif err.startswith('model name already exists'):
        msg = '  Note with this name already exists.'
    elif err.startswith('collection is not available'):
        msg = '  Check if Anki is fully open.'
    elif err.startswith("'nonetype' object has no attribute"):
        msg = '  Check if Anki is fully open.'
    else:
        raise Exception(response['error'])

    return AnkiResponse(msg, error=True)


def gui_browse_cards(query: Sequence[str]) -> None:
    q = ' '.join(query) if query else 'added:1'
    response = invoke('guiBrowse', query=q)
    if response.error:
        print(f'{err_c}Could not open the card browser:\n{response.body}\n')


def add_note_to_anki() -> str | None:
    print(f'{BOLD}Available notes:{DEFAULT}')
    for i, note in enumerate(CUSTOM_NOTES, start=1):
        print(f'{index_c}{i} {R}{note[:-5]}')  # strip ".json"
    print()

    note_name = choose_item('Choose a note to add', CUSTOM_NOTES, default=0)
    if note_name is None:
        return 'Leaving...'

    with open(os.path.join(ROOT_DIR, f'notes/{note_name}')) as f:
        note_config = json.load(f)

    model_name = note_config['modelName']
    response = invoke('createModel',
                      modelName=model_name,
                      inOrderFields=note_config['fields'],
                      css=note_config['css'],
                      cardTemplates=[{'Name': note_config['cardName'],
                                      'Front': note_config['front'],
                                      'Back': note_config['back']}])
    if response.error:
        return f'{err_c}Note could not be added:\n{response.body}\n'

    print(f'{GEX}Note added successfully')
    if ask_yes_no(f'Set "{model_name}" as -note?', default=True):
        save_command('note', model_name)
    return None


def cache_current_note(*, refresh: bool = False) -> str | None:
    model_name = config['note']
    response = invoke('modelFieldNames', modelName=model_name)
    if response.error:
        return response.body

    # tries to recognize familiar fields and arranges them
    organized_fields = {}
    for mfield in response.body:
        for scheme, base in AC_BASE_FIELDS:
            if scheme in mfield.lower().split(' ')[0]:
                organized_fields[mfield] = base
                break

    # So that blank notes are not saved in ankiconnect.json
    if not organized_fields:
        if refresh:
            return None
        return f'  Check if note {R}{model_name}{err_c} contains required fields\n' \
               f'  or if field names have been changed, use {R}`-refresh`'

    config_ac[model_name] = organized_fields
    save_ac_config(config_ac)
    return None


def add_card_to_anki(field_values: dict[str, str]) -> None:
    note_name = config['note']

    # So that familiar notes aren't reorganized
    if note_name not in config_ac:
        err = cache_current_note()
        if err is not None:
            print(f'{err_c}Could not recognize note:\n{err}\n')
            return None

    # When note is not found return an empty dict so that
    # there's no attribute error in the try block below
    fields_to_add = {}
    note_from_config = config_ac.get(note_name, {})
    try:
        for anki_field_name, base in note_from_config.items():
            fields_to_add[anki_field_name] = field_values[base]
    except KeyError:  # shouldn't happen if ankiconnect.json isn't tampered with
        print(f'{err_c}Card could not be added to Anki:\n'
              f'  Check if note {R}{note_name}{err_c} contains required fields\n'
              f'  or if field names have been changed, use {R}`-refresh`\n')
        return None

    tags = config['tags'].lstrip('-')
    response = invoke('addNote',
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
    if response.error:
        print(f'{err_c}Card could not be added to Anki:\n{response.body}\n')
        return None

    print(f'{GEX}Card successfully added to Anki\n'
          f'{YEX}Deck: {R}{config["deck"]}\n'
          f'{YEX}Note: {R}{note_name}\n'
          f'{YEX}Used fields:')

    for anki_field_name, content in fields_to_add.items():
        if content.strip():
            print(f'- {anki_field_name}')
    print(f'{YEX}Tags: {R}{tags}\n'
          f'> open card browser: `-b`\n')
