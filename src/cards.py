from __future__ import annotations

import binascii
import os
from typing import Generator, Iterable, NoReturn, Optional, TYPE_CHECKING

import src.anki_interface as anki
from src.Dictionaries.audio_dictionaries import ahd_audio, diki_audio, lexico_audio
from src.Dictionaries.utils import http
from src.data import ROOT_DIR, config

if TYPE_CHECKING:
    from ankidodawacz import QuerySettings
    from src.Dictionaries.dictionary_base import Dictionary

CARD_FIELDS_SAVE_ORDER = ('def', 'syn', 'sen', 'phrase', 'exsen', 'pos', 'etym', 'audio', 'recording')
CARD_SAVE_LOCATION = os.path.join(ROOT_DIR, 'cards.txt')

PREPOSITIONS = {
    'beyond', 'of', 'outside', 'upon', 'with', 'within',
    'behind', 'from', 'like', 'opposite', 'to', 'under',
    'after', 'against', 'around', 'near', 'over', 'via',
    'among', 'except', 'for', 'out', 'since', 'through',
    'about', 'along', 'beneath', 'underneath', 'unlike',
    'below', 'into', 'on', 'onto', 'past', 'than', 'up',
    'across', 'by', 'despite', 'inside', 'off', 'round',
    'at', 'beside', 'between', 'in', 'towards', 'until',
    'above', 'as', 'before', 'down', 'during', 'without'
}


def save_card_to_file(card: dict[str, str]) -> None:
    with open(CARD_SAVE_LOCATION, 'a', encoding='UTF-8') as f:
        f.write('\t'.join(card[x] for x in CARD_FIELDS_SAVE_ORDER))
        f.write('\n')


class AnkiError(Exception):
    pass


def save_audio_url(
        url: str,
        path: Optional[str] = None,
        filename: Optional[str] = None,
        *, default_path: Optional[str] = None
) -> str | NoReturn:
    audio_content = http.urlopen('GET', url).data
    if filename is None:
        _, _, filename = url.rpartition('/')

    if path is None:
        # Use AnkiConnect to save audio files if [collection.media] path isn't given.
        # However, specifying the audio path is preferred as it's way faster.
        response = anki.invoke(
            'storeMediaFile',
            filename=filename,
            data=binascii.b2a_base64(audio_content, newline=False).decode()
        )
        if response.error:
            raise AnkiError(response.body)
        else:
            return f'[sound:{filename}]'

    try:
        with open(os.path.join(path, filename), 'wb') as file:
            file.write(audio_content)
        return f'[sound:{filename}]'
    except (FileNotFoundError, NotADirectoryError):
        if default_path is None:
            raise

        if not os.path.exists(default_path):
            os.mkdir(default_path)
        elif os.path.isfile(default_path):
            raise NotADirectoryError(f'Default path ({default_path}) is not a directory')

        with open(os.path.join(default_path, filename), 'wb') as file:
            file.write(audio_content)
        return f'[sound:{filename}]'


def add_audio_to_anki(
        audio_url: str,
        dictionary_name: str,
        phrase: str,
        flags: Optional[Iterable[str]] = None
) -> str:
    server = config['-audio']

    if audio_url:
        if server == 'auto' or dictionary_name == server:
            audio_url = audio_url
        elif server == 'ahd':
            audio_url = ahd_audio(phrase)
        elif server == 'lexico':
            audio_url = lexico_audio(phrase)
    
    if not audio_url:
        if flags is None:
            audio_url = diki_audio(phrase)
        else:
            for f in flags:
                if f in {'n', 'v', 'a', 'adj', 'noun', 'verb', 'adjective'}:
                    audio_url = diki_audio(phrase, f'-{f[0]}')
                    break
            else:
                audio_url = diki_audio(phrase)
        if not audio_url:
            return ''

    audio_path = config['audio_path']
    if config['-ankiconnect'] and os.path.basename(audio_path) != 'collection.media':
        return save_audio_url(audio_url)

    _, _, filename = audio_url.rpartition('/')
    return save_audio_url(
        audio_url, audio_path, filename, default_path=os.path.join(ROOT_DIR, 'Cards_audio')
    )


def case_replace(target: str, a: str, b: str) -> str:
    return target.replace(a, b).replace(a.capitalize(), b).replace(a.upper(), b.upper())


def hide(
        target: str,
        phrase_to_replace: str,
        mask: str = '...',
        *, hide_prepositions: bool = False,
) -> str:
    do_not_replace = {
        'the', 'and', 'a', 'is', 'an', 'it',
        'or', 'be', 'do', 'does', 'not', 'if', 'he'
    }
    words_to_replace = set(phrase_to_replace.lower().split()) - do_not_replace
    if not hide_prepositions:
        words_to_replace -= PREPOSITIONS

    for word in words_to_replace:
        target = case_replace(target, word, mask)
        if word.endswith('e'):
            target = case_replace(target, f'{word[:-1]}ing', f'{mask}ing')
            if word.endswith('ie'):
                target = case_replace(target, f'{word[:-2]}ying', f'{mask}ying')
        elif word.endswith('y'):
            target = case_replace(target, f'{word[:-1]}ies', f'{mask}ies')
            target = case_replace(target, f'{word[:-1]}ied', f'{mask}ied')

    return target


