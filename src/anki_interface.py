from __future__ import annotations

import json
import os
from typing import Any, Literal

from urllib3.exceptions import NewConnectionError

from src.Dictionaries.utils import http
from src.data import ROOT_DIR, config

# Module global configuration allows for hard refresh
# of saved notes without restarting the program and
# takes care of some edge cases
try:
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json')) as f:
        config_ac = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as f:
        f.write('{}')
    config_ac = {}

# fields used for Anki note recognition
AC_BASE_FIELDS = (
    # The most common field name schemes
    ('def',         'def'),
    ('syn',         'syn'),
    ('disamb',      'syn'),
    ('sent',        'sen'),
    ('zdanie',      'sen'),
    ('przykładowe', 'sen'),
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

    ('przykladowe', 'sen'),

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


class AnkiError(Exception):
    pass


INVOKE_ACTIONS = Literal[
    'addNote',
    'createModel',
    'guiBrowse',
    'guiCurrentCard',
    'modelFieldNames',
    'storeMediaFile',
]
def invoke(action: INVOKE_ACTIONS, **params: Any) -> Any:
    json_request = json.dumps(
        {'action': action, 'params': params, 'version': 6}
    ).encode()

    try:
        response = json.loads(
            http.urlopen(
                'POST',
                'http://127.0.0.1:8765',
                retries=False,
                body=json_request
            ).data.decode()
        )
    except NewConnectionError:
        raise AnkiError('Could not connect with Anki\nOpen Anki and try again.')

    err = response['error']
    if err is None:
        return response['result']

    err = err.lower()
    if err.startswith('model was not found:'):
        raise AnkiError(
            f'Could not find note: {config["-note"]}\n'
            f'To change the note use `-note {{note name}}`'
        )
    elif err.startswith('deck was not found'):
        raise AnkiError(
            f'Could not find deck: {config["-deck"]}\n'
            f'To change the deck use `-deck {{deck name}}`\n'
            f'If the deck name seems correct, change its name in Anki\n'
            f'so that it uses single spaces.'
        )
    elif err.startswith('cannot create note because it is empty'):
        raise AnkiError(
            f"First field empty.\n"
            f'Check if {config["-note"]} contains required fields\n'
            f'or if field names have been changed, use `-refresh`'
        )
    elif err.startswith('cannot create note because it is a duplicate'):
        raise AnkiError(
            'Duplicate.\n'
            'To allow duplicates use `-duplicates {on|off}`\n'
            'or change the scope of checking for them `-dupescope {deck|collection}`'
        )
    elif err.startswith('model name already exists'):
        raise AnkiError('Note with this name already exists.')
    elif err.startswith('gui review is not currently active'):
        raise AnkiError('Action available only in review mode.')
    elif err.startswith(('collection is not available', "'nonetype' object has no attribute")):
        raise AnkiError('Check if Anki is fully open.')
    else:
        raise Exception(response['error'])


def save_ac_config(c: dict[str, str | int | tuple[str, int]]) -> None:
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as f:
        json.dump(c, f, indent=2)


def cache_current_note(*, refresh: bool = False) -> None:
    model_name = config['-note']

    # Tries to recognize familiar fields and arranges them.
    for field_name in invoke('modelFieldNames', modelName=model_name):
        first_word_of_field_name = field_name.lower().partition(' ')[0]
        for scheme, base in AC_BASE_FIELDS:
            if scheme in first_word_of_field_name:
                config_ac[model_name] = {field_name: base}
                save_ac_config(config_ac)
                return

    if not refresh:
        raise AnkiError(
            f'Check if the note "{model_name}" contains required fields\n'
            f'or if its field names have been changed, use `-refresh`',
        )


def refresh_cached_notes() -> None:
    global config_ac
    config_ac = {}

    try:
        cache_current_note(refresh=True)
    except AnkiError:
        try:
            save_ac_config(config_ac)
        except FileNotFoundError:
            raise AnkiError('The "ankiconnect.json" file does not exist')


def gui_browse_cards(query: str = 'added:1') -> None:
    invoke('guiBrowse', query=query)


PHRASE_SCHEMES = [x[0] for x in AC_BASE_FIELDS if x[1] == 'phrase']
def currently_reviewed_phrase() -> str:
    for key, value in invoke('guiCurrentCard')['fields'].items():
        key = key.lower()
        for scheme in PHRASE_SCHEMES:
            if scheme in key:
                return value['value']

    raise AnkiError('Could not find the "Phrase-like" field')


def add_card_to_anki(field_values: dict[str, str]) -> str:
    note_name = config['-note']

    if note_name not in config_ac:
        cache_current_note()

    note_from_config = config_ac.get(note_name, {})
    fields_to_add = {
        anki_field_name: field_values[base]
        for anki_field_name, base in note_from_config.items()
    }
    tags = config['-tags'].lstrip('-')
    invoke('addNote',
        note={
            'deckName': config['-deck'],
            'modelName': note_name,
            'fields': fields_to_add,
            'options': {
                'allowDuplicate': config['-duplicates'],
                'duplicateScope': config['-dupescope']
             },
            'tags': tags.split(', ')
        }
    )

    return (
        f'Deck: {config["-deck"]}\n'
        f'Note: {note_name}\n'
        f'Tags: {tags}'
    )
