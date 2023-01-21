from __future__ import annotations

import atexit
import sys
from typing import Any

from src.data import USER_AGENT

# Silence warnings if soupsieve is not installed, which is good
# because its bloated "css parse" slows down import time a lot.
# ~70ms on my desktop and ~200ms on an android phone.
# bs4 itself compiles regexes on startup which slows it down by
# another 40-150ms. And guess what? These regexes are useless.
try:
    sys.stderr = None  # type: ignore[assignment]
    from bs4 import BeautifulSoup, __version__  # type: ignore[attr-defined]
finally:
    sys.stderr = sys.__stderr__

if (*map(int, __version__.split('.')),) < (4, 10, 0):
    sys.stderr.write(
         '----------------------------------------------------------------\n'
         'Your version of beautifulsoup is out of date, please update:\n'
         'pip install -U beautifulsoup4\n'
         'If you are using a virtual environment, you can safely uninstall\n'
         'the soupsieve package to slightly speed up program startup:\n'
         'pip uninstall soupsieve\n'
    )
    raise SystemExit
else:
    del __version__

import urllib3
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError

http = urllib3.PoolManager(timeout=10, headers=USER_AGENT)
atexit.register(http.pools.clear)


def request_soup(
        url: str, fields: dict[str, str] | None = None, **kw: Any
) -> BeautifulSoup:
    try:
        r = http.request_encode_url('GET', url, fields=fields, **kw)  # type: ignore[no-untyped-call]
    except Exception as e:
        if isinstance(e.__context__, NewConnectionError):
            raise ConnectionError('possibly no Internet connection')
        elif isinstance(e.__context__, ConnectTimeoutError):
            raise ConnectionError('connection timed out')
        else:
            raise

    # At the moment only WordNet uses other than UTF-8 encoding (iso-8859-1),
    # so as long as there are no decoding problems we'll use UTF-8.
    return BeautifulSoup(r.data.decode(), 'lxml')
