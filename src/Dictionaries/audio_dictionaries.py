# Copyright 2021 Gryzus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import binascii
import os.path

import src.anki_interface as anki
from src.Dictionaries.utils import request_soup, request_session
from src.colors import R, YEX, err_c
from src.data import config


def diki_audio(raw_phrase, flag=''):
    diki_phrase = raw_phrase.lower()\
        .replace('(', '').replace(')', '').replace("'", "") \
        .replace(' or something', '')\
        .replace('someone', 'somebody')\
        .strip(' !?.')\
        .replace(' ', '_')

    url = f'https://www.diki.pl/images-common/en/mp3/{diki_phrase}{flag}.mp3'
    url_ame = f'https://www.diki.pl/images-common/en-ame/mp3/{diki_phrase}{flag}.mp3'
    # First try British pronunciation, then American
    if request_session.head(url).status_code == 200 or \
       request_session.head(url_ame).status_code == 200:
        return url

    if flag:
        # Try the same but without the flag
        url = f'https://www.diki.pl/images-common/en/mp3/{diki_phrase}.mp3'
        url_ame = f'https://www.diki.pl/images-common/en-ame/mp3/{diki_phrase}.mp3'
        if request_session.head(url).status_code == 200 or \
           request_session.head(url_ame).status_code == 200:
            return url

    print(f'{err_c}Diki does not have the desired pronunciation\n'
          f'{YEX}Squeezing the last bits out...')

    def shorten_to_possessive(*args):
        verb, _, rest = diki_phrase.partition('_the_')
        if not rest:
            return verb
        noun, _, sb = rest.partition('_of_')
        return f'{verb}_{sb}s_{noun}'.strip(' _')

    def get_longest_word(*args):
        # Returning diki_phrase here essentially means diki doesn't have the audio.
        s = max(diki_phrase.split('_'), key=len)
        if len(s) < 4 or s.startswith('some') or s.startswith('onesel'):
            return diki_phrase
        return s

    salvage_methods = (
        lambda x: x + '_somebody' if x.endswith('_for') else x,
        lambda x: x + '_something' if x.endswith('_by') else x,
        lambda x: x.replace('an_', '', 1) if x.startswith('an_') else x,
        lambda x: x.replace('_up_', '_'),
        lambda x: x.replace('_ones_', '_somebodys_'),
        lambda x: x.rstrip('s'),
        shorten_to_possessive,
        get_longest_word,
    )

    last_phrase = ''
    for method in salvage_methods:
        diki_phrase = method(diki_phrase)
        # To avoid making unnecessary requests, continue if nothing in the url has changed.
        if last_phrase == diki_phrase:
            continue
        else:
            last_phrase = diki_phrase

        url = f'https://www.diki.pl/images-common/en/mp3/{diki_phrase}.mp3'
        if request_session.head(url).status_code == 200:
            return url

    print(f"{err_c}Diki does not have the pronunciation for {R}{raw_phrase}")
    return ''


def save_audio_url(audio_url):
    filename = audio_url.rsplit('/', 1)[-1]
    audio_content = request_session.get(audio_url).content
    audio_path = config['audio_path']

    # Use AnkiConnect to save audio files if 'collection.media' path isn't given.
    # Specifying audio_path is preferred as it's way faster.
    if config['ankiconnect'] and os.path.basename(audio_path) != 'collection.media':
        _, err = anki.invoke('storeMediaFile',
                             filename=filename,
                             data=binascii.b2a_base64(  # convert to base64 string
                                 audio_content, newline=False).decode())
        if err is None:
            return f'[sound:{filename}]'

    try:
        with open(os.path.join(audio_path, filename), 'wb') as file:
            file.write(audio_content)
        return f'[sound:{filename}]'
    except FileNotFoundError:
        print(f"{err_c}Saving audio {R}{filename}{err_c} failed\n"
              f"Current audio path: {R}{audio_path}\n"
              f"{err_c}Make sure the directory exists and try again\n")
        return ''
    except Exception:
        print(f'{err_c}Unexpected error occurred while saving audio')
        raise


def ahd_audio(query):
    soup = request_soup('https://www.ahdictionary.com/word/search.html?q=' + query)
    audio_url = soup.find('a', {'target': '_blank'}).get('href')
    if audio_url == 'http://www.hmhco.com':
        print(f'{err_c}AHD does not have the pronunciation for {R}{query}\n'
              f'{YEX}Querying diki...')
        return diki_audio(query)
    return 'https://www.ahdictionary.com' + audio_url


def lexico_audio(query):
    soup = request_soup('https://www.lexico.com/definition/' + query.replace(' ', '_'))
    audio_url = soup.find('audio')
    if audio_url is None:
        print(f'{err_c}Lexico does not have the pronunciation for {R}{query}\n'
              f'{YEX}Querying diki...')
        return diki_audio(query)
    return audio_url.get('src')
