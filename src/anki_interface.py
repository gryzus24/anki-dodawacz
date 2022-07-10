# The API offered by this module is not type safe and pretty bad.
# TODO: make it cleaner.
from __future__ import annotations

import json
import os
from typing import Any, NamedTuple

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


class AnkiResponse(NamedTuple):
    body: Any
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
            'Could not connect with Anki\n'
            'Open Anki and try again.',
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
        msg = (
            f'Could not find note: {config["-note"]}\n'
            f'To change the note use `-note {{note name}}`'
        )
    elif err.startswith('deck was not found'):
        msg = (
            f'Could not find deck: {config["-deck"]}\n'
            f'To change the deck use `-deck {{deck name}}`\n'
            f'If deck name seems correct, change its name in Anki\n'
            f'to use single spaces.'
        )
    elif err.startswith('cannot create note because it is empty'):
        msg = (
            f'First field empty.\n'
            f'Check if {config["-note"]} contains required fields\n'
            f'or if field names have been changed, use `-refresh`'
        )
    elif err.startswith('cannot create note because it is a duplicate'):
        msg = (
            f'Duplicate.\n'
            f'To allow duplicates use `-duplicates {{on|off}}`\n'
            f'or change the scope of checking for them `-dupescope {{deck|collection}}`'
        )
    elif err.startswith('model name already exists'):
        msg = 'Note with this name already exists.'
    elif err.startswith('gui review is not currently active'):
        msg = 'Action available only in review mode.'
    elif err.startswith(('collection is not available', "'nonetype' object has no attribute")):
        msg = 'Check if Anki is fully open.'
    else:
        raise Exception(response['error'])

    return AnkiResponse(msg, error=True)


def save_ac_config(c: dict[str, str | int | tuple[str, int]]) -> None:
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as f:
        json.dump(c, f, indent=2)


def cache_current_note(*, refresh: bool = False) -> AnkiResponse:
    model_name = config['-note']
    response = invoke('modelFieldNames', modelName=model_name)
    if response.error:
        return response

    # tries to recognize familiar fields and arranges them
    organized_fields = {}
    for mfield in response.body:
        for scheme, base in AC_BASE_FIELDS:
            if scheme in mfield.lower().partition(' ')[0]:
                organized_fields[mfield] = base
                break

    # So that blank notes are not saved in ankiconnect.json
    if not organized_fields:
        return AnkiResponse(
            f'Check if note {model_name} contains required fields\n'
            f'or if field names have been changed, use `-refresh`',
            error=not refresh
        )

    config_ac[model_name] = organized_fields
    save_ac_config(config_ac)

    return AnkiResponse('Note cached successfully', error=False)


def refresh_cached_notes() -> AnkiResponse:
    global config_ac
    config_ac = {}

    response = cache_current_note(refresh=True)
    if response.error:
        try:
            save_ac_config(config_ac)
        except FileNotFoundError:
            return AnkiResponse(
                '"ankiconnect.json" file does not exist',
                error=True
            )

    return AnkiResponse(f'Notes refreshed', error=False)


def gui_browse_cards(query: str = 'added:1') -> AnkiResponse:
    response = invoke('guiBrowse', query=query)
    if response.error:
        return response

    return AnkiResponse('Anki card browser opened', error=False)


def currently_reviewed_phrase() -> AnkiResponse:
    response = invoke('guiCurrentCard')
    if response.error:
        return response

    fields = response.body['fields']
    phrase_like = [x[0] for x in AC_BASE_FIELDS if x[1] == 'phrase']
    for key, value in fields.items():
        key = key.lower()
        for p in phrase_like:
            if p in key:
                return AnkiResponse(value['value'], error=False)

    return AnkiResponse('Could not find the "Phrase" field', error=True)


def add_card_to_anki(field_values: dict[str, str]) -> AnkiResponse:
    note_name = config['-note']

    # So that familiar notes aren't reorganized
    if note_name not in config_ac:
        response = cache_current_note()
        if response.error:
            return response

    note_from_config = config_ac.get(note_name, {})
    fields_to_add = {
        anki_field_name: field_values[base]
        for anki_field_name, base in note_from_config.items()
    }
    tags = config['-tags'].lstrip('-')
    response = invoke('addNote',
                      note={
                          'deckName': config['-deck'],
                          'modelName': note_name,
                          'fields': fields_to_add,
                          'options': {
                              'allowDuplicate': config['-duplicates'],
                              'duplicateScope': config['-dupescope']
                          },
                          'tags': tags.split(', ')
                      })
    if response.error:
        return response

    return AnkiResponse(
        f'Deck: {config["-deck"]}\n'
        f'Note: {note_name}\n'
        f'Tags: {tags}',
        error=False
    )
