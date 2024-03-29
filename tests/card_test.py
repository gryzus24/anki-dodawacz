import pytest

import src.card as card
from src.data import config


@pytest.mark.parametrize(
    ('target', 'phrase_to_hide', 'expected'),
    (
        ('An example sentence.', 'example', 'An ___ sentence.'),
        ('An example sentence.', 'example sentence', 'An ___ ___.'),
        ('AN EXAMPLE SENTENCE.', 'example sentence', 'AN ___ ___.'),
        ('An Example Sentence.', 'example sentence', 'An ___ ___.'),
        pytest.param('aN eXAmpLe sENtEncE.', 'example sentence', 'An ___ ___.', marks=pytest.mark.xfail),
        ('Vary is a problematic word.', 'vary', '___ is a problematic word.'),
        ('Varied is a problematic word.', 'vary', '___ied is a problematic word.'),
        ('Vary is a problematic word.', 'varied', 'Vary is a problematic word.'),
        ('Vary is a problematic word.', 'vary is a', '___ is a problematic word.'),
        ('Varies is a problematic word.', 'problem vary', '___ies is a ___atic word.'),
        ('Liked sane manes with delight', 'like mane', '___d sane ___s with delight'),
        ('Liked sane manes with delight.', 'liked mane', '___ sane ___s with delight.'),
        ('Liked sane manes with delight.', 'delight with', 'Liked sane manes ___ ___.'),
        ('Over-engineered', 'engineer', 'Over-___ed'),
    )
)
def test_hide_hidepreps(target, phrase_to_hide, expected):
    config['hidepreps'] = True
    config['hides'] = '___'
    hide_func = card.prepare_hide_func(phrase_to_hide)
    assert hide_func(target) == expected


@pytest.mark.parametrize(
    ('target', 'phrase_to_hide', 'expected'),
    (
        ('Liked sane manes with delight.', 'like mane', 'Liked sane ___s with delight.'),
        ('Liked sane manes with delight.', 'delight with', 'Liked sane manes with ___.'),
        ('Above all else.', 'above all else', 'Above ___ ___.'),
        ('Over and beyond.', 'beyond and over', 'Over and beyond.')
    )
)
def test_hide_nohidepreps(target, phrase_to_hide, expected):
    config['hidepreps'] = False
    config['hides'] = '___'
    hide_func = card.prepare_hide_func(phrase_to_hide)
    assert hide_func(target) == expected
