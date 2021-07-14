# This file has to be moved to the project's main directory in order to work.
# I have no idea how to get imports to work without fiddling with the sys.path.
# AFAIK it's possible to do.
from ankidodawacz import ah_dictionary

# Make sure phonetic spelling is separated from 'phrase' field in these cases:
# One headword and one phonetic spelling (trivial case)
ah_dictionary('garbage')
# Headwords with numbers
ah_dictionary('key')
# One headword and one phonetic spelling separated by commas
ah_dictionary('foyer')
# Person headword with pronunciation
ah_dictionary('wolf')
# Person headword with no pronunciation
ah_dictionary('monk')
# Long person headword with no pronunciation
ah_dictionary('beach')
# Two headwords with 'also' and phonetic spelling separated by commas
ah_dictionary('coconut')
# Two headwords with 'or' and phonetic spelling separated by commas
ah_dictionary('fjord')
# Only one space between phonetic spelling and headword
ah_dictionary('incandescent')
# No pronunciation phrase
ah_dictionary('vicious circle')
# first headword numbered, second not and one phonetic spelling + Informal thingy
ah_dictionary('ok')

# These are problematic with the current implementation
# Two headwords with 'also' and two phonetic spellings
ah_dictionary('mastodon')
# first headword numbered, second not and two phonetic spellings
ah_dictionary('like')

