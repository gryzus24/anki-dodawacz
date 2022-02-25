from src.Dictionaries.dictionary_base import Dictionary

test_dict_content = [
    ('HEADER', 'AH Dictionary'), ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'), ('PHRASE', 'fell', '/fɛl/'), ('LABEL', 'tr.v.', 'felled * fell·ing * fells'), ('DEF', 'To cause to fall by striking; cut or knock down.', '‘fell a tree’<br>‘fell an opponent in boxing.’', ''), ('SUBDEF', 'To kill.', "‘was felled by an assassin's bullet.’", ''), ('DEF', 'To sew or finish (a seam) with the raw edges flattened, turned under, and stitched down.', '', ''), ('LABEL', 'n.', ''), ('DEF', 'The timber cut down in one season.', '', ''), ('DEF', 'A felled seam.', '', ''), ('POS', 'fell.able adj.|'), ('ETYM', '[Middle English fellen, from Old English fellan, fyllan.]'), ('HEADER', ''), ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'), ('PHRASE', 'fell', '/fɛl/'), ('LABEL', 'adj.', ''), ('DEF', 'Of an inhumanly cruel nature; fierce.', '‘fell hordes.’', ''), ('DEF', 'Capable of destroying; lethal.', '‘a fell blow.’', ''), ('DEF', 'Dire; sinister.', '‘by some fell chance.’', ''), ('DEF', 'Sharp and biting.', '', 'Scots'), ('POS', 'fell.ness n.|'), ('ETYM', '[Middle English fel, from Old French, variant of felon; see  FELON1.]'), ('HEADER', 'Idioms'), ('PHRASE', 'at/in one fell swoop', ''), ('DEF', 'All at once.', '', ''), ('HEADER', ''), ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'), ('PHRASE', 'fell', '/fɛl/'), ('LABEL', 'n.', ''), ('DEF', 'The hide of an animal; a pelt.', '', ''), ('DEF', 'A thin membrane directly beneath the hide.', '', ''), ('POS', ''), ('ETYM', '[Middle English fel, from Old English fell; see  pel-3 in the Appendix of Indo-European roots.]'), ('HEADER', ''), ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'), ('PHRASE', 'fell', '/fɛl/'), ('LABEL', 'n.', ''), ('DEF', 'An upland stretch of open country; a moor.', '', 'Chiefly British'), ('DEF', 'A barren or stony hill.', '', ''), ('POS', ''), ('ETYM', '[Middle English fel, from Old Norse fell, fjall, mountain, hill.]'), ('HEADER', ''), ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'), ('PHRASE', 'fell', '/fɛl/'), ('LABEL', 'v.', ''), ('DEF', 'Past tense of  fall.', '', ''), ('POS', ''), ('ETYM', '')
]


def test_audio_urls_property():
    d = Dictionary()
    assert d.audio_urls == ['']

    d = Dictionary()
    d.add('AUDIO', '')
    d.add('AUDIO', '')
    assert d.audio_urls == ['', '']

    d = Dictionary()
    d.add('AUDIO', 'someaudio.mp3')
    d.add('AUDIO', 'moreaudio.mp3')
    assert d.audio_urls == ['someaudio.mp3', 'moreaudio.mp3']

    d = Dictionary()
    d.add('AUDIO', '')
    d.add('AUDIO', 'someaudio.mp3')
    assert d.audio_urls == ['someaudio.mp3', 'someaudio.mp3']

    d = Dictionary()
    d.add('AUDIO', 'someaudio.mp3')
    d.add('AUDIO', '')
    d.add('AUDIO', 'moreaudio.mp3')
    assert d.audio_urls == ['someaudio.mp3', '', 'moreaudio.mp3']

    d = Dictionary()
    d.add('HEADER', 'Dictionary')
    d.add('AUDIO', 'someaudio.mp3')
    d.add('DEF', '', '', '')
    d.add('AUDIO', '')
    d.add('AUDIO', 'moreaudio.mp3')
    assert d.audio_urls == ['someaudio.mp3', '', 'moreaudio.mp3']


def _test_get_positions_in_sections(test_content, from_within, choices_of):
    d = Dictionary(test_content)

    def call(*choices):
        return d.get_positions_in_sections(list(choices), from_within, choices_of)

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

        ('HEADER', '', ''),
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


def test_to_audio_choice():
    d = Dictionary(test_dict_content)  # type: ignore

    choices_by_etym = d.get_positions_in_sections([1, 2, 3, 4, 5], from_within='ETYM')
    assert d.to_auto_choice(choices_by_etym, 'ETYM') == '1'

    choices_by_etym = d.get_positions_in_sections([1, 2, 3, 4, 5, 6], from_within='ETYM')
    assert d.to_auto_choice(choices_by_etym, 'ETYM') == '1,2'

    choices_by_etym = d.get_positions_in_sections([6], from_within='ETYM')
    assert d.to_auto_choice(choices_by_etym, 'ETYM') == '2'

    choices_by_etym = d.get_positions_in_sections([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14], from_within='ETYM')
    assert d.to_auto_choice(choices_by_etym, 'ETYM') == '1,2,3,4'

    choices_by_etym = d.get_positions_in_sections([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], from_within='ETYM')
    assert d.to_auto_choice(choices_by_etym, 'ETYM') == '-1'

    # shouldn't happen if input is parsed, _max == 15.
    choices_by_etym = d.get_positions_in_sections([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], from_within='ETYM')
    assert d.to_auto_choice(choices_by_etym, 'ETYM') == '-1'
    assert d.to_auto_choice(choices_by_etym, 'HEADER') == '1,2,3,4,5'

    choices_by_etym = d.get_positions_in_sections([6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 1, 2, 3, 4, 5], from_within='ETYM')
    assert d.to_auto_choice(choices_by_etym, 'ETYM') == '2,3,4,5,1'
    assert d.to_auto_choice(choices_by_etym, 'HEADER') == '2,3,4,5,1'

    choices_by_headers = d.get_positions_in_sections([6])
    assert d.to_auto_choice(choices_by_headers, 'ETYM') == '2'
    assert d.to_auto_choice(choices_by_headers, 'HEADER') == '2'

    # shouldn't happen if input is parsed, _max == 15.
    choices_by_headers = d.get_positions_in_sections([16], from_within='ETYM')
    assert d.to_auto_choice(choices_by_headers, 'ETYM') == '1'
    assert d.to_auto_choice(choices_by_headers, 'HEADER') == '1'

    choices_by_headers = d.get_positions_in_sections([6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 1, 2, 3, 4, 5])
    assert d.to_auto_choice(choices_by_headers, 'ETYM') == '2,3,4,5,1'
    assert d.to_auto_choice(choices_by_headers, 'HEADER') == '2,3,4,5,6,1'


if __name__ == '__main__':
    test_audio_urls_property()
    test_get_positions_in_sections()
    test_to_audio_choice()
