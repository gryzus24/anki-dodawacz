from src.Dictionaries.base import AUDIO
from src.Dictionaries.base import DEF
from src.Dictionaries.base import Dictionary
from src.Dictionaries.base import DictionarySelection
from src.Dictionaries.base import EntrySelector
from src.Dictionaries.base import ETYM
from src.Dictionaries.base import HEADER
from src.Dictionaries.base import LABEL
from src.Dictionaries.base import PHRASE
from src.Dictionaries.base import POS


def test_dump_selection():
    d = Dictionary()
    phrase_one = PHRASE('1', '1')
    phrase_two = PHRASE('2', '2')

    audio_one = AUDIO('1')
    audio_two = AUDIO('2')

    label_one = LABEL('1', '1')
    label_two = LABEL('2', '2')

    def_one = DEF('1', ['1', '2'], '1', subdef=False)
    def_two = DEF('2', ['3', '4'], '2', subdef=True)
    def_three = DEF('3', ['5', '6'], '3', subdef=False)
    def_four = DEF('4', ['7', '8'], '4', subdef=False)

    pos_one = POS([('1', '1'), ('2', '2')])
    pos_two = POS([('3', '3'), ('4', '4')])

    etym_one = ETYM('1')
    etym_two = ETYM('2')

    d.add(HEADER('Test'))
    d.add(phrase_one)
    d.add(audio_one)
    d.add(label_one)
    d.add(label_two)
    d.add(def_one)
    d.add(def_two)
    d.add(pos_one)
    d.add(etym_one)
    d.add(HEADER('Header'))
    d.add(phrase_two)
    d.add(audio_two)
    d.add(def_three)
    d.add(def_four)
    d.add(etym_two)
    d.add(pos_two)

    e = EntrySelector(d)
    assert e.dump_selection(respect_phrase_boundaries=True) == None
    assert e.dump_selection(respect_phrase_boundaries=False) == None

    e.toggle_def_index(1)
    assert e.dump_selection(respect_phrase_boundaries=True) == [
        DictionarySelection(audio_one, [def_one], etym_one, phrase_one, pos_one, [])
    ]
    assert e.dump_selection(respect_phrase_boundaries=False) == [
        DictionarySelection(audio_one, [def_one], etym_one, phrase_one, pos_one, [])
    ]

    e.toggle_def_index(2)
    assert e.dump_selection(respect_phrase_boundaries=True) == [
        DictionarySelection(audio_one, [def_one, def_two], etym_one, phrase_one, pos_one, [])
    ]
    assert e.dump_selection(respect_phrase_boundaries=False) == [
        DictionarySelection(audio_one, [def_one, def_two], etym_one, phrase_one, pos_one, [])
    ]

    e.toggle_def_index(1)
    e.toggle_def_index(3)
    assert e.dump_selection(respect_phrase_boundaries=True) == [
        DictionarySelection(audio_one, [def_two], etym_one, phrase_one, pos_one, []),
        DictionarySelection(audio_two, [def_three], etym_two, phrase_two, pos_two, [])
    ]
    assert e.dump_selection(respect_phrase_boundaries=False) == [
        DictionarySelection(audio_one, [def_two, def_three], etym_one, phrase_one, pos_one, [])
    ]

    e.clear_selection()
    e.toggle_def_index(1)
    e.toggle_def_index(2)
    e.toggle_def_index(3)
    e.toggle_def_index(4)
    assert e.dump_selection(respect_phrase_boundaries=True) == [
        DictionarySelection(audio_one, [def_one, def_two], etym_one, phrase_one, pos_one, []),
        DictionarySelection(audio_two, [def_three, def_four], etym_two, phrase_two, pos_two, [])
    ]
    assert e.dump_selection(respect_phrase_boundaries=False) == [
        DictionarySelection(audio_one, [def_one, def_two, def_three, def_four], etym_one, phrase_one, pos_one, [])
    ]

    e.toggle_def_index(1)
    e.toggle_def_index(2)
    assert e.dump_selection(respect_phrase_boundaries=True) == [
        DictionarySelection(audio_two, [def_three, def_four], etym_two, phrase_two, pos_two, [])
    ]
    assert e.dump_selection(respect_phrase_boundaries=False) == [
        DictionarySelection(audio_two, [def_three, def_four], etym_two, phrase_two, pos_two, [])
    ]
