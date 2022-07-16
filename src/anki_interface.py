from __future__ import annotations

import atexit
import json
import os
from typing import Any, Literal, overload

from urllib3.exceptions import NewConnectionError

from src.Dictionaries.utils import http
from src.data import ROOT_DIR, config

# fields used for Anki note recognition
SCHEME_TO_FIELD = (
    # The most common field name scheme.
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
    ('front', 'def'),
    ('gloss', 'def'),
    ('wyjaś', 'def'),
    ('wyjas', 'def'),

    ('usunięcie', 'syn'),
    ('usuniecie', 'syn'),
    ('ujedn',     'syn'),

    ('przyklady', 'exsen'),
    ('illust',    'exsen'),
    ('exsen',     'exsen'),

    ('back', 'phrase'),
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
)

PHRASE_SCHEMES = [x[0] for x in SCHEME_TO_FIELD if x[1] == 'phrase']


class AnkiError(Exception):
    pass


class FirstFieldEmptyError(AnkiError):
    pass


class IncompatibleModelError(AnkiError):
    pass


INVOKE_ACTIONS = Literal[
    'addNote',
    'createModel',
    'deckNames',
    'guiBrowse',
    'guiCurrentCard',
    'modelFieldNames',
    'storeMediaFile',
]
# overloads are added on an as-needed basis, some
# signatures are just too complex to bother typing them.
@overload
def invoke(action: Literal['modelFieldNames'], **params: Any) -> list[str]: ...
@overload
def invoke(action: INVOKE_ACTIONS, **params: Any) -> Any: ...


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
        raise AnkiError(
            'Could not connect with Anki.\n'
            'Check if Anki is running with Anki-Connect installed.'
        )

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
        raise FirstFieldEmptyError(
            "First field empty.\n"
            "To check what fields are assigned to your note use `--check-note`"
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


def currently_reviewed_phrase() -> str:
    for key, value in invoke('guiCurrentCard')['fields'].items():
        key = key.lower()
        for scheme in PHRASE_SCHEMES:
            if scheme in key:
                return value['value']

    raise AnkiError('Could not find the "Phrase-like" field')


def map_scheme_to_fields(model_name: str) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for field_name in invoke('modelFieldNames', modelName=model_name):
        first_word_of_field_name = field_name.lower().partition(' ')[0]
        for scheme, base in SCHEME_TO_FIELD:
            if scheme in first_word_of_field_name:
                result[field_name] = base
                break
        else:
            result[field_name] = None

    return result


class _AnkiModels:
    def __init__(self) -> None:
        self._model_cache: dict[str, dict[str, str | None]] | None = None

    @staticmethod
    def error_incompatible(model_name: str) -> str:
        return (
            f'Note {model_name!r} has no compatible fields.\n'
            f'To fix this, you can:\n'
            f'- add one of the built-in notes with `--add-note`,\n'
            f"- or rename the fields of the current note to use\n"
            f"  the supported names that are listed by `-scheme`,\n"
            f'  after renaming, use the `--check-note` command\n'
            f'  to reflect the changes in the program.'
        )

    def _save_models(self, path: str) -> None:
        with open(path, 'w') as f:
            json.dump(self._model_cache, f, indent=1)

    def get_model(self, model_name: str, refresh: bool = False) -> dict[str, str | None]:
        if self._model_cache is None:
            path = os.path.join(ROOT_DIR, 'config/ankiconnect.json')
            try:
                with open(path) as f:
                    self._model_cache = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                self._model_cache = {}
            atexit.register(self._save_models, path)

        if not refresh and model_name in self._model_cache:
            return self._model_cache[model_name]

        mapping = map_scheme_to_fields(model_name)
        self._model_cache[model_name] = mapping
        return mapping


models = _AnkiModels()


def _add_note(model_name: str, card: dict[str, str], model: dict[str, str | None]) -> None:
    fields = {k: card[v] for k, v in model.items() if v is not None}
    if not fields:
        raise IncompatibleModelError(models.error_incompatible(model_name))

    invoke(
        'addNote',
        note={
            'deckName': config['-deck'],
            'modelName': model_name,
            'fields': fields,
            'options': {
                'allowDuplicate': config['-duplicates'],
                'duplicateScope': config['-dupescope']
            },
            'tags': config['-tags'].split(',')
        }
    )


def add_card_to_anki(card: dict[str, str]) -> str:
    model_name = config['-note']

    try:
        _add_note(model_name, card, models.get_model(model_name))
    except (FirstFieldEmptyError, IncompatibleModelError):
        # If the user renamed the fields with wrong names to good names
        # and then forgot to apply the change with --check-note, we can save it.
        _add_note(model_name, card, models.get_model(model_name, refresh=True))

    return (
        f'Deck: {config["-deck"]}\n'
        f'Note: {model_name}\n'
        f'Tags: {config["-tags"]}'
    )
