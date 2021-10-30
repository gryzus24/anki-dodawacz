import unittest

# This file has to be moved to the project's main directory in order to work.
# I have no idea how to get imports to work without fiddling with the sys.path.
# AFAIK it's possible to do.
from src.Dictionaries.audio_dictionaries import diki_audio

link = 'https://www.diki.pl/images-common/en/mp3/'


class TestDikiAudio(unittest.TestCase):

    def test_trivial_cases(self):
        self.assertEqual(diki_audio('mince', ''), (f'{link}mince.mp3', 'mince.mp3'))
        self.assertEqual(diki_audio('a blot on the landscape', ''),
                         (f'{link}a_blot_on_the_landscape.mp3', 'a_blot_on_the_landscape.mp3'))
        self.assertEqual(diki_audio('asdfasdf', 'noun'), ('', ''))
        self.assertEqual(diki_audio('asdfasdf', 'asdfasdf'), ('', ''))
        self.assertEqual(diki_audio('', 'asdfasdf'), ('', ''))
        self.assertEqual(diki_audio('', 'noun'), ('', ''))
        self.assertEqual(diki_audio('', ''), ('', ''))
        self.assertEqual(diki_audio('', None), ('', ''))

    def test_noun_verb_adj_functionality(self):
        # all possible flags are: noun, verb, adjective, n, v, adj
        self.assertEqual(diki_audio('mince', 'noun'), (f'{link}mince.mp3', 'mince.mp3'))
        self.assertEqual(diki_audio('mince', 'verb'), (f'{link}mince.mp3', 'mince.mp3'))
        self.assertEqual(diki_audio('mince', 'adjective'), (f'{link}mince.mp3', 'mince.mp3'))
        self.assertEqual(diki_audio('concert', ''), (f'{link}concert-n.mp3', 'concert-n.mp3'))
        self.assertEqual(diki_audio('concert', 'noun'), (f'{link}concert-n.mp3', 'concert-n.mp3'))
        self.assertEqual(diki_audio('concert', 'verb'), (f'{link}concert-v.mp3', 'concert-v.mp3'))
        self.assertEqual(diki_audio('concert', 'adjective'), (f'{link}concert-n.mp3', 'concert-n.mp3'))
        self.assertEqual(diki_audio('concert', 'n'), (f'{link}concert-n.mp3', 'concert-n.mp3'))
        self.assertEqual(diki_audio('concert', 'v'), (f'{link}concert-v.mp3', 'concert-v.mp3'))
        self.assertEqual(diki_audio('concert', 'adj'), (f'{link}concert-n.mp3', 'concert-n.mp3'))
        self.assertEqual(diki_audio('invalid', 'n'), (f'{link}invalid-n.mp3', 'invalid-n.mp3'))
        self.assertEqual(diki_audio('invalid', 'adj'), (f'{link}invalid-a.mp3', 'invalid-a.mp3'))
        self.assertEqual(diki_audio('perfect', 'adjective'), (f'{link}perfect-a.mp3', 'perfect-a.mp3'))
        self.assertEqual(diki_audio('perfect', 'v'), (f'{link}perfect-v.mp3', 'perfect-v.mp3'))

    def test_idioms_and_phrasals(self):  # might use last_resort function
        # flags shouldn't interfere
        self.assertEqual(diki_audio('Zip (up) your lip(s)!', ''),
                         (f'{link}zip_your_lip.mp3', 'zip_your_lip.mp3'))
        self.assertEqual(diki_audio('Zip (up) your lip(s)', 'noun'),
                         (f'{link}zip_your_lip.mp3', 'zip_your_lip.mp3'))
        self.assertEqual(diki_audio('Zip (up) your lip(s)', 'v'),
                         (f'{link}zip_your_lip.mp3', 'zip_your_lip.mp3'))
        self.assertEqual(diki_audio('Zip (up) your lip(s)', 'adjective'),
                         (f'{link}zip_your_lip.mp3', 'zip_your_lip.mp3'))
        self.assertEqual(diki_audio('    burst the bubble of (someone) ', ''),
                         (f'{link}burst_somebodys_bubble.mp3', 'burst_somebodys_bubble.mp3'))
        self.assertEqual(diki_audio('burst the bubble of (someone)', 'noun'),
                         (f'{link}burst_somebodys_bubble.mp3', 'burst_somebodys_bubble.mp3'))
        self.assertEqual(diki_audio('account for', ''),
                         (f'{link}account_for_somebody.mp3', 'account_for_somebody.mp3'))
        self.assertEqual(diki_audio('abide by', ''),
                         (f'{link}abide_by_something.mp3', 'abide_by_something.mp3'))
        self.assertEqual(diki_audio('an open marriage', ''), (f'{link}open_marriage.mp3', 'open_marriage.mp3'))
        self.assertEqual(diki_audio('pull (oneself) together', ''),
                         (f'{link}pull_together.mp3', 'pull_together.mp3'))
        self.assertEqual(diki_audio('cast lots', ''), (f'{link}cast_lots.mp3', 'cast_lots.mp3'))
        self.assertEqual(diki_audio('a lot of bunk', ''), ('', ''))
        self.assertEqual(diki_audio('(as) thick as mince', ''), (f'{link}thick.mp3', 'thick.mp3'))
        self.assertEqual(diki_audio('new wine in old wineskins', ''), (f'{link}wineskin.mp3', 'wineskin.mp3'))

    def test_unknown_flags(self):
        self.assertEqual(diki_audio('tap out', 'abbreviation'), (f'{link}tap_out.mp3', 'tap_out.mp3'))
        self.assertEqual(diki_audio('tap out', '--abbreviation'), (f'{link}tap_out.mp3', 'tap_out.mp3'))
        self.assertEqual(diki_audio('tap out', None), (f'{link}tap_out.mp3', 'tap_out.mp3'))
        self.assertEqual(diki_audio('tap out', 0), (f'{link}tap_out.mp3', 'tap_out.mp3'))
        self.assertEqual(diki_audio('tap out', -273.15), (f'{link}tap_out.mp3', 'tap_out.mp3'))


if __name__ == '__main__':
    unittest.main()
