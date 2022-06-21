import time

import pytest

from ankidodawacz import get_dictionaries, parse_query, Query
from src.data import config


@pytest.mark.parametrize(
    ('input_', 'expected'),
    (
        ('test', [Query('test', '', [], [], False)]),
        ('test -n', [Query('test', '', [], ['n'], False)]),
        ('test  -rec -ahd -adh', [Query('test', '', ['ahd'], ['adh'], True)]),
        ('test <testing> ok', [Query('testing', 'test {{testing}} ok', [], [], False)]),
        ('<testing> --asdf', [Query('testing', '{{testing}}', [], ['asdf'], False)]),
        ('<<<', [Query('<<<', '', [], [], False)]),
        ('>>>', [Query('>>>', '', [], [], False)]),
        ('<>', [Query('', '{{}}', [], [], False)]),
        ('>>test<<', [Query('>>test<<', '', [], [], False)]),
        ('<;>', [
            Query('<', '', [], [], False),
            Query('>', '', [], [], False)
        ]),
        ('one -a -record, two <...>> -b, three -c --d', [
            Query('one', '', [], ['a'], True),
            Query('...>', 'two {{...>}}', [], ['b'], False),
            Query('three', '', [config['-dict'], config['-dict2']], ['d'], False)
        ]),
        ('<a> test -l -lexico;<b> test --rec -f', [
            Query('a', '{{a}} test', ['l', 'lexico'], [], False),
            Query('b', '{{b}} test', [], ['f'], True)
        ]),
        ('a;b,c,d', [
            Query('a;b', '', [], [], False),
            Query('c', '', [], [], False),
            Query('d', '', [], [], False)
        ]),
        ('t<es>t -/pla', [Query('es', 't{{es}}t', [], ['/pla'], False)]),
        ('test - ahd  -  /pla ', [Query('test', '', ['ahd'], ['/pla'], False)]),
        ('test - ahd  -  /pla  s ', [Query('test', '', ['ahd'], ['/pla  s'], False)]),
        (',,,', None),
        (',;,;', None),
        (',,a,,', [Query('a', '', [], [], False)]),
    )
)
def test_parse_query(input_, expected):
    assert parse_query(input_) == expected


@pytest.mark.parametrize(
    ('query', 'flags', 'expected'),
    (
        ('mint', ['ahd'], ['ahd']),
        ('best', ['l'], ['lexico']),
        ('best', ['ahd', 'lexico'], ['ahd', 'lexico']),
        ('leap', ['ahd', 'idioms', 'lexico'], ['ahd', 'lexico']),
        ('brem', ['ahd', 'l', 'l'], ['lexico' ,'lexico']),
    )

)
def test_get_dictionaries(query, flags, expected):
    result = get_dictionaries(query, flags)
    assert result is not None
    assert [x.name for x in result] == expected


@pytest.mark.parametrize(
    ('query', 'flags', 'expected', 'cache_hit'),
    (
        ('blind', ['ahd'], ['ahd'], False),
        ('away', ['idioms'], ['farlex'], False),
        ('blind', ['ahd'], ['ahd'], True),
        ('alarm', ['l', 'l'], ['lexico', 'lexico'], False),
        ('alarm', ['lexico', 'lexico', 'l', 'lexico'], ['lexico', 'lexico', 'lexico', 'lexico'], True),
        ('away', ['i', 'idiom'], ['farlex', 'farlex'], True),
    )
)
def test_get_dictionaries_with_cache(query, flags, expected, cache_hit):
    d1 = time.perf_counter()
    result = get_dictionaries(query, flags)
    d2 = time.perf_counter()
    assert result is not None
    assert [x.name for x in result] == expected
    assert (d2 - d1 < 0.001) is cache_hit


def test_get_dictionaries_with_fallback():
    config['-dict'] = 'ahd'
    config['-dict2'] = 'lexico'

    result = get_dictionaries('mint', [])
    assert result is not None
    assert [x.name for x in result] == ['ahd']

    result = get_dictionaries('breme', [])
    assert result is not None
    assert [x.name for x in result] == ['lexico']

    config['-dict2'] = '-'
    result = get_dictionaries('breme', [])
    assert result is None

    result = get_dictionaries('źdźbło', [])
    assert result is None

