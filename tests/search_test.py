import pytest

from src.data import config
from src.search import parse_query, Query


@pytest.mark.parametrize(
    ('input_', 'expected'),
    (
        ('test', [Query('test', '', [], [], False)]),
        ('test -n', [Query('test', '', [], ['n'], False)]),
        ('test -rec -ahd -adh', [Query('test', '', ['ahd'], ['adh'], True)]),
        ('test -b - - --4 --c', [Query('test', '', ['ahd', 'farlex'], ['b', '4'], False)]),
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
        ('<a> test -l -farlex;<b> test --rec -f', [
            Query('a', '{{a}} test', ['farlex'], ['l'], False),
            Query('b', '{{b}} test', [], ['f'], True)
        ]),
        ('<,>', [
            Query('<', '', [], [], False),
            Query('>', '', [], [], False)
        ]),
        ('<,,>', [
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
