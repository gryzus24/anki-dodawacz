import pytest

from src.console_main import parse_input


@pytest.mark.parametrize(
    ('input_', 'expected'),
    (
        ('1', [1]),
        ('9', [9]),
        ('20', [20]),
        ('21', [20]),
        ('-1', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]),
        ('all', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]),
        ('-all', [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
    )
)
def test_parse_input_base_cases(input_, expected):
    assert parse_input(input_, 20) == expected


@pytest.mark.parametrize(
    ('input_', 'expected'),
    (
        ('1,2', [1, 2]),
        ('4,3,2', [4, 3, 2]),
        ('6,1,9', [6, 1, 9]),
        (' 6  ,2 ,  9  ', [6, 2, 9]),
        ('5,5,2,1,2', [5, 2, 1]),
        ('0,2,2,-1', [2]),
        ('42, 5, 90', [20, 5]),
        ('99, 89, 78', [20]),
    )
)
def test_parse_input_comma_separated(input_, expected):
    assert parse_input(input_, 20) == expected


@pytest.mark.parametrize(
    ('input_', 'expected'),
    (
        ('1:5', [1, 2, 3, 4, 5]),
        ('0:5', [5]),
        (':5', [1, 2, 3, 4, 5]),
        ('-1:5', [5]),
        ('5:1', [5, 4, 3, 2, 1]),
        ('5:0', [5]),
        ('5:', [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]),
        ('5:-1', [5]),
        ('7:3', [7, 6, 5, 4, 3]),
        ('16:20', [16, 17, 18, 19, 20]),
        ('16:70', [16, 17, 18, 19, 20]),
        (' 18 : 21  ', [18, 19, 20]),
        ('0:', [20]),
        (':', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]),
        ('5:7:2:2', [5, 6, 7, 4, 3, 2]),
    )
)
def test_parse_input_ranges(input_, expected):
    assert parse_input(input_, 20) == expected


@pytest.mark.parametrize(
    ('input_', 'expected'),
    (
        ('1:3,5:7', [1, 2, 3, 5, 6, 7]),
        ('4:1,7:2', [4, 3, 2, 1, 7, 6, 5]),
        (':,:', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]),
        (':5:2:10,4:1:2:1:7', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        ('3:s,5:s', [3, 5])
    )
)
def test_parse_input_comma_separated_ranges(input_, expected):
    assert parse_input(input_, 20) == expected


@pytest.mark.parametrize(
    ('input_', 'expected'),
    (
        ('a', None),
        (',,', None),
        ('0', None),
        ('-s', None),
    )
)
def test_parse_input_invalid_cases(input_, expected):
    assert parse_input(input_, 20) == expected
