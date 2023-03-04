from __future__ import annotations

import threading
from typing import Callable
from typing import NamedTuple
from typing import TYPE_CHECKING

from src.data import config
from src.data import dictkey_t
from src.Dictionaries.ahd import ask_ahd
from src.Dictionaries.base import Dictionary
from src.Dictionaries.base import DictionaryError
from src.Dictionaries.collins import ask_collins
from src.Dictionaries.farlex import ask_farlex
from src.Dictionaries.wordnet import ask_wordnet

if TYPE_CHECKING:
    from src.Curses.proto import StatusInterface

QUERY_SEPARATOR = ','

DICT_KEY_ALIASES: dict[str, dictkey_t] = {
    'ahd':     'ahd',
    'col':     'collins',
    'collins': 'collins',
    'i':       'farlex',
    'farlex':  'farlex',
    'wnet':    'wordnet',
    'wordnet': 'wordnet',
}

# Every dictionary has its individual key to avoid cluttering cache
# with identical dictionaries that were called with the same query
# but different "dictionary flag", which acts as nothing more but
# an alias.
DICTIONARY_LOOKUP: dict[dictkey_t, Callable[[str], Dictionary]] = {
    'ahd': ask_ahd,
    'farlex': ask_farlex,
    'wordnet': ask_wordnet,
    'collins': ask_collins,
}

_cache: dict[tuple[dictkey_t, str], Dictionary] = {}
def _query(key: dictkey_t, query: str) -> Dictionary:
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


def _qthread(
        query: str,
        key: dictkey_t,
        keyid: int,
        success: dict[int, Dictionary],
        err: dict[int, QueryError]
) -> None:
    try:
        success[keyid] = _query(key, query)
    except (DictionaryError, ConnectionError) as e:
        err[keyid] = QueryError(key, str(e))


def _perror_threaded_query(
        status: StatusInterface,
        query: str,
        keys: list[dictkey_t]
) -> list[Dictionary] | None:
    success: dict[int, Dictionary] = {}
    err: dict[int, QueryError] = {}
    threads = []
    for keyid, key in enumerate(keys):
        try:
            success[keyid] = _cache[key, query]
        except KeyError:
            # I hope it's ok to make them daemonic. It simplifies the handling
            # of SIGINT, but try-finally blocks don't run inside of urllib3.
            t = threading.Thread(
                target=_qthread,
                args=(query, key, keyid, success, err),
                daemon=True
            )
            t.start()
            threads.append(t)

    for t in threads:
        t.join()

    result = []
    for keyid, _ in enumerate(keys):
        if keyid in success:
            result.append(success[keyid])
        elif keyid in err:
            status.error(err[keyid].info)
        else:
            raise AssertionError('unreachable')

    if not result:
        return None

    return result


class Query(NamedTuple):
    query:       str
    dict_flags:  list[dictkey_t]
    query_flags: list[str]


def _perror_query(
        status: StatusInterface,
        query: str,
        key: dictkey_t
) -> list[Dictionary] | None:
    try:
        return [_query(key, query)]
    except (DictionaryError, ConnectionError) as e:
        status.error(str(e))
        return None


def _perror_query_with_fallback(
        status: StatusInterface,
        query: str,
        key: dictkey_t,
        fallback_key: dictkey_t
) -> list[Dictionary] | None:
    result = _perror_query(status, query, key)
    if result is None:
        result = _perror_query(status, query, fallback_key)

    return result


def parse(s: str) -> list[Query] | None:
    to_strip = QUERY_SEPARATOR + ' '

    s = s.strip(to_strip)
    if not s:
        return None
    s = ' '.join(s.split())

    result = []
    for field in s.split(QUERY_SEPARATOR):
        field = field.strip(to_strip)
        if not field:
            continue

        query, *flags = field.split(' -')

        dict_flags: list[dictkey_t] = []
        query_flags = []
        for flag in flags:
            flag = flag.strip(' -')
            if not flag:
                continue

            if flag in DICT_KEY_ALIASES:
                dict_flags.append(DICT_KEY_ALIASES[flag])
            elif flag in ('c', 'compare'):
                dict_flags.append(config['primary'])

                # `secondary` might be set to '-'. Do the membership check.
                if config['secondary'] in DICTIONARY_LOOKUP:
                    dict_flags.append(config['secondary'])  # type: ignore[arg-type]
            else:
                query_flags.append(flag)

        result.append(Query(query, list(dict.fromkeys(dict_flags)), query_flags))

    return result


def search(
        status: StatusInterface,
        queries: list[Query]
) -> list[list[Dictionary] | None]:
    # TODO: Use threads for multiple queries like "a -c, b, c" etc.
    #       We can do this by turning `_perror_threaded_query()` into a
    #       generator that yields just before `Thread.join()`, we can then
    #       collect the return values of these generators here. Keep in mind
    #       that we want to minimize the number of requests and handle
    #       duplicate queries (or disallow them) so that we can avoid the race
    #       condition when accessing the `_cache` in parallel.
    result = []
    for query, flags, _ in queries:
        if len(flags) == 0:
            if config['secondary'] == '-':
                result.append(_perror_query(status, query, config['primary']))
            else:
                result.append(
                    _perror_query_with_fallback(
                        status, query, config['primary'], config['secondary']
                    )
                )
        elif len(flags) == 1:
            result.append(_perror_query(status, query, flags.pop()))
        else:
            result.append(_perror_threaded_query(status, query, flags))

    return result
