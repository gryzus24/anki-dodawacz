from __future__ import annotations

import atexit
import os
import shelve
import threading
from typing import Callable
from typing import Dict
from typing import Mapping
from typing import NamedTuple
from typing import TYPE_CHECKING
from typing import Union

from src.data import DATA_DIR
from src.data import dictkey_t
from src.data import getconf
from src.Dictionaries.ahd import ask_ahd
from src.Dictionaries.base import Dictionary
from src.Dictionaries.base import DictionaryError
from src.Dictionaries.base import MAGIC
from src.Dictionaries.collins import ask_collins
from src.Dictionaries.diki import ask_diki_english
from src.Dictionaries.diki import ask_diki_french
from src.Dictionaries.diki import ask_diki_german
from src.Dictionaries.diki import ask_diki_italian
from src.Dictionaries.diki import ask_diki_spanish
from src.Dictionaries.farlex import ask_farlex
from src.Dictionaries.wordnet import ask_wordnet

if TYPE_CHECKING:
    from src.Curses.proto import StatusProto

QUERY_SEPARATOR = ','

DICT_KEY_ALIASES: Mapping[str, dictkey_t] = {
    'ahd':     'ahd',
    'col':     'collins',
    'collins': 'collins',
    'den':     'diki-en',
    'diki-en': 'diki-en',
    'dfr':     'diki-fr',
    'diki-fr': 'diki-fr',
    'dde':     'diki-de',
    'diki-de': 'diki-de',
    'dit':     'diki-it',
    'diki-it': 'diki-it',
    'des':     'diki-es',
    'diki-es': 'diki-es',
    'i':       'farlex',
    'farlex':  'farlex',
    'wnet':    'wordnet',
    'wordnet': 'wordnet',
}

# Every dictionary has its individual key to avoid cluttering cache
# with identical dictionaries that were called with the same query
# but different "dictionary flag", which acts as nothing more but
# an alias.
DICTIONARY_LOOKUP: Mapping[dictkey_t, Callable[[str], Dictionary]] = {
    'ahd': ask_ahd,
    'collins': ask_collins,
    'diki-en': ask_diki_english,
    'diki-fr': ask_diki_french,
    'diki-de': ask_diki_german,
    'diki-it': ask_diki_italian,
    'diki-es': ask_diki_spanish,
    'farlex': ask_farlex,
    'wordnet': ask_wordnet,
}

MONOLINGUAL_DICTIONARIES = [x for x in DICTIONARY_LOOKUP if 'diki' not in x]

db_t = Union[shelve.DbfilenameShelf[Dictionary], Dict[str, Dictionary]]


class _Cache:
    def __init__(self) -> None:
        self._path = os.path.join(DATA_DIR, f'dictionary_cache.{MAGIC}')
        self._db: db_t | None = None

    def _open_shelf(self) -> shelve.DbfilenameShelf[Dictionary] | None:
        try:
            # We use features from the 4th protocol at max.
            return shelve.DbfilenameShelf(self._path, protocol=4)
        except OSError:
            return None

    def _save(self) -> None:
        if self._db is None:
            return
        if isinstance(self._db, shelve.DbfilenameShelf):
            self._db.close()
        elif getconf('cachefile'):
            dbfile = self._open_shelf()
            if dbfile is not None:
                for key, dictionary in self._db.items():
                    dbfile[key] = dictionary
                dbfile.close()

    @property
    def db(self) -> tuple[db_t, bool]:
        err = False
        if self._db is None:
            if getconf('cachefile'):
                dbfile = self._open_shelf()
                if dbfile is None:
                    err = True
                    self._db = {}
                else:
                    self._db = dbfile
            else:
                self._db = {}
            atexit.register(self._save)
        elif isinstance(self._db, dict) and getconf('cachefile'):
            dbfile = self._open_shelf()
            if dbfile is None:
                err = True
            else:
                for key, dictionary in self._db.items():
                    dbfile[key] = dictionary
                self._db = dbfile

        return self._db, err


