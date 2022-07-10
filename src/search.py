from __future__ import annotations

import functools
from itertools import repeat
from typing import Optional, Sequence, NamedTuple, TYPE_CHECKING

import src.ffmpeg_interface as ffmpeg
from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.dictionary_base import DictionaryError
from src.Dictionaries.dictionary_base import filter_dictionary
from src.Dictionaries.farlex import ask_farlex
from src.Dictionaries.lexico import ask_lexico
from src.Dictionaries.wordnet import ask_wordnet
from src.colors import Color
from src.data import config

if TYPE_CHECKING:
    from src.proto import WriterInterface


DICT_FLAG_TO_QUERY_KEY = {
    'ahd': 'ahd',
    'i': 'farlex', 'farlex': 'farlex',
    'l': 'lexico', 'lexico': 'lexico',
    'wnet': 'wordnet', 'wordnet': 'wordnet',
}
# Every dictionary has its individual key to avoid cluttering cache
# with identical dictionaries that were called with the same query
# but different "dictionary flag", which acts as nothing more but
# an alias.
DICTIONARY_LOOKUP = {
    'ahd': ask_ahdictionary,
    'farlex': ask_farlex,
    'lexico': ask_lexico,
    'wordnet': ask_wordnet,
}
@functools.lru_cache(maxsize=None)
def query_dictionary(key: str, query: str) -> Dictionary:
    # Lookup might raise a DictionaryError or a ConnectionError.
    # Only successful queries will be cached.
    return DICTIONARY_LOOKUP[key](query)


def get_dictionaries(
        writer: WriterInterface, query: str, flags: Optional[Sequence[str]] = None
) -> list[Dictionary] | None:
    if flags is None or not flags:
        flags = [config['-dict']]

    # Ideally `none_keys` would be static and kept throughout searches like
    # "phrase1, phrase1, phrase1", but in normal, non-malicious (źdź,źdź,źdź...),
    # usage it is never needed, because nobody really queries the same thing
    # multiple times that is also not in the dictionary.
    none_keys = set()
    result = []
    for flag in flags:
        key = DICT_FLAG_TO_QUERY_KEY[flag]
        if key not in none_keys:
            try:
                result.append(query_dictionary(key, query))
            except DictionaryError as e:
                none_keys.add(key)
                writer.writeln(str(e))
            except ConnectionError as e:
                writer.writeln(str(e))
                return None

    if result:
        return result
    if config['-dict2'] == '-':
        return None
    fallback_key = DICT_FLAG_TO_QUERY_KEY[config['-dict2']]
    if fallback_key in none_keys:
        return None

    writer.writeln(f'{Color.heed}Querying the fallback dictionary...')
    try:
        result.append(query_dictionary(fallback_key, query))
    except (DictionaryError, ConnectionError) as e:
        writer.writeln(str(e))
        return None

    return result


class Query(NamedTuple):
    query:       str
    sentence:    str
    dict_flags:  list[str]
    query_flags: list[str]
    record:      bool


class QuerySettings:
    __slots__ = 'queries', 'user_sentence', 'recording_filename'

    def __init__(self, queries: list[Query], user_sentence: str, recording_filename: str) -> None:
        self.queries = queries
        self.user_sentence = user_sentence
        self.recording_filename = recording_filename

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}('
            f'queries={self.queries!r}, '
            f'user_sentence={self.user_sentence!r}, '
            f'recording_filename={self.recording_filename!r})'
        )


def parse_query(full_query: str) -> list[Query] | None:
    separators = ',;'
    chars_to_strip = ' ' + separators

    full_query = full_query.strip(chars_to_strip)
    if not full_query:
        return None

    result = []
    for field in max(map(str.split, repeat(full_query), separators), key=len):
        field = field.strip(chars_to_strip)
        if not field:
            continue

        query, *flags = field.split(' -')
        emph_start = query.find('<')
        emph_stop = query.rfind('>')
        if ~emph_start and ~emph_stop and emph_start < emph_stop:
            sentence = (
                    query[:emph_start]
                    + '{{' + query[emph_start + 1:emph_stop] + '}}'
                    + query[emph_stop + 1:]
            )
            query = query[emph_start + 1:emph_stop]
        else:
            sentence = ''

        dict_flags = []
        query_flags = []
        record = False
        for flag in flags:
            flag = flag.strip(' -')
            if not flag:
                continue

            if flag in {'rec', 'record'}:
                record = True
            elif flag in DICT_FLAG_TO_QUERY_KEY:
                dict_flags.append(flag)
            elif flag in {'c', 'compare'}:
                d1, d2 = config['-dict'], config['-dict2']
                if d1 in DICT_FLAG_TO_QUERY_KEY:
                    dict_flags.append(d1)
                if d2 in DICT_FLAG_TO_QUERY_KEY:
                    dict_flags.append(d2)
            else:
                query_flags.append(flag)

        result.append(
            Query(query.strip(), sentence, dict_flags, query_flags, record)
        )

    return result


def search_dictionaries(writer: WriterInterface, s: str) -> tuple[list[Dictionary], QuerySettings] | None:
    parsed = parse_query(s)
    if parsed is None:
        return None

    dictionaries: list[Dictionary] = []
    recorded = False
    user_sentence = recording_filename = ''
    valid_queries = []
    for query in parsed:
        if query.sentence and not user_sentence:
            user_sentence = query.sentence
        if query.record and not recorded:
            recording_filename = ffmpeg.capture_audio(query.query)
            recorded = True

        dicts = get_dictionaries(writer, query.query, query.dict_flags)
        if dicts is not None:
            valid_queries.append(query)
            if query.query_flags:
                dictionaries.extend(
                    map(filter_dictionary, dicts, repeat(query.query_flags))
                )
            else:
                dictionaries.extend(dicts)

    if not dictionaries:
        return None

    return dictionaries, QuerySettings(valid_queries, user_sentence, recording_filename)
