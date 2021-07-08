import unittest

# This file has to be moved to the project's main directory in order to work.
# I have no idea how to get imports to work without fiddling with the sys.path.
# AFAIK it's possible to do.
from ankidodawacz import get_audio_from_diki

link = 'https://www.diki.pl/images-common/en/mp3/'


class TestDikiAudio(unittest.TestCase):

    def test_trivial_cases(self):
        self.assertEqual(get_audio_from_diki('mince', ''), (f'{link}mince.mp3', 'mince.mp3'))
        self.assertEqual(get_audio_from_diki('a blot on the landscape', ''),
                         (f'{link}a_blot_on_the_landscape.mp3', 'a_blot_on_the_landscape.mp3'))
        self.assertEqual(get_audio_from_diki('asdfasdf', 'noun'), ('', ''))
        self.assertEqual(get_audio_from_diki('asdfasdf', 'asdfasdf'), ('', ''))
        self.assertEqual(get_audio_from_diki('', 'asdfasdf'), ('', ''))
        self.assertEqual(get_audio_from_diki('', 'noun'), ('', ''))
        self.assertEqual(get_audio_from_diki('', ''), ('', ''))
        self.assertEqual(get_audio_from_diki('', None), ('', ''))

    def test_noun_verb_adj_functionality(self):
        # all possible flags are: noun, verb, adjective, n, v, adj
        self.assertEqual(get_audio_from_diki('mince', 'noun'), (f'{link}mince.mp3', 'mince.mp3'))
        self.assertEqual(get_audio_from_diki('mince', 'verb'), (f'{link}mince.mp3', 'mince.mp3'))
        self.assertEqual(get_audio_from_diki('mince', 'adjective'), (f'{link}mince.mp3', 'mince.mp3'))
        self.assertEqual(get_audio_from_diki('concert', ''), (f'{link}concert-n.mp3', 'concert-n.mp3'))
        self.assertEqual(get_audio_from_diki('concert', 'noun'), (f'{link}concert-n.mp3', 'concert-n.mp3'))
        self.assertEqual(get_audio_from_diki('concert', 'verb'), (f'{link}concert-v.mp3', 'concert-v.mp3'))
        self.assertEqual(get_audio_from_diki('concert', 'adjective'), (f'{link}concert-n.mp3', 'concert-n.mp3'))
        self.assertEqual(get_audio_from_diki('concert', 'n'), (f'{link}concert-n.mp3', 'concert-n.mp3'))
        self.assertEqual(get_audio_from_diki('concert', 'v'), (f'{link}concert-v.mp3', 'concert-v.mp3'))
        self.assertEqual(get_audio_from_diki('concert', 'adj'), (f'{link}concert-n.mp3', 'concert-n.mp3'))
        self.assertEqual(get_audio_from_diki('invalid', 'n'), (f'{link}invalid-n.mp3', 'invalid-n.mp3'))
        self.assertEqual(get_audio_from_diki('invalid', 'adj'), (f'{link}invalid-a.mp3', 'invalid-a.mp3'))
        self.assertEqual(get_audio_from_diki('perfect', 'adjective'), (f'{link}perfect-a.mp3', 'perfect-a.mp3'))
        self.assertEqual(get_audio_from_diki('perfect', 'v'), (f'{link}perfect-v.mp3', 'perfect-v.mp3'))

    def test_idioms_and_phrasals(self):  # might use last_resort function
        # flags shouldn't interfere
        self.assertEqual(get_audio_from_diki('Zip (up) your lip(s)!', ''),
                         (f'{link}zip_your_lip.mp3', 'zip_your_lip.mp3'))
        self.assertEqual(get_audio_from_diki('Zip (up) your lip(s)', 'noun'),
                         (f'{link}zip_your_lip.mp3', 'zip_your_lip.mp3'))
        self.assertEqual(get_audio_from_diki('Zip (up) your lip(s)', 'v'),
                         (f'{link}zip_your_lip.mp3', 'zip_your_lip.mp3'))
        self.assertEqual(get_audio_from_diki('Zip (up) your lip(s)', 'adjective'),
                         (f'{link}zip_your_lip.mp3', 'zip_your_lip.mp3'))
        self.assertEqual(get_audio_from_diki('    burst the bubble of (someone) ', ''),
                         (f'{link}burst_somebodys_bubble.mp3', 'burst_somebodys_bubble.mp3'))
        self.assertEqual(get_audio_from_diki('burst the bubble of (someone)', 'noun'),
                         (f'{link}burst_somebodys_bubble.mp3', 'burst_somebodys_bubble.mp3'))
        self.assertEqual(get_audio_from_diki('account for', ''),
                         (f'{link}account_for_somebody.mp3', 'account_for_somebody.mp3'))
        self.assertEqual(get_audio_from_diki('abide by', ''),
                         (f'{link}abide_by_something.mp3', 'abide_by_something.mp3'))
        self.assertEqual(get_audio_from_diki('an open marriage', ''), (f'{link}open_marriage.mp3', 'open_marriage.mp3'))
        self.assertEqual(get_audio_from_diki('pull (oneself) together', ''),
                         (f'{link}pull_together.mp3', 'pull_together.mp3'))
        self.assertEqual(get_audio_from_diki('cast lots', ''), (f'{link}cast_lots.mp3', 'cast_lots.mp3'))
        self.assertEqual(get_audio_from_diki('a lot of bunk', ''), ('', ''))
        self.assertEqual(get_audio_from_diki('(as) thick as mince', ''), (f'{link}thick.mp3', 'thick.mp3'))

    def test_unknown_flags(self):
        self.assertEqual(get_audio_from_diki('tap out', 'abbreviation'), (f'{link}tap_out.mp3', 'tap_out.mp3'))
        self.assertEqual(get_audio_from_diki('tap out', '--abbreviation'), (f'{link}tap_out.mp3', 'tap_out.mp3'))
        self.assertEqual(get_audio_from_diki('tap out', None), (f'{link}tap_out.mp3', 'tap_out.mp3'))
        self.assertEqual(get_audio_from_diki('tap out', 0), (f'{link}tap_out.mp3', 'tap_out.mp3'))
        self.assertEqual(get_audio_from_diki('tap out', -2.453), (f'{link}tap_out.mp3', 'tap_out.mp3'))


if __name__ == '__main__':
    unittest.main()