def format_definitions(definition_string: str) -> str:
    styles = (
        ('', ''),
        ('<span style="opacity: .6;">', '</span>'),
        ('<small style="opacity: .4;">', '</small>'),
        ('<small style="opacity: .2;"><sub>', '</sub></small>')
    )
    formatted = []
    style_no = len(styles)
    for i, item in enumerate(definition_string.split('<br>'), 1):
        style_i = style_no - 1 if i > style_no else i - 1
        prefix, suffix = styles[style_i]

        prefix += f'<small style="color: #4EAA72;">{i}.</small>  '
        formatted.append(prefix + item + suffix)

    return '<br>'.join(formatted)


def _map_card_fields_to_values(
        dictionary: Dictionary, definition_indices: list[int]
) -> tuple[dict[str, str], str]:
    card = {k: '' for k in CARD_FIELDS_SAVE_ORDER}
    contents = dictionary.contents
    related_entries = dictionary.static_entries_to_index_from_index(definition_indices[0])
    audio_url = ''
    for op, i in related_entries.items():
        entry = contents[i]
        if op == 'PHRASE':
            card['phrase'] = entry[1]
        elif op == 'AUDIO':
            url = entry[1]
            if url:
                audio_url = url
            else:
                unique_urls = set()
                for x in contents:
                    if x == entry:
                        break
                    if x[0] == 'AUDIO' and x[1]:
                        unique_urls.add(x[1])
                if len(unique_urls) == 1:
                    audio_url = unique_urls.pop()
        elif op == 'POS':
            card['pos'] = '<br>'.join(
                x.replace('|', '  ') for x in entry[1:]
            ).strip()
        elif op == 'ETYM':
            card['etym'] = entry[1]

    definitions, example_sentences, synonyms = [], [], []
    for def_index in definition_indices:
        entry = contents[def_index]
        op = entry[0]
        if 'DEF' in op:
            _, _def, _exsen, _label = entry
            if _label:
                definitions.append(f'{{{_label}}} {_def}')
            else:
                definitions.append(_def)
            if _exsen:
                example_sentences.append(_exsen)
        elif op == 'SYN':
            synonyms.append(entry[2] + ' ' + entry[1])

    card['def'] = '<br>'.join(definitions)
    card['exsen'] = '<br>'.join(example_sentences)
    card['syn'] = '<br>'.join(synonyms)

    return card, audio_url


def format_and_prepare_card(card: dict[str, str]) -> dict[str, str]:
    if config['-formatdefs']:
        card['def'] = format_definitions(card['def'])

    sentence = card['sen']
    sentence = sentence.replace('{{', '<b style="color: #91cb7d;">', 1)
    sentence = sentence.replace('}}', '</b>', 1)
    card['sen'] = sentence

    return {
        k: v.replace("'", "&#39;").replace('"', '&quot;') for k, v in card.items()
    }


class DictionaryError(Exception):
    pass


def cards_from_definitions(
        dictionary: Dictionary,
        grouped_by_phrase: dict[int, list[int]],
        settings: QuerySettings,
) -> Generator[tuple[dict[str, str], str | None, list[str]], None, None]:
    contents = dictionary.contents
    for phrase_index, definition_indices in grouped_by_phrase.items():
        phrase = contents[phrase_index][1]
        card, audio_url = _map_card_fields_to_values(dictionary, definition_indices)
        if not config['-exsen']:
            card['exsen'] = ''
        if not config['-pos']:
            card['pos'] = ''
        if not config['-etym']:
            card['etym'] = ''

        try:
            audio_tag = add_audio_to_anki(
                audio_url,
                dictionary.name,
                phrase,
                settings.flags_for_query(0)
            )
        except AnkiError as e:
            error = 'Could not save audio:'
            error_info = [
                *str(e).splitlines(),
                'To not rely on Anki to save audio',
                'use `-ap auto` to specify the audio save location.'
            ]
            card['audio'] = ''
        except (FileNotFoundError, NotADirectoryError) as e:
            error = 'Could not save audio:'
            error_info = str(e).splitlines()
            card['audio'] = ''
        else:
            if not audio_tag:
                error = f'No audio available for {phrase!r}'
            else:
                error = None  # type: ignore[assignment]
            error_info = []
            card['audio'] = audio_tag

        sentence = settings.user_sentence
        if sentence:
            card['sen'] = sentence
        elif config['-tsc'] != '-':
            if card['exsen']:
                card['sen'] = card['exsen']
                card['exsen'] = ''
            elif config['-tsc'] == 'strict':
                card['sen'] = phrase
                card['phrase'] = ''

        card['recording'] = settings.recording_filename

        for elem in ('sen', 'def', 'exsen', 'syn'):
            if config[f'-h{elem}']:
                card[elem] = hide(
                    card[elem], phrase, config['-hideas'],
                    hide_prepositions=config['-hpreps']
                )

        yield card, error, error_info
