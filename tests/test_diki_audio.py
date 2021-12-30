# This file has to be moved to the project's main directory in order to work.
# I have no idea how to get imports to work without fiddling with the sys.path.
# AFAIK it's possible to do.
from src.Dictionaries.audio_dictionaries import diki_audio

link = 'https://www.diki.pl/images-common/en/mp3/'


def test_diki():
    t = diki_audio
    assert t('mince') == f'{link}mince.mp3'
    assert t('a blot on the landscape') == f'{link}a_blot_on_the_landscape.mp3'
    assert t('(as) light as a feather') == f'{link}as_light_as_a_feather.mp3'
    assert t('asdf') == ''

    assert t('zip (up) your lip(s)!') == f'{link}zip_your_lip.mp3'
    assert t(' burst the bubble of (someone)  ') == f'{link}burst_somebodys_bubble.mp3'
    assert t('account for') == f'{link}account_for_somebody.mp3'
    assert t('abide by') == f'{link}abide_by_something.mp3'
    assert t('an open marriage') == f'{link}open_marriage.mp3'
    assert t('cast lots') == f'{link}cast_lots.mp3'
    assert t('a lot of bunk') == f'{link}bunk.mp3'
    assert t('(as) thick as mince') == f'{link}thick.mp3'
    assert t('new_wine_in_old_bottles') == f'{link}new_wine_in_old_bottles.mp3'

    assert t('tap out', '-n') == f'{link}tap_out.mp3'
    assert t('tap out', '-a') == f'{link}tap_out.mp3'

    assert t('invalid', '-a') == f'{link}invalid-a.mp3'
    assert t('invalid', '-n') == f'{link}invalid-n.mp3'
    assert t('invalid', '') == f'{link}invalid.mp3'

    assert t('concert', '-v') == f'{link}concert-v.mp3'
    assert t('concert', '') == f'{link}concert.mp3'
    assert t('concert', 'asdf') == f'{link}concert.mp3'


if __name__ == '__main__':
    test_diki()
