from __future__ import annotations

import functools
from itertools import repeat
from typing import Sequence, NamedTuple, TYPE_CHECKING

from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.collins import ask_collins
from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.dictionary_base import DictionaryError
from src.Dictionaries.farlex import ask_farlex
from src.Dictionaries.wordnet import ask_wordnet
from src.data import config

if TYPE_CHECKING:
    from src.Curses.proto import StatusInterface


DICT_FLAG_TO_QUERY_KEY = {
    'ahd':     'ahd',
    'i':       'farlex',
    'farlex':  'farlex',
    'wnet':    'wordnet',
    'wordnet': 'wordnet',
    'collins': 'collins',
    'col':     'collins',
}
# Every dictionary has its individual key to avoid cluttering cache
# with identical dictionaries that were called with the same query
# but different "dictionary flag", which acts as nothing more but
# an alias.
DICTIONARY_LOOKUP = {
    'ahd': ask_ahdictionary,
    'farlex': ask_farlex,
    'wordnet': ask_wordnet,
    'collins': ask_collins,
}
@functools.lru_cache(maxsize=None)
def _query(key: str, query: str) -> Dictionary:
    # Lookup might raise a DictionaryError or a ConnectionError.
    # Only successful queries will be cached.
    return DICTIONARY_LOOKUP[key](query)


def _lookup_dictionaries(
        implementor: StatusInterface, query: str, flags: Sequence[str] | None = None
) -> list[Dictionary] | None:
    if flags is None or not flags:
        flags = [config['dict']]

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
                result.append(_query(key, query))
            except DictionaryError as e:
                none_keys.add(key)
                implementor.error(str(e))
            except ConnectionError as e:
                implementor.error(str(e))
                return None

    if result:
        return result

    if config['dict2'] == '-':
        return None

    fallback_key = DICT_FLAG_TO_QUERY_KEY[config['dict2']]
    if fallback_key in none_keys:
        return None

    try:
        result.append(_query(fallback_key, query))
    except (DictionaryError, ConnectionError) as e:
        implementor.error(str(e))
        return None

    return result


class Query(NamedTuple):
    query:       str
    dict_flags:  list[str]
    query_flags: list[str]


def _parse(s: str) -> list[Query] | None:
    separators = ',;'
    chars_to_strip = separators + ' '

    s = s.strip(chars_to_strip)
    if not s:
        return None

    result = []
    for field in max(map(str.split, repeat(s), separators), key=len):
        field = field.strip(chars_to_strip)
        if not field:
            continue

        query, *flags = field.split(' -')

        dict_flags = []
        query_flags = []
        for flag in flags:
            flag = flag.strip(' -')
            if not flag:
                continue

            if flag in DICT_FLAG_TO_QUERY_KEY:
                dict_flags.append(flag)
            elif flag in {'c', 'compare'}:
                d1, d2 = config['dict'], config['dict2']
                if d1 in DICT_FLAG_TO_QUERY_KEY:
                    dict_flags.append(d1)
                if d2 in DICT_FLAG_TO_QUERY_KEY:
                    dict_flags.append(d2)
            else:
                query_flags.append(flag)

        result.append(Query(query, dict_flags, query_flags))

    return result


def search(implementor: StatusInterface, s: str) -> list[Dictionary] | None:
    parsed = _parse(s)
    if parsed is None:
        return None

    dictionaries: list[Dictionary] = []
    for query in parsed:
        dicts = _lookup_dictionaries(implementor, query.query, query.dict_flags)
        if dicts is not None:
            dictionaries.extend(dicts)

    if not dictionaries:
        return None

    return dictionaries
