from __future__ import annotations

import functools
import os
from typing import Callable
from typing import Iterable
from typing import Literal
from typing import TYPE_CHECKING
from typing import TypedDict

import src.anki as anki
from src.data import AUDIO_DIR
from src.data import config
from src.Dictionaries.base import DictionaryError
from src.Dictionaries.diki import diki_audio
from src.Dictionaries.util import http

if TYPE_CHECKING:
    from src.Curses.proto import StatusProto
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
def _format(s: str, number: int) -> str:
    try:
        left, right = FORMAT_STYLES[number - 1]
    except IndexError:
        left, right = FORMAT_STYLES[-1]
    return f'{left}<small style="color: #4EAA72;">{number}.</small> {s}{right}'


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

    phrase = selection.PHRASE.phrase
    hide_phrase_in = prepare_hide_func(phrase)
    hidedef = config['hidedef']
    hidesyn = config['hidesyn']
    hideexsen = config['hideexsen']
    formatdefs = config['formatdefs']

    definitions = []
    examples = []
    for i, op in enumerate(selection.DEF, 1):
        if op.label and ' ' not in op.label:
            definition = f'[{op.label}] {op.definition}'
        else:
            definition = op.definition
        if hidedef:
            definition = hide_phrase_in(definition)
        definition = _html_quote(definition)
        if formatdefs:
            definition = _format(definition, i)
        definitions.append(definition)

        if op.examples:
            examples.append(
                '<br>'.join(
                    f'<small>({i})</small> '
                    f'{_html_quote(hide_phrase_in(x) if hideexsen else x)}'
                    for x in op.examples
                )
            )

    if definitions:
        synonyms = [
            _html_quote(hide_phrase_in(x) if hidesyn else x)
            for x in (f'{x.definition} {x.synonyms}' for x in selection.SYN)
        ]
    else:
        synonyms = []
        for i, op in enumerate(selection.SYN, 1):
            definition = hide_phrase_in(op.definition) if hidedef else op.definition
            definition = _html_quote(definition)
            if formatdefs:
                definition = _format(definition, i)
            definitions.append(definition)

            syns = hide_phrase_in(op.synonyms) if hidesyn else op.synonyms
            syns = _html_quote(syns)
            synonyms.append(f'<small>({i})</small> {syns}')

            if op.examples:
                examples.append(
                    '<br>'.join(
                        f'<small>({i})</small> '
                        f'{_html_quote(hide_phrase_in(x) if hideexsen else x)}'
                        for x in op.examples
                    )
                )

    card['DEF'] = '<br>'.join(definitions)
    card['SYN'] = '<br>'.join(synonyms)
    card['PHRASE'] = _html_quote(phrase)
    card['EXSEN'] = '<br>'.join(examples)

    if config['pos'] and selection.POS is not None:
        card['POS'] = '<br>'.join(
            _html_quote(f'{pos}  {extra}') for pos, extra in selection.POS.pos
        )

    if config['etym'] and selection.ETYM is not None:
        card['ETYM'] = _html_quote(selection.ETYM.etymology)

    return card


def _save_audio(url: str) -> str:
    audio_bytes = http.urlopen('GET', url).data

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
        status: StatusProto,
        selection: DictionarySelection
) -> str:
    phrase = selection.PHRASE.phrase

    if selection.AUDIO is None:
        try:
            url = diki_audio(phrase)
        except DictionaryError as e:
            status.error(str(e))
            status.attention(f'No audio available for {phrase!r}')
            return ''
    else:
        url = selection.AUDIO.resource

    try:
        return _save_audio(url)
    except anki.AnkiError as e:
        status.error('Saving audio failed:', str(e))
        return ''


def create_and_add_card(
        status: StatusProto,
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
