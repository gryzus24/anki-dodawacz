from __future__ import annotations

import atexit
from typing import Callable
from typing import Mapping

import lxml.etree as etree
import urllib3
from urllib3.exceptions import ConnectTimeoutError
from urllib3.exceptions import MaxRetryError
from urllib3.exceptions import NewConnectionError

from src.Dictionaries.base import DictionaryError

http = urllib3.PoolManager(
    timeout=10,
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/116.0',
        'Accept-Encoding': 'gzip'
    }
)
atexit.register(http.pools.clear)


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


def prepare_check_text(dictionary_name: str) -> Callable[[etree._Element], str]:
    def check_text(el: etree._Element) -> str:
        text = el.text
        if text is None:
            raise DictionaryError(
                f'ERROR: {dictionary_name}: no text: {el.tag!r} {el.attrib} tail: {el.tail!r}'
            )
        return text

    return check_text


def prepare_check_tail(dictionary_name: str) -> Callable[[etree._Element], str]:
    def check_tail(el: etree._Element) -> str:
        tail = el.tail
        if tail is None:
            raise DictionaryError(
                f'ERROR: {dictionary_name}: no tail: {el.tag!r} {el.attrib} text: {el.text!r}'
            )
        return tail

    return check_tail


def all_text(el: etree._Element) -> str:
    return ''.join(etree.ElementTextIterator(el))


def full_strip(s: str) -> str:
    return ' '.join(s.split())


def quote_example(s: str) -> str:
    return f'‘{s}’'
