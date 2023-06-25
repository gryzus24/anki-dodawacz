from __future__ import annotations

import atexit
import json
import os
import sys
from typing import Any
from typing import Literal
from typing import overload
from typing import TYPE_CHECKING

from urllib3.exceptions import NewConnectionError

from src.data import config
from src.data import DATA_DIR
from src.data import LINUX
from src.data import MAC
from src.data import ROOT_DIR
from src.data import WINDOWS
from src.Dictionaries.util import http

if TYPE_CHECKING:
    from src.card import cardkey_t
    from src.card import Card

SCHEME_TO_FIELD: tuple[tuple[str, cardkey_t], ...] = (
    ('def',      'DEF'),
    ('front',    'DEF'),
    ('gloss',    'DEF'),
    ('przód',    'DEF'),
    ('przod',    'DEF'),
    ('wyjaś',    'DEF'),
    ('wyjas',    'DEF'),

    ('syn',      'SYN'),
    ('disamb',   'SYN'),
    ('usunięci', 'SYN'),
    ('usunieci', 'SYN'),
    ('ujedn',    'SYN'),

    ('exsen',    'EXSEN'),
    ('example',  'EXSEN'),
    ('usage',    'EXSEN'),
    ('przykład', 'EXSEN'),
    ('przyklad', 'EXSEN'),

    ('phrase',   'PHRASE'),
    ('target',   'PHRASE'),
    ('back',     'PHRASE'),
    ('tył',      'PHRASE'),
    ('tyl',      'PHRASE'),
    ('słowo',    'PHRASE'),
    ('slowo',    'PHRASE'),
    ('fraz',     'PHRASE'),
    ('word',     'PHRASE'),
    ('vocab',    'PHRASE'),
    ('idiom',    'PHRASE'),

    ('pos',      'POS'),
    ('part',     'POS'),
    ('części',   'POS'),
    ('czesci',   'POS'),

    ('etym',     'ETYM'),

    ('audio',    'AUDIO'),
    ('wymow',    'AUDIO'),
    ('pron',     'AUDIO'),
    ('media',    'AUDIO'),
)

PHRASE_SCHEMES = [x[0] for x in SCHEME_TO_FIELD if x[1] == 'PHRASE']


class AnkiError(Exception):
    pass

class FirstFieldEmptyError(AnkiError):
    pass

class IncompatibleModelError(AnkiError):
    pass

class ModelExistsError(AnkiError):
    pass


INVOKE_ACTIONS = Literal[
    'addNote',
    'createModel',
    'deckNames',
    'guiBrowse',
    'guiCurrentCard',
    'modelFieldNames',
    'modelNames',
]
# Overloads are added on an as-needed basis, some
# signatures are just too complex to bother typing them.
@overload
def invoke(action: Literal['deckNames', 'modelFieldNames', 'modelNames'], **params: Any) -> list[str]: ...
@overload
def invoke(action: Literal['guiBrowse'], **params: Any) -> list[int]: ...
@overload
def invoke(action: Literal['addNote'], **params: Any) -> int: ...
@overload
def invoke(action: Literal['createModel', 'guiCurrentCard'], **params: Any) -> Any: ...


def invoke(action: INVOKE_ACTIONS, **params: Any) -> Any:
    json_request = json.dumps(
        {'action': action, 'params': params, 'version': 6}
    ).encode()

    try:
        response = json.loads(
            http.urlopen(  # type: ignore[no-untyped-call]
                'POST',
                'http://127.0.0.1:8765',
                retries=False,
                body=json_request
            ).data.decode()
        )
    except NewConnectionError:
        raise AnkiError('could not connect with Anki')

    err = response['error']
    if err is None:
        return response['result']

    err = err.lower()
    if err.startswith('model was not found:'):
        raise AnkiError('could not find note: ' + config['note'])

    elif err.startswith('deck was not found'):
        raise AnkiError('could not find deck: ' + config['deck'])

    elif err.startswith('cannot create note because it is empty'):
        raise FirstFieldEmptyError('first field empty')

    elif err.startswith('cannot create note because it is a duplicate'):
        raise AnkiError('card is a duplicate')

    elif err.startswith('model name already exists'):
        raise ModelExistsError('note with this name already exists')

    elif err.startswith('gui review is not currently active'):
        raise AnkiError('action available only in review mode')

    elif err.startswith(('collection is not available', "'nonetype' object has no attribute")):
        raise AnkiError('could not connect with Anki')

    else:
        raise Exception(response['error'])


