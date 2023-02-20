import pytest

from src.Dictionaries.diki import diki_audio

# British English pronunciation
gb = 'https://www.diki.pl/images-common/en/mp3/'
# American English pronunciation
ame = 'https://www.diki.pl/images-common/en-ame/mp3/'


@pytest.mark.skip(reason='run when changing diki')
@pytest.mark.parametrize(
    ('phrase', 'expected'),
    (
        ('mince', f'{gb}mince.mp3'),
        ('a blot on the landscape', f'{gb}a_blot_on_the_landscape.mp3'),
        ('(as) light as a feather', f'{gb}as_light_as_a_feather.mp3'),
        ('zip (up) your lip(s)', f'{gb}zip_your_lip.mp3'),
        ('burst the bubble of (someone)', f'{gb}burst_somebodys_bubble.mp3'),
        ('account for', f'{gb}account_for_somebody.mp3'),
        ('abide by', f'{gb}abide_by_something.mp3'),
        ('an open marriage', f'{gb}open_marriage.mp3'),
        ('cast lots', f'{gb}cast_lots.mp3'),
        ('a lot of bunk', f'{gb}bunk.mp3'),
        ('(as) thick as mince', f'{gb}thick.mp3'),
        ('baloney', f'{gb}baloney.mp3'),
    )
)
def test_diki_no_flag_gb(phrase, expected):
    assert diki_audio(phrase) == expected


@pytest.mark.skip(reason='run when changing diki')
@pytest.mark.parametrize(
    ('phrase', 'expected'),
    (
        ('new wine in old bottles', f'{ame}new_wine_in_old_bottles.mp3'),
    )
)
def test_diki_no_flag_ame(phrase, expected):
    assert diki_audio(phrase) == expected


@pytest.mark.skip(reason='run when changing diki')
@pytest.mark.parametrize(
    ('phrase', 'expected'),
    (
        ('', ''),
        ('asdf', ''),
    )
)
def test_diki_incorrect_phrase(phrase, expected):
    assert diki_audio(phrase) == expected


@pytest.mark.skip(reason='run when changing diki')
@pytest.mark.parametrize(
    ('phrase', 'flag', 'expected'),
    (
        ('invalid', '-a', f'{gb}invalid-a.mp3'),
        ('invalid', '-n', f'{gb}invalid-n.mp3'),
        ('invalid', '', f'{gb}invalid.mp3'),
        ('concert', '-v', f'{gb}concert-v.mp3'),
        ('concert', '', f'{gb}concert.mp3'),
        ('concert', 'asdf', f'{gb}concert.mp3'),
        ('concert', 'v', f'{gb}concert.mp3'),
        ('concert', '--v', f'{gb}concert.mp3'),
        ('tap out', '-n', f'{gb}tap_out.mp3'),
        ('tap out', '-a', f'{gb}tap_out.mp3'),
    )
)
def test_diki_with_flag(phrase, flag, expected):
    assert diki_audio(phrase, flag) == expected
