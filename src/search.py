from __future__ import annotations

import threading
from itertools import repeat
from typing import Sequence, Iterable, NamedTuple, TYPE_CHECKING

from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.collins import ask_collins
from src.Dictionaries.dictionary_base import Dictionary, DictionaryError
from src.Dictionaries.farlex import ask_farlex
from src.Dictionaries.wordnet import ask_wordnet
from src.data import config

if TYPE_CHECKING:
    from src.Curses.proto import StatusInterface


DICT_KEY_ALIASES = {
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

_cache: dict[tuple[str, str], Dictionary] = {}
def _query(key: str, query: str) -> Dictionary:
    try:
        return _cache[key, query]
    except KeyError:
        # Lookup might raise a DictionaryError or a ConnectionError.
        # Invalid results will not be cached.
        result = DICTIONARY_LOOKUP[key](query)
        _cache[key, query] = result
        return result


class QueryError(NamedTuple):
    key:  str
    info: str


def _thread_query(
        key: str,
        query: str,
        keyid: int,
        ret: dict[int, Dictionary],
        err: dict[int, QueryError]
) -> None:
    try:
        ret[keyid] = _query(key, query)
    except (DictionaryError, ConnectionError) as e:
        err[keyid] = QueryError(key, str(e))


def _perror_no_thread_query(
        implementor: StatusInterface,
        key: str,
        query: str
) -> list[Dictionary] | None:
    try:
        return [_query(key, query)]
    except (DictionaryError, ConnectionError) as e:
        implementor.error(str(e))
        return None


def _lookup_dictionaries(
        implementor: StatusInterface,
        query: str,
        keys: Sequence[str] | None = None
) -> list[Dictionary] | None:
    keys = keys or [config['primary']]

    if len(keys) == 1:
        return _perror_no_thread_query(implementor, keys[0], query)

    success = {}
    err: dict[int, QueryError] = {}
    threads = []
    for keyid, key in enumerate(keys):
        try:
            success[keyid] = _cache[key, query]
        except KeyError:
            t = threading.Thread(
                target=_thread_query,
                args=(key, query, keyid, success, err)
            )
            t.start()
            threads.append(t)

    for t in threads:
        t.join()

    fallback_key = config['secondary']
    result = []
    for keyid, _ in enumerate(keys):
        if keyid in success:
            result.append(success[keyid])
        elif keyid in err:
            bad_key, exc_info = err[keyid]
            # Although extremely unlikely, `fallback_key` and `query` might
            # have been cached previously and can be retrieved in spite of
            # the key being invalid now.
            if fallback_key == bad_key and (fallback_key, query) not in _cache:
                fallback_key = '-'

            implementor.error(exc_info)
        else:
            raise AssertionError('unreachable')

    if result:
        return result

    if fallback_key == '-':
        return None

    return _perror_no_thread_query(implementor, fallback_key, query)


class Query(NamedTuple):
    query:       str
    dict_flags:  list[str]
    query_flags: list[str]


def _unique(it: Iterable[str]) -> list[str]:
    result = []
    seen = set()
    for x in it:
        if x not in seen:
            result.append(x)
            seen.add(x)

    return result


def search_parse(s: str) -> list[Query] | None:
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

            if flag in DICT_KEY_ALIASES:
                dict_flags.append(DICT_KEY_ALIASES[flag])
            elif flag in ('c', 'compare'):
                assert config['primary'] in DICTIONARY_LOOKUP
                dict_flags.append(config['primary'])

                # `secondary` might be set to '-'.
                if config['secondary'] in DICTIONARY_LOOKUP:
                    dict_flags.append(config['secondary'])
            else:
                query_flags.append(flag)

        result.append(Query(query, _unique(dict_flags), query_flags))

    return result


def search(
        implementor: StatusInterface,
        queries: list[Query]
) -> list[list[Dictionary] | None]:
    # To keep things simple, we only use threads in `_lookup_dictionaries()`
    # for now.
    # TODO: Use threads for multiple queries like "a -c, b, c" etc.
    #       We can easily do this by turning the `_lookup_dictionaries()` into
    #       a generator that yields just before `Thread.join()`, we can then
    #       collect the return values of these generators here. Keep in mind
    #       that we want to minimize the number of requests and handle
    #       duplicate queries (or disallow them) so that we can avoid the race
    #       condition within the `_cache`.
    return [
        _lookup_dictionaries(implementor, x.query, x.dict_flags)
        for x in queries
    ]
