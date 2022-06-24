import time

import pytest

from ankidodawacz import get_dictionaries, parse_query, Query
from src.data import config


@pytest.mark.parametrize(
    ('input_', 'expected'),
    (
        ('test', [Query('test', '', [], [], False)]),
        ('test -n', [Query('test', '', [], ['n'], False)]),
        ('test -rec -ahd -adh', [Query('test', '', ['ahd'], ['adh'], True)]),
        ('test -b - - --4 --c', [Query('test', '', ['ahd', 'lexico'], ['b', '4'], False)]),
        ('test  -rec    -ahd-adh', [Query('test', '', [], ['ahd-adh'], True)]),
        # be more lenient with validation, as long as we can
        ('test - ahd  -  / pla ', [Query('test', '', ['ahd'], ['/ pla'], False)]),
    )
)
def test_parse_query_trivial(input_, expected):
    assert parse_query(input_) == expected


@pytest.mark.parametrize(
    ('input_', 'expected'),
    (
        ('test <testing>', [Query('testing', 'test {{testing}}', [], [], False)]),
        ('test <testing> ok', [Query('testing', 'test {{testing}} ok', [], [], False)]),
        ('<test t>esting ok', [Query('test t', '{{test t}}esting ok', [], [], False)]),
        ('<test <t>esting ok', [Query('test <t', '{{test <t}}esting ok', [], [], False)]),
        ('<test <t>estin>g ok', [Query('test <t>estin', '{{test <t>estin}}g ok', [], [], False)]),
        ('<test> <testing> ok', [Query('test> <testing', '{{test> <testing}} ok', [], [], False)]),
        ('<test> <tes<t>ing> ok --asdf -wnet', [Query('test> <tes<t>ing', '{{test> <tes<t>ing}} ok', ['wnet'], ['asdf'], False)]),
        ('<>', [Query('', '{{}}', [], [], False)]),
        ('<<<', [Query('<<<', '', [], [], False)]),
        ('>>>', [Query('>>>', '', [], [], False)]),
        ('>>test<<', [Query('>>test<<', '', [], [], False)]),
        ('-ahd <test>', [Query('test', '-ahd {{test}}', [], [], False)]),
    )
)
def test_parse_query_sentences(input_, expected):
    assert parse_query(input_) == expected


@pytest.mark.parametrize(
    ('input_', 'expected'),
    (
        ('one -a -record, two <...> -b, three -c --d', [
            Query('one', '', [], ['a'], True),
            Query('...', 'two {{...}}', [], ['b'], False),
            Query('three', '', [config['-dict'], config['-dict2']], ['d'], False)
        ]),
        ('one -a -record; two <...> -b; three -c --d', [
            Query('one', '', [], ['a'], True),
            Query('...', 'two {{...}}', [], ['b'], False),
            Query('three', '', [config['-dict'], config['-dict2']], ['d'], False)
        ]),
        ('<a> test -l -lexico;<b> test --rec -f', [
            Query('a', '{{a}} test', ['l', 'lexico'], [], False),
            Query('b', '{{b}} test', [], ['f'], True)
        ]),
        ('<;>', [
            Query('<', '', [], [], False),
            Query('>', '', [], [], False)
        ]),
        (' -l ;<;>; ; ; ', [
            Query('-l', '', [], [], False),
            Query('<', '', [], [], False),
            Query('>', '', [], [], False)
        ]),
        ('a,b,c,d', [
            Query('a', '', [], [], False),
            Query('b', '', [], [], False),
            Query('c', '', [], [], False),
            Query('d', '', [], [], False)
        ]),
        ('a;b,c,d', [
            Query('a;b', '', [], [], False),
            Query('c', '', [], [], False),
            Query('d', '', [], [], False)
        ]),
        (',,a,a,', [
            Query('a', '', [], [], False),
            Query('a', '', [], [], False)
        ]),
        (',,<>,<>,', [
            Query('', '{{}}', [], [], False),
            Query('', '{{}}', [], [], False)
        ]),
        (',,,', None),
        (',;,;', None),
    )
)
def test_parse_query_separators(input_, expected):
    assert parse_query(input_) == expected


@pytest.mark.parametrize(
    ('query', 'flags', 'expected_dictionary_names'),
    (
        ('mint', ['ahd'], ['ahd']),
        ('best', ['l'], ['lexico']),
        ('best', ['ahd', 'lexico'], ['ahd', 'lexico']),
        ('leap', ['ahd', 'idioms', 'lexico'], ['ahd', 'lexico']),
        ('brem', ['ahd', 'l', 'l'], ['lexico' ,'lexico']),
    )

)
def test_get_dictionaries(query, flags, expected_dictionary_names):
    result = get_dictionaries(query, flags)
    assert result is not None
    assert [x.name for x in result] == expected_dictionary_names


@pytest.mark.parametrize(
    ('query', 'flags', 'expected_dictionary_names', 'cache_hit'),
    (
        ('blind', ['ahd'], ['ahd'], False),
        ('away', ['idioms'], ['farlex'], False),
        ('blind', ['ahd'], ['ahd'], True),
        ('alarm', ['l', 'l'], ['lexico', 'lexico'], False),
        ('alarm', ['lexico', 'lexico', 'l', 'lexico'], ['lexico', 'lexico', 'lexico', 'lexico'], True),
        ('away', ['i', 'idiom'], ['farlex', 'farlex'], True),
    )
)
def test_get_dictionaries_with_cache(query, flags, expected_dictionary_names, cache_hit):
    t1 = time.perf_counter()
    result = get_dictionaries(query, flags)
    t2 = time.perf_counter()
    assert result is not None
    assert [x.name for x in result] == expected_dictionary_names
    assert (t2 - t1 < 0.001) is cache_hit


def test_get_dictionaries_with_fallback():
    config['-dict'] = 'ahd'
    config['-dict2'] = 'lexico'
    result = get_dictionaries('mint', [])
    assert result is not None
    assert [x.name for x in result] == ['ahd']

    result = get_dictionaries('breme', [])
    assert result is not None
    assert [x.name for x in result] == ['lexico']

    result = get_dictionaries('źdźbło', [])
    assert result is None

    config['-dict'] = 'ahd'
    config['-dict2'] = '-'
    result = get_dictionaries('breme', [])
    assert result is None

    result = get_dictionaries('źdźbło', [])
    assert result is None

    config['-dict'] = 'ahd'
    config['-dict2'] = 'ahd'
    result = get_dictionaries('źdźbło', [])
    assert result is None
