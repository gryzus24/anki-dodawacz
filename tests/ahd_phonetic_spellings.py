# This file has to be moved to the project's main directory in order to work.
# I have no idea how to get imports to work without fiddling with the sys.path.
# AFAIK it's possible to do.
from ankidodawacz import ahdictionary

# Make sure phonetic spelling is separated from 'phrase' field in these cases:
# One headword and one phonetic spelling (trivial case)
ahdictionary('garbage')
# Headwords with numbers
ahdictionary('key')
# One headword and one phonetic spelling separated by commas
ahdictionary('foyer')
# Person headword with pronunciation
ahdictionary('wolf')
# Person headword with no pronunciation
ahdictionary('monk')
# Long person headword with no pronunciation
ahdictionary('beach')
# Two headwords with 'also' and phonetic spelling separated by commas
ahdictionary('coconut')
# Two headwords with 'or' and phonetic spelling separated by commas
ahdictionary('fjord')
# Only one space between phonetic spelling and headword
ahdictionary('incandescent')
# No pronunciation phrase
ahdictionary('vicious circle')
# first headword numbered, second not and one phonetic spelling + Informal thingy
ahdictionary('ok')

ahdictionary('mastodon')
# first headword numbered, second not and two phonetic spellings
ahdictionary('like')

# problematic:
ahdictionary('a')
ahdictionary('was')
ahdictionary('the')
ahdictionary('but')
