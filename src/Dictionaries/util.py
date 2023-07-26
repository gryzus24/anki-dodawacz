from __future__ import annotations

import atexit
import sys
from typing import Any
from typing import Callable
from typing import Mapping
from typing import NoReturn

import lxml.etree as etree

from src.Dictionaries.base import DictionaryError


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
from urllib3.exceptions import ConnectTimeoutError
from urllib3.exceptions import MaxRetryError
from urllib3.exceptions import NewConnectionError

http = urllib3.PoolManager(
    timeout=10,
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:111.0) Gecko/20100101 Firefox/111.0',
        'Accept-Encoding': 'gzip'
    }
)
atexit.register(http.pools.clear)


def request_soup(
        url: str, fields: dict[str, str] | None = None, **kw: Any
) -> BeautifulSoup:
    try:
        r = http.request_encode_url('GET', url, fields=fields, **kw)
    except MaxRetryError:
        raise ConnectionError('connection error: max retries exceeded')
    except Exception as e:
        if isinstance(e.__context__, NewConnectionError):
            raise ConnectionError('connection error: no Internet connection?')
        elif isinstance(e.__context__, ConnectTimeoutError):
            raise ConnectionError('connection error: connection timed out')
        else:
            raise

    # At the moment only WordNet uses other than UTF-8 encoding (iso-8859-1),
    # so as long as there are no decoding problems we'll use UTF-8.
    return BeautifulSoup(r.data.decode(), 'lxml')


def _req(
        url: str, fields: dict[str, str] | None = None, **kw: Any
) -> str:
    try:
        r = http.request_encode_url('GET', url, fields=fields, **kw)
    except MaxRetryError:
        raise ConnectionError('connection error: max retries exceeded')
    except Exception as e:
        if isinstance(e.__context__, NewConnectionError):
            raise ConnectionError('connection error: no Internet connection?')
        elif isinstance(e.__context__, ConnectTimeoutError):
            raise ConnectionError('connection error: connection timed out')
        else:
            raise

    # At the moment only WordNet uses other than UTF-8 encoding (iso-8859-1),
    # so as long as there are no decoding problems we'll use UTF-8.
    return r.data.decode()
    # return BeautifulSoup(r.data.decode(), 'lxml')


def try_request(
        url: str,
        fields: Mapping[str, str | bytes] | None = None,
        **kw: str
) -> bytes:
    try:
        r = http.request_encode_url('GET', url, fields, None, **kw)
    except MaxRetryError:
        raise ConnectionError('connection error: max retries exceeded')
    except Exception as e:
        if isinstance(e.__context__, NewConnectionError):
            raise ConnectionError('connection error: no Internet connection?')
        elif isinstance(e.__context__, ConnectTimeoutError):
            raise ConnectionError('connection error: connection timed out')
        else:
            raise

    return r.data


def parse_response(data: bytes) -> etree._Element:
    p = etree.HTMLParser()
    p.feed(data)
    return p.close()


def prepare_check_text(dictionary_name: str) -> Callable[[etree._Element], str | NoReturn]:
    def check_text(el: etree._Element) -> str | NoReturn:
        text = el.text
        if text is None:
            raise DictionaryError(
                f'ERROR: {dictionary_name}: no text: {el.tag!r} {el.attrib} tail: {el.tail!r}'
            )
        return text

    return check_text


def prepare_check_tail(dictionary_name: str) -> Callable[[etree._Element], str | NoReturn]:
    def check_tail(el: etree._Element) -> str | NoReturn:
        tail = el.tail
        if tail is None:
            raise DictionaryError(
                f'ERROR: {dictionary_name}: no tail: {el.tag!r} {el.attrib} text: {el.text!r}'
            )
        return tail

    return check_tail


def all_text(el: etree._Element) -> str:
    return ''.join(etree.ElementTextIterator(el))


def quote_example(s: str) -> str:
    return f'‘{s}’'
