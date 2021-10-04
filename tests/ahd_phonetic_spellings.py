# This file has to be moved to the project's main directory in order to work.
# I have no idea how to get imports to work without fiddling with the sys.path.
# AFAIK it's possible to do.
from src.Dictionaries.ahdictionary import AHDictionary

# Make sure phonetic spelling is separated from 'phrase' field in these cases:
# One headword and one phonetic spelling (trivial case)
AHDictionary().get_dictionary(query='garbage')
# Headwords with numbers
AHDictionary().get_dictionary(query='key')
# One headword and one phonetic spelling separated by commas
AHDictionary().get_dictionary(query='foyer')
# Person headword with pronunciation
AHDictionary().get_dictionary(query='wolf')
# Person headword with no pronunciation
AHDictionary().get_dictionary(query='monk')
# Long person headword with no pronunciation
AHDictionary().get_dictionary(query='beach')
# Two headwords with 'also' and phonetic spelling separated by commas
AHDictionary().get_dictionary(query='coconut')
# Two headwords with 'or' and phonetic spelling separated by commas
AHDictionary().get_dictionary(query='fjord')
# Only one space between phonetic spelling and headword
AHDictionary().get_dictionary(query='incandescent')
# No pronunciation phrase
AHDictionary().get_dictionary(query='vicious circle')
# first headword numbered, second not and one phonetic spelling + Informal label
AHDictionary().get_dictionary(query='ok')

# with "also"
AHDictionary().get_dictionary(query='mastodon')
# first headword numbered, second not and two phonetic spellings
AHDictionary().get_dictionary(query='like')

# problematic:
AHDictionary().get_dictionary(query='a')
AHDictionary().get_dictionary(query='was')
AHDictionary().get_dictionary(query='the')
AHDictionary().get_dictionary(query='but')
AHDictionary().get_dictionary(query='frazzle')