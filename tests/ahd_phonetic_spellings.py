# This file has to be moved to the project's main directory in order to work.
# I have no idea how to get imports to work without fiddling with the sys.path.
# AFAIK it's possible to do.
from src.Dictionaries.ahdictionary import ask_ahdictionary

# Make sure phonetic spelling is separated from 'phrase' field in these cases:
# One headword and one phonetic spelling (trivial case)
ask_ahdictionary(query='garbage')
# Headwords with numbers
ask_ahdictionary(query='key')
# One headword and one phonetic spelling separated by commas
ask_ahdictionary(query='foyer')
# Person headword with pronunciation
ask_ahdictionary(query='wolf')
# Person headword with no pronunciation
ask_ahdictionary(query='monk')
# Long person headword with no pronunciation
ask_ahdictionary(query='beach')
# Two headwords with 'also' and phonetic spelling separated by commas
ask_ahdictionary(query='coconut')
# Two headwords with 'or' and phonetic spelling separated by commas
ask_ahdictionary(query='fjord')
# Only one space between phonetic spelling and headword
ask_ahdictionary(query='incandescent')
# No pronunciation phrase
ask_ahdictionary(query='vicious circle')
# first headword numbered, second not and one phonetic spelling + Informal label
ask_ahdictionary(query='ok')

# with "also"
ask_ahdictionary(query='mastodon')
# first headword numbered, second not and two phonetic spellings
ask_ahdictionary(query='like')

# problematic:
ask_ahdictionary(query='a')
ask_ahdictionary(query='was')
ask_ahdictionary(query='the')
ask_ahdictionary(query='but')
ask_ahdictionary(query='frazzle')
