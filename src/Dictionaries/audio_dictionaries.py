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

import os.path

import requests
from bs4 import BeautifulSoup

from src.Dictionaries.utils import handle_connection_exceptions
from src.Dictionaries.utils import request_soup, request_session
from src.colors import \
    R, YEX, \
    err_c
from src.data import config, USER_AGENT


@handle_connection_exceptions
def diki_request(full_url):
    reqs = requests.get(full_url, headers=USER_AGENT, timeout=10)
    soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    return soup.find_all('span', class_='audioIcon icon-sound dontprint soundOnClick')


#
# Diki needs a hardcore refactor
#
def diki_audio(raw_phrase, flag, url='https://www.diki.pl/slownik-angielskiego?q='):
    def find_audio_url(filename, aurls):
        flag_values = {'noun': 'n', 'verb': 'v',
                       'adj': 'a', 'adjective': 'a'}
        search_flag = flag_values.get(flag, flag)
        dk = filename
        aurl = ''
        if flag and len(dk.split('_')) == 1:
            dk = f"{dk.split('_')[0]}-{search_flag}.mp3"
        for recording in aurls:
            if dk in str(recording):
                aurl = recording
                break
        if flag and len(dk.split('_')) == 1 and not aurl:
            pos = {'n': 'noun', 'v': 'verb', 'a': 'adjective'}
            print(f"{YEX.color}Diki nie posiada wymowy dla: {R}{raw_phrase} "
                  f"'{pos.get(search_flag, 'Kaczakonina')}'\n{YEX.color}Szukam {R}{raw_phrase}")
            return aurls[0] if aurls else aurls
        return aurl

    def get_url_end(aurl):
        try:
            end_of_url = str(aurl).split('data-audio-url=')[1]
            end_of_url = end_of_url.split(' tabindex')[0].strip('"')
            return end_of_url
        except IndexError:
            # url not found
            return None

    def last_resort():
        paren_numb = raw_phrase.count(')')
        if paren_numb == 1:
            if raw_phrase.startswith('('):
                attempt = raw_phrase.split(')')[-1]
            elif raw_phrase.endswith(')'):
                attempt = raw_phrase.split('(')[0]
            else:
                attempt = raw_phrase.split('(')[0] + raw_phrase.split(')')[-1]
        elif paren_numb > 1:
            # boil (something) down to (something) -> boil down to
            # Zip (up) your lip(s) -> Zip your lip
            split_phrase = raw_phrase.split('(')
            second_sp = ''
            for sp in split_phrase[:2]:
                second_sp = sp.split(')')[-1]
            attempt = split_phrase[0] + second_sp.rstrip()
        else:  # 0
            longest_word = max(raw_phrase.split(' '), key=len)
            if longest_word not in ('somebody', 'something'):
                attempt = longest_word
            else:
                attempt = raw_phrase
        return attempt

    def get_audio_url(_search_phrase, search_by_filename=True):
        _diki_phrase = _search_phrase.strip()
        audio_urls = diki_request(full_url=url + _diki_phrase)
        if audio_urls is None:
            return None, None
        if not search_by_filename:
            return (_diki_phrase, audio_urls[0]) if audio_urls else (_diki_phrase, audio_urls)
        # Cannot remove the apostrophe earlier cause diki needs it during search
        filename = '_'.join(_diki_phrase.split(' ')).replace("'", "").lower()
        aurl = find_audio_url(filename, aurls=audio_urls)
        return _diki_phrase, aurl

    search_phrase = raw_phrase.replace('(', '').replace(')', '') \
        .replace(' or something', '').replace('someone', 'somebody')
    diki_phrase, audio_url = get_audio_url(search_phrase)
    if diki_phrase is None:
        return '', ''

    if not audio_url:
        print(f'{err_c.color}Diki nie posiada pożądanego audio\n{YEX.color}Spróbuję dodać co łaska...\n')
    if not audio_url and search_phrase.startswith('an '):
        diki_phrase, audio_url = get_audio_url(search_phrase.replace('an ', '', 1))
    if not audio_url and 'lots' in search_phrase:
        diki_phrase, audio_url = get_audio_url(search_phrase.replace('lots', 'a lot'))
    if not audio_url and "don't" in search_phrase:
        diki_phrase, audio_url = get_audio_url(search_phrase.replace("don't ", ""))
    if not audio_url and ' of' in search_phrase:
        diki_phrase, audio_url = get_audio_url(search_phrase.replace(' of', ''), search_by_filename=False)
    if not audio_url:
        # diki_phrase is just the first argument of get_audio_url()
        diki_phrase, audio_url = get_audio_url(last_resort(), search_by_filename=False)

    url_end = get_url_end(audio_url)  # e.g. /images-common/en/mp3/confirm.mp3
    if url_end is None:
        print(f"{err_c.color}Nie udało się pozyskać audio\nKarta zostanie dodana bez audio")
        return '', ''
    audiofile_name = url_end.split('/')[-1]  # e.g. confirm.mp3
    audiofile_name_no_mp3 = audiofile_name.split('.mp3')[0].replace('-n', '').replace('-v', '').replace('-a', '')
    last_word_in_dphrase = diki_phrase.split()[-1]
    # We need to check if audio was added in full to prevent garbage's stubs from slipping through
    # e.g. "as" from "as thick as mince", I would rather go with "thick" or "mince" as it's more substantial
    audiofile_added_in_full = audiofile_name_no_mp3.endswith(last_word_in_dphrase)
    # Phrases like "account for", "abide by" in diki show up as "account for somebody", "abide by something" etc.
    # audiofile_added_in_full check prevents these from being handled properly
    if len(audiofile_name_no_mp3.split('_')) >= len(search_phrase.split()) and \
            audiofile_name_no_mp3.split('_')[-1] in ('something', 'somebody'):
        pass
    elif not audiofile_added_in_full and len(audiofile_name_no_mp3) > 4 or audiofile_added_in_full:
        pass
    else:
        print(f"{err_c.color}Nie udało się pozyskać audio\nKarta zostanie dodana bez audio")
        return '', ''

    audio_link = 'https://www.diki.pl' + url_end
    return audio_link, audiofile_name


