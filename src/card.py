from __future__ import annotations

import functools
import os
from typing import Callable
from typing import Iterable
from typing import Literal
from typing import TYPE_CHECKING
from typing import TypedDict

import src.anki as anki
from src.data import config
from src.data import AUDIO_DIR
from src.Dictionaries.base import DictionaryError
from src.Dictionaries.diki import diki_audio
from src.Dictionaries.util import http

if TYPE_CHECKING:
    from src.Curses.proto import StatusInterface
    from src.Dictionaries.base import DictionarySelection


class Card(TypedDict):
    DEF:    str
    SYN:    str
    PHRASE: str
    EXSEN : str
    POS:    str
    ETYM:   str
    AUDIO:  str


cardkey_t = Literal['DEF', 'SYN', 'PHRASE', 'EXSEN', 'POS', 'ETYM', 'AUDIO']

DO_NOT_HIDE = frozenset((
    'the', 'and', 'a', 'is', 'an', 'it',
    'or', 'be', 'do', 'does', 'not', 'if', 'he'
))

PREPOSITIONS = frozenset((
    'beyond', 'of', 'outside', 'upon', 'with', 'within',
    'behind', 'from', 'like', 'opposite', 'to', 'under',
    'after', 'against', 'around', 'near', 'over', 'via',
    'among', 'except', 'for', 'out', 'since', 'through',
    'about', 'along', 'beneath', 'underneath', 'unlike',
    'below', 'into', 'on', 'onto', 'past', 'than', 'up',
    'across', 'by', 'despite', 'inside', 'off', 'round',
    'at', 'beside', 'between', 'in', 'towards', 'until',
    'above', 'as', 'before', 'down', 'during', 'without'
))


def _replace(s: str, a: str, b: str) -> str:
    return s.replace(a, b).replace(a.capitalize(), b).replace(a.upper(), b.upper())


def _hide(target: str, words: Iterable[str], mask: str) -> str:
    for word in words:
        target = _replace(target, word, mask)
        if word.endswith('e'):
            target = _replace(target, f'{word[:-1]}ing', f'{mask}ing')
            if word.endswith('ie'):
                target = _replace(target, f'{word[:-2]}ying', f'{mask}ying')
        elif word.endswith('y'):
            target = _replace(target, f'{word[:-1]}ies', f'{mask}ies')
            target = _replace(target, f'{word[:-1]}ied', f'{mask}ied')

    return target


def prepare_hide_func(phrase: str) -> Callable[[str], str]:
    words_to_hide = set(phrase.lower().split()) - DO_NOT_HIDE
    if not config['hidepreps']:
        words_to_hide -= PREPOSITIONS

    return functools.partial(_hide, words=words_to_hide, mask=config['hides'])


FORMAT_STYLES = (
    ('', ''),
    ('<span style="opacity: 0.6;">', '</span>'),
    ('<small style="opacity: 0.4;">', '</small>'),
    ('<small style="opacity: 0.2;"><sub>', '</sub></small>')
)
def _format(s: str, index: int, style: tuple[str, str]) -> str:
    left, right = style
    return f'{left}<small style="color: #4EAA72;">{index}.</small> {s}{right}'


def _html_quote(s: str) -> str:
    return s.replace("'", '&#39;').replace('"', '&quot;')


def make_card(selection: DictionarySelection) -> Card:
    card: Card = {
        'DEF':    '',
        'SYN':    '',
        'PHRASE': '',
        'EXSEN':  '',
        'POS':    '',
        'ETYM':   '',
        'AUDIO':  '',
    }

    phrase = selection.phrase.phrase
    hide_phrase_in = prepare_hide_func(phrase)

    definitions: list[str] = []
    examples = []
    for i, op in enumerate(selection.definitions, 1):
        if op.label:
            definition = f'{{{op.label}}} {op.definition}'
        else:
            definition = op.definition

        if config['hidedef']:
            definition = hide_phrase_in(definition)

        definition = _html_quote(definition)
        if config['formatdefs']:
            try:
                style = FORMAT_STYLES[i - 1]
            except IndexError:
                style = FORMAT_STYLES[-1]
            definition = _format(definition, i, style)

        definitions.append(definition)
        if op.examples:
            examples.append(
                '<br>'.join(
                    _html_quote(hide_phrase_in(x) if config['hideexsen'] else x)
                    for x in op.examples
                )
            )

    card['DEF'] = '<br>'.join(definitions)
    card['EXSEN'] = '<br>'.join(examples)

    card['SYN'] = '<br>'.join(
        _html_quote(hide_phrase_in(x) if config['hidesyn'] else x)
        for x in (f'{x.definition} {x.synonyms}' for x in selection.synonyms)
    )

    card['PHRASE'] = _html_quote(phrase)

    if config['pos'] and selection.pos is not None:
        card['POS'] = '<br>'.join(
            _html_quote(f'{pos}  {infl}') for pos, infl in selection.pos.pos
        )

    if config['etym'] and selection.etymology is not None:
        card['ETYM'] = _html_quote(selection.etymology.etymology)

    return card


def _save_audio(url: str) -> str:
    audio_bytes = http.urlopen('GET', url).data  # type: ignore[no-untyped-call]

    mediadir_path = os.path.expanduser(
        AUDIO_DIR if config['mediadir'] == '-' else config['mediadir']
    )
    _, _, filename = url.rpartition('/')

    try:
        with open(os.path.join(mediadir_path, filename), 'wb') as f:
            f.write(audio_bytes)
    except Exception as e:
        raise anki.AnkiError(str(e))

    return f'[sound:{filename}]'


def _perror_save_audio(
        status: StatusInterface,
        selection: DictionarySelection
) -> str:
    phrase = selection.phrase.phrase

    if selection.audio is None:
        try:
            url = diki_audio(phrase)
        except DictionaryError as e:
            status.error(str(e))
            status.attention(f'No audio available for {phrase!r}')
            return ''
    else:
        url = selection.audio.resource

    try:
        return _save_audio(url)
    except anki.AnkiError as e:
        status.error('Saving audio failed:', str(e))
        return ''


def create_and_add_card(
        status: StatusInterface,
        selections: list[DictionarySelection]
) -> list[int]:
    nids = []
    for selection in selections:
        card = make_card(selection)
        if config['audio']:
            card['AUDIO'] = _perror_save_audio(status, selection)

        try:
            nids.append(anki.add_card(card))
        except anki.AnkiError as e:
            status.error('Adding card failed:', str(e))
        else:
            status.success('Card added successfully:', 'press "b" to open in Anki')

    return nids

