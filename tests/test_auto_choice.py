from src.Dictionaries.lexico import Lexico


def ic_test_encl(test_dict, split_at='HEADER', choices_of='DEF', expect_choice_first=False):
    def ic_test(choi, sa=split_at, cf=choices_of, ecf=expect_choice_first):
        lexico = Lexico()
        for instr in test_dict:
            lexico.add(instr)

        return lexico.get_positions_in_sections(choi, sa, cf, expect_choice_first=ecf)

    return ic_test


def test_input_cycle():
    td = [
        ('PHRASE', 'phrase_1', '/ˈɪnvəlɪd/'),

        ('LABEL', 'noun', ''),
        ('DEF', 'def_1', 'exsen_1'),
        ('AUDIO', 'audio_1'),

        ('LABEL', 'verb', '[with object]'),
        ('DEF', 'def_2', 'exsen_2'),
        ('SUBDEF', 'def_3', 'exsen_3'),  # 3
        ('AUDIO', 'audio_2'),
        ('ETYM', 'etym_1'),

        ('HEADER', ' '),
        ('PHRASE', 'phrase_2', '/ɪnˈvalɪd/'),

        ('LABEL', 'adjective', ''),
        ('DEF', 'def_4', 'exsen_4'),
        ('SUBDEF', 'def_5', 'exsen_5'),
        ('SUBDEF', 'def_6', 'exsen_6'),
        ('AUDIO', 'audio_3'),
        ('ETYM', 'etym_2'),
    ]

    t = ic_test_encl(td, expect_choice_first=True)
    assert t([1]) == [1]
    assert t([1, 2]) == [1]
    assert t([3]) == [1]
    assert t([4]) == [2]
    assert t([6, 1]) == [2, 1]
    assert t([8]) == [1]
    assert t([9, 8, 0, 0]) == [1]
    assert t([0]) == [1]
    assert t([1, 2, 3, 4, 5, 6]) == [1, 2]

    t = ic_test_encl(td, split_at='LABEL')
    assert t([1]) == [1]
    assert t([1, 2]) == [1, 2]
    assert t([3]) == [2]
    assert t([4]) == [3]
    assert t([6, 1]) == [3, 1]
    assert t([8]) == [1]
    assert t([9, 8, 0, 0]) == [1]
    assert t([0]) == [1]
    assert t([1, 2, 3, 4, 5, 6]) == [1, 2, 3]

    t = ic_test_encl(td, split_at='AUDIO', expect_choice_first=True)
    assert t([1]) == [1]
    assert t([1, 2]) == [1, 2]
    assert t([3]) == [2]
    assert t([4]) == [3]
    assert t([6, 1]) == [3, 1]
    assert t([8]) == [1]
    assert t([9, 8, 0, 0]) == [1]
    assert t([0]) == [1]
    assert t([1, 2, 3, 4, 5, 6]) == [1, 2, 3]

    td = [
        ('PHRASE', 'phrase_1', '/ˈɪnvəlɪd/'),

        ('LABEL', 'noun', ''),
        ('DEF', 'def_1', 'exsen_1'),

        ('LABEL', 'verb', '[with object]'),
        ('DEF', 'def_2', 'exsen_2'),
        ('SUBDEF', 'def_3', 'exsen_3'),  # 3
        ('ETYM', 'etym_1'),

        ('HEADER', ' '),
        ('PHRASE', 'phrase_2', '/ɪnˈvalɪd/'),

        ('LABEL', 'adjective', ''),
        ('DEF', 'def_4', 'exsen_4'),
        ('SUBDEF', 'def_5', 'exsen_5'),
        ('SUBDEF', 'def_6', 'exsen_6'),
        ('AUDIO', 'audio_3'),
        ('ETYM', 'etym_2'),
    ]

    t = ic_test_encl(td, split_at='AUDIO', expect_choice_first=True)
    assert t([1]) == [1]
    assert t([1, 2]) == [1]
    assert t([3]) == [1]
    assert t([4]) == [1]
    assert t([6, 1]) == [1]
    assert t([8]) == [1]
    assert t([9, 8, 0, 0]) == [1]
    assert t([0]) == [1]
    assert t([1, 2, 3, 4, 5, 6]) == [1]

    td = [
        ('PHRASE', 'phrase_1', '/ˈɪnvəlɪd/'),
        ('AUDIO', 'audio_1'),
        ('LABEL', 'noun', ''),
        ('DEF', 'def_1', 'exsen_1'),

        ('LABEL', 'verb', '[with object]'),
        ('DEF', 'def_2', 'exsen_2'),
        ('SUBDEF', 'def_3', 'exsen_3'),  # 3
        ('ETYM', 'etym_1'),

        ('HEADER', ' '),
        ('PHRASE', 'phrase_2', '/ɪnˈvalɪd/'),

        ('LABEL', 'adjective', ''),
        ('DEF', 'def_4', 'exsen_4'),
        ('SUBDEF', 'def_5', 'exsen_5'),
        ('SUBDEF', 'def_6', 'exsen_6'),
        ('ETYM', 'etym_2'),
    ]

    t = ic_test_encl(td, split_at='AUDIO')
    assert t([1]) == [1]
    assert t([1, 2]) == [1]
    assert t([3]) == [1]
    assert t([4]) == [1]
    assert t([6, 1]) == [1]
    assert t([8]) == [1]
    assert t([9, 8, 0, 0]) == [1]
    assert t([0]) == [1]
    assert t([1, 2, 3, 4, 5, 6]) == [1]


if __name__ == '__main__':
    test_input_cycle()