_cache = _Cache()
def _query(key: dictkey_t, query: str, db: db_t) -> Dictionary:
    try:
        return db[key + query]
    except KeyError:
        # Lookup might raise a DictionaryError or a ConnectionError.
        # Invalid results will not be cached.
        result = DICTIONARY_LOOKUP[key](query)
        db[key + query] = result
        return result


def _query_thread(
        key: dictkey_t,
        query: str,
        keyid: int,
        success: dict[int, Dictionary],
        error: dict[int, str],
        db: db_t
) -> None:
    try:
        success[keyid] = _query(key, query, db)
    except (DictionaryError, ConnectionError) as e:
        error[keyid] = str(e)


def perror_threaded_query(
        status: StatusProto,
        query: str,
        keys: list[dictkey_t],
        db: db_t
) -> list[Dictionary] | None:
    success: dict[int, Dictionary] = {}
    error: dict[int, str] = {}
    threads = []

    for keyid, key in enumerate(keys):
        try:
            success[keyid] = db[key + query]
        except KeyError:
            # I hope it's ok to make them daemonic. It simplifies the handling
            # of SIGINT, but try-finally blocks don't run inside of urllib3.
            t = threading.Thread(
                target=_query_thread,
                args=(key, query, keyid, success, error, db),
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
        elif keyid in error:
            status.error(error[keyid])
        else:
            raise AssertionError('unreachable')

    if not result:
        return None

    return result


class Query(NamedTuple):
    query:       str
    dict_flags:  list[dictkey_t]
    query_flags: list[str]


def perror_query(
        status: StatusProto,
        query: str,
        key: dictkey_t,
        db: db_t
) -> list[Dictionary] | None:
    try:
        return [_query(key, query, db)]
    except (DictionaryError, ConnectionError) as e:
        status.error(str(e))
        return None


def perror_query_with_fallback(
        status: StatusProto,
        query: str,
        key: dictkey_t,
        fallback_key: dictkey_t,
        db: db_t
) -> list[Dictionary] | None:
    result = perror_query(status, query, key, db)
    if result is None:
        result = perror_query(status, query, fallback_key, db)

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
                dict_flags.append(getconf('primary'))

                # `secondary` might be set to '-'. Do the membership check.
                if getconf('secondary') in DICTIONARY_LOOKUP:
                    dict_flags.append(getconf('secondary'))  # type: ignore[arg-type]
            elif flag == 'all':
                dict_flags.extend(MONOLINGUAL_DICTIONARIES)
            else:
                query_flags.append(flag)

        result.append(Query(query, list(dict.fromkeys(dict_flags)), query_flags))

    return result


def search(
        status: StatusProto,
        queries: list[Query]
) -> list[list[Dictionary] | None]:
    # TODO: Use threads for multiple queries like "a -c, b, c" etc.
    #       We can do this by turning `perror_threaded_query()` into a
    #       generator that yields just before `Thread.join()`, we can then
    #       collect the return values of these generators here. Keep in mind
    #       that we want to minimize the number of requests and handle
    #       duplicate queries (or disallow them) so that we can avoid the race
    #       condition when accessing the `_cache` in parallel.

    db, err = _cache.db
    if err:
        status.error(
            'Cannot open cache file:',
            'another instance of the program is using the cache'
        )
        status.attention('- you can switch to the other instance or')
        status.attention('- close it and continue using this one, alternatively')
        status.attention('- disable the \'cachefile\' option in the F2 Config')

    result = []
    for query, flags, _ in queries:
        if len(flags) == 0:
            fallback_key = getconf('secondary')
            if fallback_key == '-':
                result.append(perror_query(status, query, getconf('primary'), db))
            else:
                cached = []
                for key in DICTIONARY_LOOKUP:
                    try:
                        cached.append(db[key + query])
                    except KeyError:
                        continue

                result.append(
                    cached or perror_query_with_fallback(
                        status, query, getconf('primary'), fallback_key, db
                    )
                )
        elif len(flags) == 1:
            result.append(perror_query(status, query, flags.pop(), db))
        else:
            result.append(perror_threaded_query(status, query, flags, db))

    return result
