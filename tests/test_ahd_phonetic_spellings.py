# This file has to be moved to the project's main directory in order to work.
# I have no idea how to get imports to work without fiddling with the sys.path.
# AFAIK it's possible to do.
from ankidodawacz import ah_dictionary

# Make sure phonetic spelling is separated from 'phrase' field in these cases:
# One headword and one phonetic spelling (trivial case)
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'garbage')
# Headwords with numbers
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'key')
# One headword and one phonetic spelling separated by commas
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'foyer')
# Person headword with pronunciation
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'wolf')
# Person headword with no pronunciation
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'monk')
# Long person headword with no pronunciation
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'beach')
# Two headwords with 'also' and phonetic spelling separated by commas
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'coconut')
# Two headwords with 'or' and phonetic spelling separated by commas
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'fjord')
# Only one space between phonetic spelling and headword
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'incandescent')
# No pronunciation phrase
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'vicious circle')

# These are problematic with the current implementation
# Two headwords with 'also' and two phonetic spellings
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'mastodon')
# first headword numbered, second not and two phonetic spellings
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'like')
ah_dictionary('https://www.ahdictionary.com/word/search.html?q=' + 'ok')
