from src.Dictionaries.lexico import Lexico


def _test_get_positions_in_sections(test_content, from_within, choices_of):
    lexico = Lexico()
    for item in test_content:
        lexico.add(*item)

    def call(*choices):
        return lexico.get_positions_in_sections(list(choices), from_within, choices_of)

    return call


def test_get_positions_in_sections():
    test_content = [
        ('PHRASE', '', ''),

        ('LABEL', '', ''),
        ('DEF', '', ''),
        ('AUDIO', ''),

        ('LABEL', '', ''),
        ('DEF', '', ''),
        ('SUBDEF', '', ''),
        ('AUDIO', ''),
        ('ETYM', ''),

        ('HEADER', ''),
        ('PHRASE', '', ''),

        ('LABEL', '', ''),
        ('DEF', '', ''),
        ('SUBDEF', '', ''),
        ('SUBDEF', '', ''),
        ('AUDIO', ''),
        ('ETYM', ''),
    ]

    choices_of = _test_get_positions_in_sections(
        test_content,
        from_within='HEADER',
        choices_of='DEF'
    )
    assert choices_of(1) == [1]
    assert choices_of(1, 2) == [1]
    assert choices_of(3) == [1]
    assert choices_of(4) == [2]
    assert choices_of(1, 6) == [1, 2]
    assert choices_of(7) == [1]
    assert choices_of(0) == [1]
    assert choices_of(-1) == [1]
    assert choices_of(-2, 9, 0) == [1]
    assert choices_of(-2, 5, 4, 0) == [2]
    assert choices_of(1, 2, 3, 4, 5, 6) == [1, 2]

    choices_of = _test_get_positions_in_sections(
        test_content,
        from_within='LABEL',
        choices_of='DEF'
    )
    assert choices_of(1) == [1]
    assert choices_of(1, 2) == [1, 2]
    assert choices_of(3) == [2]
    assert choices_of(4) == [3]
    assert choices_of(1, 6) == [1, 3]
    assert choices_of(7) == [1]
    assert choices_of(0) == [1]
    assert choices_of(-1) == [1]
    assert choices_of(-2, 9, 0) == [1]
    assert choices_of(-2, 5, 4, 0) == [3]
    assert choices_of(1, 2, 3, 4, 5, 6) == [1, 2, 3]


if __name__ == '__main__':
    test_get_positions_in_sections()
