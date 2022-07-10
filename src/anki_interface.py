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
        ankiconnect_config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as f:
        f.write('{}')
    ankiconnect_config = {}

# fields used for Anki note recognition
SCHEMA_TO_FIELD = (
    # The most common field name schemas come first.
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

PHRASE_SCHEMAS = [x[0] for x in SCHEMA_TO_FIELD if x[1] == 'phrase']


class AnkiError(Exception):
    pass


# TODO: Add typing overloads.
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


def save_ankiconnect_config() -> None:
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as f:
        json.dump(ankiconnect_config, f, indent=1)


def cache_current_note(*, ignore_errors: bool = False) -> None:
    model_name = config['-note']

    # Tries to recognize familiar fields and arranges them.
    result = {}
    for field_name in invoke('modelFieldNames', modelName=model_name):
        first_word_of_field_name = field_name.lower().partition(' ')[0]
        for scheme, base in SCHEMA_TO_FIELD:
            if scheme in first_word_of_field_name:
                result[field_name] = base
                break

    if result:
        ankiconnect_config[model_name] = result
        save_ankiconnect_config()
    elif not ignore_errors:
        raise AnkiError(
            f'Incompatible note.\n'
            f'Check if the note "{model_name}" contains required fields\n'
            f'or if its field names have been changed, use `-refresh`',
        )


def refresh_cached_notes() -> None:
    global ankiconnect_config
    ankiconnect_config = {}

    try:
        cache_current_note(ignore_errors=True)
    except AnkiError:
        try:
            save_ankiconnect_config()
        except FileNotFoundError:
            raise AnkiError('The "ankiconnect.json" file does not exist')


def gui_browse_cards(query: str = 'added:1') -> None:
    invoke('guiBrowse', query=query)


def currently_reviewed_phrase() -> str:
    for key, value in invoke('guiCurrentCard')['fields'].items():
        key = key.lower()
        for schema in PHRASE_SCHEMAS:
            if schema in key:
                return value['value']

    raise AnkiError('Could not find the "Phrase-like" field')


def add_card_to_anki(field_values: dict[str, str]) -> str:
    note_name = config['-note']

    if note_name not in ankiconnect_config:
        cache_current_note()

    note_from_config = ankiconnect_config.get(note_name, {})
    fields_to_add = {
        anki_field_name: field_values[base]
        for anki_field_name, base in note_from_config.items()
    }
    tags = config['-tags'].lstrip('-')
    invoke(
        'addNote',
        note={
            'deckName': config['-deck'],
            'modelName': note_name,
            'fields': fields_to_add,
            'options': {
                'allowDuplicate': config['-duplicates'],
                'duplicateScope': config['-dupescope']
             },
            'tags': tags.split(',')
        }
    )

    return (
        f'Deck: {config["-deck"]}\n'
        f'Note: {note_name}\n'
        f'Tags: {tags}'
    )