def currently_reviewed_phrase() -> str:
    for key, value in invoke('guiCurrentCard')['fields'].items():
        key = key.lower()
        for scheme in PHRASE_SCHEMES:
            if scheme in key:
                return value['value']

    raise AnkiError('could not find a "Phrase-like" field')


def _map_scheme_to_fields(model_name: str) -> dict[str, cardkey_t | None]:
    result: dict[str, cardkey_t | None] = {}
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
        self._model_cache: dict[str, dict[str, cardkey_t | None]] | None = None

    def _save_models(self, path: str) -> None:
        with open(path, 'w') as f:
            json.dump(self._model_cache, f, indent=2)

    def get_model(self,
            model: str,
            recheck: bool = False
    ) -> dict[str, cardkey_t | None]:
        if self._model_cache is None:
            path = os.path.join(DATA_DIR, 'ankiconnect.json')
            try:
                with open(path) as f:
                    self._model_cache = json.load(f)
            except FileNotFoundError:
                self._model_cache = {}
            atexit.register(self._save_models, path)

        if recheck or model not in self._model_cache:
            self._model_cache[model] = _map_scheme_to_fields(model)

        return self._model_cache[model]


models = _AnkiModels()


def _add_card(model_name: str, card: Card, model: dict[str, cardkey_t | None]) -> int:
    fields = {
        anki_field_name: card[ckey]
        for anki_field_name, ckey in model.items()
        if ckey is not None
    }
    if not fields:
        raise IncompatibleModelError(f'note {config["note"]} has no compatible fields, try rechecking (F4)')

    return invoke(
        'addNote',
        note={
            'deckName': config['deck'],
            'modelName': model_name,
            'fields': fields,
            'options': {
                'allowDuplicate': config['duplicates'],
                'duplicateScope': config['dupescope']
            },
            'tags': config['tags'].split(',')
        }
    )


def add_card(card: Card) -> int:
    model_name = config['note']

    try:
        return _add_card(model_name, card, models.get_model(model_name))
    except (FirstFieldEmptyError, IncompatibleModelError):
        # If the user renamed the fields with wrong names to good names
        # and then forgot to recheck, we can save it.
        return _add_card(model_name, card, models.get_model(model_name, recheck=True))


def add_custom_note(note_name: str) -> str:
    with open(os.path.join(ROOT_DIR, note_name)) as f:
        note_config = json.load(f)

    invoke(
        'createModel',
        modelName=note_config['modelName'],
        inOrderFields=note_config['fields'],
        css=note_config['css'],
        cardTemplates=[{
            'Name': note_config['cardName'],
            'Front': note_config['front'],
            'Back': note_config['back']
        }]
    )

    return note_config['modelName']


def collection_media_paths() -> list[str]:
    if WINDOWS:
        initial_path = os.path.join(os.environ['APPDATA'], 'Anki2')
    elif LINUX:
        initial_path = os.path.join(os.environ['HOME'], '.local/share/Anki2')
    elif MAC:
        initial_path = os.path.join(os.environ['HOME'], 'Library/Application Support/Anki2')
    else:
        raise ValueError(f'I have no idea where to look for collection.media on {sys.platform}')

    try:
        anki_directory_listing = os.listdir(initial_path)
    except FileNotFoundError:
        raise ValueError('directory with Anki data does not exist')

    result = []
    for file in anki_directory_listing:
        next_file = os.path.join(initial_path, file)
        if os.path.isdir(next_file) and 'collection.media' in os.listdir(next_file):
            result.append(os.path.join(next_file, 'collection.media'))

    if not result:
        raise ValueError('no collection.media paths found')

    return result