def save_audio(audio_link, audiofile_name):
    try:
        with open(os.path.join(config['audio_path'], audiofile_name), 'wb') as file:
            response = request_session.get(audio_link)
            file.write(response.content)
        return f'[sound:{audiofile_name}]'
    except FileNotFoundError:
        print(f"{err_c.color}Zapisywanie pliku audio {R}{audiofile_name}{err_c.color} nie powiodło się\n"
              f"Aktualna ścieżka zapisu audio: {R}{config['audio_path']}\n"
              f"{err_c.color}Upewnij się, że taki folder istnieje i spróbuj ponownie\n")
        return ''
    except Exception:
        print(f'{err_c.color}Wystąpił nieoczekiwany błąd podczas zapisywania audio')
        raise


def ahd_audio(query):
    soup = request_soup('https://www.ahdictionary.com/word/search.html?q=' + query)
    audio_url = soup.find('a', {'target': '_blank'}).get('href')
    if audio_url == 'http://www.hmhco.com':
        print(f'{err_c.color}AHD nie posiada audio dla {R}{query}\n'
              f'{YEX.color}Sprawdzam diki...')
        return diki_audio(raw_phrase=query, flag='')

    audio_url = 'https://www.ahdictionary.com' + audio_url
    return audio_url, audio_url.rsplit('/')[-1]


def lexico_audio(query):
    soup = request_soup('https://www.lexico.com/definition/' + query.replace(' ', '_'))
    audio_url = soup.find('audio')
    if audio_url is None:
        print(f'{err_c.color}Lexico nie posiada audio dla {R}{query}\n'
              f'{YEX.color}Sprawdzam diki...')
        return diki_audio(raw_phrase=query, flag='')

    audio_url = audio_url.get('src')
    return audio_url, audio_url.rsplit('/')[-1]
