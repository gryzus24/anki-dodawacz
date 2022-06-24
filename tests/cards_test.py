import pytest

import src.cards as cards
from src.Dictionaries.dictionary_base import Dictionary


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
def test_hide_with_hide_prepositions(target, phrase_to_hide, expected):
    assert cards.hide(target, phrase_to_hide, '___', hide_prepositions=True) == expected


@pytest.mark.parametrize(
    ('target', 'phrase_to_hide', 'expected'),
    (
        ('Liked sane manes with delight.', 'like mane', 'Liked sane ___s with delight.'),
        ('Liked sane manes with delight.', 'delight with', 'Liked sane manes with ___.'),
        ('Above all else.', 'above all else', 'Above ___ ___.'),
        ('Over and beyond.', 'beyond and over', 'Over and beyond.')
    )
)
def test_hide_without_hide_prepositions(target, phrase_to_hide, expected):
    assert cards.hide(target, phrase_to_hide, '___', hide_prepositions=False) == expected


def test_map_card_fields_to_values():
    dictionary = Dictionary([
        ('HEADER', 'Dictionary Title'),
        ('PHRASE', 'test phrase one', 'some phonetic spelling one'),
        ('AUDIO', 'test_audio_url_one.mp3'),
        ('LABEL', 'test label one', ''),
        ('DEF', 'first definition', 'example sentence one', ''),                        # 4
        ('SUBDEF', 'second definition', 'example sentence two', ''),                    # 5
        ('SUBDEF', 'third definition', 'example sentence three', 'def label one'),      # 6
        ('ETYM', 'etymology one'),
        ('LABEL', 'test label two', ''),
        ('DEF', 'fourth definition', 'example sentence four', 'def label two'),         # 9
        ('SUBDEF', 'fifth definition', 'example sentence five', ''),                    # 10
        ('HEADER', ''),

        ('PHRASE', 'test phrase two', 'some phonetic spelling two'),
        ('AUDIO', 'test_audio_url_two.mp3'),
        ('LABEL', 'test label three', 'some additional label info'),
        ('DEF', 'sixth definition', 'example sentence six', ''),                        # 15
        ('SUBDEF', 'seventh definition', 'example sentence seven', 'def label three'),  # 16
        ('POS', 'pos1|phon1', 'pos2|phon2', 'pos3|'),
        ('ETYM', 'etymology two'),
        ('SYN', 'synonym one, synonym two', 'synonym gloss one:', 'example synonym sentence one'),     # 19
        ('SYN', 'synonym three, synonym four', 'synonym gloss two:', 'example synonym sentence two'),  # 20
    ], name='test')

    expected = (
        {
            'def': 'first definition<br>second definition',
            'syn': '',
            'sen': '',
            'phrase': 'test phrase one',
            'exsen': 'example sentence one<br>example sentence two',
            'pos': '',
            'etym': 'etymology one',
            'audio': '',
            'recording': '',
        },
        'test_audio_url_one.mp3',
    )
    assert cards._map_card_fields_to_values(dictionary, [4, 5]) == expected

    expected = (
        {
            'def': 'sixth definition<br>{def label three} seventh definition',
            'syn': 'synonym gloss two: synonym three, synonym four',
            'sen': '',
            'phrase': 'test phrase two',
            'exsen': 'example sentence six<br>example sentence seven',
            'pos': 'pos1  phon1<br>pos2  phon2<br>pos3',
            'etym': 'etymology two',
            'audio': '',
            'recording': '',
        },
        'test_audio_url_two.mp3'
    )
    assert cards._map_card_fields_to_values(dictionary, [15, 16, 20]) == expected

    dictionary = Dictionary([
        ('HEADER', 'Dictionary Title'),
        ('PHRASE', 'test phrase one', 'some phonetic spelling one'),
        ('AUDIO', 'test_audio_url_one.mp3'),
        ('LABEL', 'test label one', ''),
        ('DEF', 'first definition', 'example sentence one', ''),                        # 4
        ('SUBDEF', 'second definition', 'example sentence two', ''),                    # 5
        ('SUBDEF', 'third definition', 'example sentence three', 'def label one'),      # 6
        ('ETYM', 'etymology one'),
        ('LABEL', 'test label two', ''),
        ('DEF', 'fourth definition', 'example sentence four', 'def label two'),         # 9
        ('SUBDEF', 'fifth definition', 'example sentence five', ''),                    # 10
        ('HEADER', ''),

        ('PHRASE', 'test phrase two', 'some phonetic spelling two'),
        ('AUDIO', ''),
        ('LABEL', 'test label three', 'some additional label info'),
        ('DEF', 'sixth definition', 'example sentence six', ''),                        # 15
        ('SUBDEF', 'seventh definition', 'example sentence seven', 'def label three'),  # 16
        ('POS', 'pos1|phon1', 'pos2|phon2', 'pos3|'),
        ('ETYM', 'etymology two'),
        ('SYN', 'synonym one, synonym two', 'synonym gloss one:', 'example synonym sentence one'),     # 19
        ('SYN', 'synonym three, synonym four', 'synonym gloss two:', 'example synonym sentence two'),  # 20
    ], name='test')
    expected = (
        {
            'def': 'sixth definition<br>{def label three} seventh definition',
            'syn': 'synonym gloss two: synonym three, synonym four',
            'sen': '',
            'phrase': 'test phrase two',
            'exsen': 'example sentence six<br>example sentence seven',
            'pos': 'pos1  phon1<br>pos2  phon2<br>pos3',
            'etym': 'etymology two',
            'audio': '',
            'recording': '',
        },
        'test_audio_url_one.mp3'
    )
    assert cards._map_card_fields_to_values(dictionary, [15, 16, 20]) == expected

    dictionary = Dictionary([
        ('HEADER', 'Dictionary Title'),
        ('PHRASE', 'test phrase one', 'some phonetic spelling one'),
        ('AUDIO', 'test_audio_url_one.mp3'),
        ('LABEL', 'test label one', ''),
        ('DEF', 'first definition', 'example sentence one', ''),                        # 4
        ('SUBDEF', 'second definition', 'example sentence two', ''),                    # 5
        ('SUBDEF', 'third definition', 'example sentence three', 'def label one'),      # 6
        ('ETYM', 'etymology one'),
        ('LABEL', 'test label two', ''),
        ('AUDIO', 'test_audio_url_two.mp3'),
        ('DEF', 'fourth definition', 'example sentence four', 'def label two'),         # 10
        ('SUBDEF', 'fifth definition', 'example sentence five', ''),                    # 11
        ('HEADER', ''),

        ('PHRASE', 'test phrase two', 'some phonetic spelling two'),
        ('AUDIO', ''),
        ('LABEL', 'test label three', 'some additional label info'),
        ('DEF', 'sixth definition', 'example sentence six', ''),                        # 16
        ('SUBDEF', 'seventh definition', 'example sentence seven', 'def label three'),  # 17
        ('POS', 'pos1|phon1', 'pos2|phon2', 'pos3|'),
        ('ETYM', 'etymology two'),
        ('SYN', 'synonym one, synonym two', 'synonym gloss one:', 'example synonym sentence one'),     # 20
        ('SYN', 'synonym three, synonym four', 'synonym gloss two:', 'example synonym sentence two'),  # 21
    ], name='test')
    expected = (
        {
            'def': 'sixth definition<br>{def label three} seventh definition',
            'syn': 'synonym gloss one: synonym one, synonym two',
            'sen': '',
            'phrase': 'test phrase two',
            'exsen': 'example sentence six<br>example sentence seven',
            'pos': 'pos1  phon1<br>pos2  phon2<br>pos3',
            'etym': 'etymology two',
            'audio': '',
            'recording': '',
        },
        ''
    )
    assert cards._map_card_fields_to_values(dictionary, [16, 17, 20]) == expected

    dictionary = Dictionary([
        ('HEADER', 'Dictionary Title'),
        ('PHRASE', 'test phrase one', 'some phonetic spelling one'),
        ('AUDIO', 'test_audio_url_one.mp3'),
        ('LABEL', 'test label one', ''),
        ('DEF', 'first definition', '', ''),                                            # 4
        ('SUBDEF', 'second definition', '', ''),                                        # 5
        ('SUBDEF', 'third definition', 'example sentence three', 'def label one'),      # 6
        ('ETYM', 'etymology one'),
        ('LABEL', 'test label two', ''),
        ('DEF', 'fourth definition', 'example sentence four', 'def label two'),         # 10
        ('SUBDEF', 'fifth definition', 'example sentence five', ''),                    # 11
        ('HEADER', ''),

        ('PHRASE', 'test phrase two', 'some phonetic spelling two'),
        ('AUDIO', ''),
        ('LABEL', 'test label three', 'some additional label info'),
        ('DEF', 'sixth definition', 'example sentence six', ''),                        # 16
        ('SUBDEF', 'seventh definition', 'example sentence seven', 'def label three'),  # 17
        ('POS', 'pos1|phon1', 'pos2|phon2', 'pos3|'),
        ('ETYM', 'etymology two'),
        ('SYN', 'synonym one, synonym two', 'synonym gloss one:', 'example synonym sentence one'),     # 20
        ('SYN', 'synonym three, synonym four', 'synonym gloss two:', 'example synonym sentence two'),  # 21
    ], name='test')
    expected = (
        {
            'def': 'first definition<br>{def label one} third definition<br>second definition',
            'syn': '',
            'sen': '',
            'phrase': 'test phrase one',
            'exsen': 'example sentence three',
            'pos': '',
            'etym': 'etymology one',
            'audio': '',
            'recording': '',
        },
        'test_audio_url_one.mp3'
    )
    assert cards._map_card_fields_to_values(dictionary, [4, 6, 5]) == expected
