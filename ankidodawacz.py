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

import os
import os.path
import sys

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError as requestsConnectError
from requests.exceptions import Timeout

import src.anki_interface as anki
import src.commands as c
import src.data as data
import src.ffmpeg_interface as ffmpeg
import src.help as h
from src.colors import \
    R, BOLD, END, YEX, GEX, \
    def1_c, def2_c, pos_c, etym_c, syn_c, psyn_c, \
    pidiom_c, syngloss_c, synpos_c, index_c, phrase_c, \
    phon_c, poslabel_c, err_c, delimit_c, input_c, inputtext_c
from src.data import config

if sys.platform.startswith('linux'):
    # For saving command history, this module doesn't work on windows
    import readline
    readline.read_init_file()

USER_AGENT = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'}
requests_session_ah = requests.Session()
requests_session_ah.headers.update(USER_AGENT)
# Globals for main function to modify
skip = 0
skip_wordnet = 0
phrase = ''

commands = {
    # commands that take arguments
    '--delete-last': c.delete_cards, '--delete-recent': c.delete_cards,
    '-textwidth': c.set_width_settings,
    '-indent': c.set_width_settings,
    '-delimsize': c.set_width_settings,
    '-center': c.set_width_settings,
    '-note': c.set_free_value_commands,
    '-deck': c.set_free_value_commands,
    '-tags': c.set_free_value_commands,
    '--audio-path': c.set_audio_path, '-ap': c.set_audio_path,
    '-dupescope': c.set_text_value_commands,
    '-server': c.set_text_value_commands,
    '-quality': c.set_text_value_commands,
    '--add-note': anki.add_notes,
    '--field-order': c.change_field_order, '-fo': c.change_field_order,
    '-color': c.set_colors, '-c': c.set_colors,
    '--config-bulk': c.config_bulk, '--config-defaults': c.config_bulk, '-cd': c.config_bulk, '-cb': c.config_bulk,
    '--audio-device': ffmpeg.set_audio_device, '-device': ffmpeg.set_audio_device,
    # commands that take no arguments
    '-refresh': anki.refresh_notes,
    '--help': h.quick_help, '-help': h.quick_help, '-h': h.quick_help,
    '--help-bulk': h.bulk_help, '--help-defaults': h.bulk_help,
    '--help-commands': h.commands_help, '--help-command': h.commands_help,
    '--help-recording': h.recording_help,
    '-config': c.print_config_representation, '-conf': c.print_config_representation,
}


def search_interface() -> list:
    while True:
        word = input(f'{input_c.color}Szukaj ${inputtext_c.color} ').strip()
        if not word:
            continue
        args = word.split()
        cmd = args[0]
        try:
            if cmd in tuple(data.command_data)[:26]:
                # to avoid writing all of them in the commands dict above
                c.boolean_commands(*args)
            # don't forget to change the splice when adding/removing commands
            elif cmd in tuple(commands)[:25]:
                commands[cmd](*args)
            else:
                commands[cmd]()
        except KeyError:
            # command not found
            return word.split(' -')


def get_audio_response(audio_link, audiofile_name):
    try:
        with open(os.path.join(config['audio_path'], audiofile_name), 'wb') as file:
            response = requests_session_ah.get(audio_link)
            file.write(response.content)
        return f'[sound:{audiofile_name}]'
    except FileNotFoundError:
        print(f"{err_c.color}Zapisywanie pliku audio {R}{audiofile_name} {err_c.color}nie powiodło się\n"
              f"Aktualna ścieżka zapisu audio to {R}{config['audio_path']}\n"
              f"{err_c.color}Upewnij się, że taki folder istnieje i spróbuj ponownie\n")
        return ''
    except Exception:
        print(f'{err_c.color}Wystąpił nieoczekiwany błąd podczas zapisywania audio')
        raise


def get_audio_from_diki(raw_phrase, flag, url='https://www.diki.pl/slownik-angielskiego?q='):
    def diki_request(full_url):
        try:
            reqs = requests.get(full_url, headers=USER_AGENT, timeout=10)
            soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
            return soup.find_all('span', class_='audioIcon icon-sound dontprint soundOnClick')
        except requestsConnectError:
            print(f'{err_c.color}Diki zerwało połączenie\n'
                  f'zmień serwer audio lub zrestartuj program i spróbuj ponownie')
        except Timeout:
            print(f'{err_c.color}Diki nie odpowiada\n'
                  f'zmień serwer audio lub zrestartuj program i spróbuj ponownie')

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
        if not search_by_filename:
            return (_diki_phrase, audio_urls[0]) if audio_urls else (_diki_phrase, audio_urls)
        # Cannot remove the apostrophe earlier cause diki needs it during search
        filename = '_'.join(_diki_phrase.split(' ')).replace("'", "").lower()
        aurl = find_audio_url(filename, aurls=audio_urls)
        return _diki_phrase, aurl

    search_phrase = raw_phrase.replace('(', '').replace(')', '') \
        .replace(' or something', '').replace('someone', 'somebody')
    diki_phrase, audio_url = get_audio_url(search_phrase)
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


def audio_ahd(query):
    full_url = 'https://www.ahdictionary.com/word/search.html?q=' + query
    reqs = requests_session_ah.get(full_url)
    soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    audio_raw = soup.find('a', {'target': '_blank'}).get('href')
    if audio_raw == 'http://www.hmhco.com':
        print(f"{err_c.color}AH Dictionary nie posiada pożądanego audio\n{YEX.color}Sprawdzam diki...")
        return get_audio_from_diki(raw_phrase=phrase, flag='')
    audiofile_name = audio_raw.split('/')[-1]
    audiofile_name = audiofile_name.split('.')[0] + '.wav'
    audio_link = 'https://www.ahdictionary.com'
    audio_link += audio_raw
    return audio_link, audiofile_name


def lexico_flags(flag, pronunciations, word_pos, p_and_p):
    flag_pos_vals = {'n': 'noun', 'noun': 'noun', 'v': 'verb', 'verb': 'verb',
                     'adj': 'adjective', 'adjective': 'adjective', 'adv': 'adverb', 'adverb': 'adverb',
                     'abbr': 'abbreviation', 'abbreviation': 'abbreviation'}
    pos = flag_pos_vals[flag]
    lx_audio = pronunciations

    x = False
    for pronun in pronunciations:
        # x shows up in words that are pronounced based on their part of speech
        # e.g. verb = conCERT, noun = CONcert
        # three letters is enough to distinguish every word combination,
        # whole phrases should work too, but lexico's naming convention is very unpredictable
        if 'x' + phrase[:3] in str(pronun):
            x = True
            break

    if not x:
        audio_numb = -1
        for wp in word_pos:
            if wp.text not in flag_pos_vals.values():
                audio_numb += 1
                continue
            if wp.text.startswith(pos):
                lx_audio = pronunciations[audio_numb]
                break
    else:
        if pos == 'noun' or pos == 'adjective' and phrase not in ('invalid', 'minute', 'complex'):
            for i, n in enumerate(p_and_p):
                if n.text.startswith("/ˈ"):
                    lx_audio = p_and_p[i + 1]
                    break
        else:
            for i, n in enumerate(p_and_p):
                # checks only for fields in phonetics
                if n.text == '':
                    continue
                if not n.text.startswith("/ˈ"):
                    lx_audio = p_and_p[i + 1]
                    break
    if lx_audio == pronunciations:
        print(f"{YEX.color}Lexico nie posiada wymowy dla: {R}{phrase} '{pos}'\n{YEX.color}Szukam {R}{phrase}")
    return list(lx_audio)[0] if lx_audio else lx_audio


def audio_lexico(query, flag):
    full_url = 'https://www.lexico.com/definition/' + query
    reqs = requests.get(full_url, headers=USER_AGENT)
    soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    relevant_content = soup.find('div', class_='entryWrapper')
    if flag == '':
        lx_audio = relevant_content.find('a', class_='speaker')
    else:
        word_pos = relevant_content.find_all('span', class_=['hw', 'pos'])
        pronunciations = relevant_content.find_all('a', class_='speaker')
        phonetics_and_pronunciations = relevant_content.select('span.phoneticspelling, a.speaker')
        # phonetics_and_pronunciations sometimes come with empty indexes
        phonetics_and_pronunciations = [x for x in phonetics_and_pronunciations if x != '']

        lx_audio = lexico_flags(flag, pronunciations, word_pos, phonetics_and_pronunciations)

    if lx_audio is None:
        print(f"{err_c.color}Lexico nie posiada pożądanego audio\n{YEX.color}Sprawdzam diki...")
        return get_audio_from_diki(raw_phrase=phrase, flag=flag)
    full_audio_link = str(lx_audio).split('src="')[-1].split('">')[0]
    audiofile_name = full_audio_link.split('/')[-1]
    return full_audio_link, audiofile_name


def get_flag_from(flags, server):
    available_flags = ('n', 'v', 'adj', '-noun', '-verb', '-adjective',
                       'adv', 'abbr', '-adverb', '-abbreviation')
    if server == 'diki':
        available_flags = available_flags[:6]
    try:
        flag = [x.strip('-') for x in flags if x in available_flags][0]
        return flag
    except IndexError:
        return ''


def search_for_audio(server, phrase_, flags):
    if not config['add_audio']:
        return ''

    if server == 'ahd':
        audio_link, audiofile_name = audio_ahd(phrase_)
    elif server == 'lexico':
        flag = get_flag_from(flags, server)
        audio_link, audiofile_name = audio_lexico(phrase_.replace(' ', '_'), flag)
    else:  # diki
        flag = get_flag_from(flags, server)
        audio_link, audiofile_name = get_audio_from_diki(phrase_, flag)

    if not audiofile_name:
        return ''
    return get_audio_response(audio_link, audiofile_name)


def wrap_lines(string: str, term_width, index_width, indent, gap):
    if not config['wraptext']:
        return string
    # Gap is the gap between indexes and strings
    real_width = int(term_width) - index_width - gap
    if len(string) < real_width:
        return string

    wrapped_text = ''
    indent_ = indent + index_width
    # split(' ') to accommodate for more than one whitespace,
    # split() can be used for consistent spacing
    string_divided = string.split(' ')
    # Current line length
    current_llen = 0
    for word, nextword in zip(string_divided, string_divided[1:]):
        # 1 is a missing space from string.split(' ')
        current_llen += len(word) + 1
        if len(nextword) + current_llen > real_width:
            wrapped_text += word + '\n' + indent_ * ' '
            current_llen = indent - gap
        else:
            wrapped_text += word + ' '
            # Definition + the last word
    return wrapped_text + string_divided[-1]


def ah_def_print(indexing, term_width, definition):
    definition_aw = wrap_lines(definition, term_width, len(str(indexing)),
                               indent=config['indent'], gap=2)
    if indexing % 2 == 1:
        print(f'{index_c.color}{indexing}  {def1_c.color}{definition_aw}')
    else:
        print(f'{index_c.color}{indexing}  {def2_c.color}{definition_aw}')


def terminal_width() -> int:
    try:
        term_width = str(config['textwidth'])
    except KeyError:
        # First exception that crops up when there is no config.yml
        print(f'{err_c.color}Plik {R}config.yml{err_c.color} jest niekompletny\n'
              f'Wypełnij plik konfiguracyjny')
        return 79

    try:
        # this is an integer
        term_width_auto = os.get_terminal_size()[0]
    except OSError:
        if '* auto' in term_width:
            print(f"{err_c.color}Wystąpił problem podczas pozyskiwania szerokości okna\n"
                  f"aby wybrać szerokość inną niż {R}{term_width.rstrip('* auto')}{err_c.color} użyj {R}-textwidth {{wartość}}")
            c.save_commands(entry='textwidth', value=term_width.rstrip('* auto'))
        return int(term_width.rstrip('* auto'))
    else:
        if '* auto' in term_width:
            c.save_commands(entry='textwidth', value=f'{term_width_auto}* auto')
            return term_width_auto
        elif int(term_width.rstrip('* auto')) > term_width_auto:
            term_width = term_width_auto
            c.save_commands(entry='textwidth', value=str(term_width))
        return int(term_width)


def get_conf_of(entry: str) -> int:
    value = config[entry]
    # Makes sure width options are an integer
    string = str(value).rstrip('* auto')
    return int(string)


def filter_ahd(definition):
    rex = definition.lstrip('1234567890.')
    rex = rex.split(' See Usage Note at')[0]
    rex = rex.split(' See Synonyms at')[0]
    for letter in ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l'):
        rex = rex.replace(f":{letter}. ", ": |")
        rex = rex.replace(f".{letter}. ", ". |")
        rex = rex.replace(f" {letter}. ", " ")
        # when definition has an example with a '?', there's no space in between
        rex = rex.replace(f"?{letter}. ", "? |")
    return rex.strip()


def manage_display_parameters(term_width):
    if config['indent'] > term_width // 2:
        c.save_commands(entry='indent', value=term_width // 2)
    if '* auto' in str(config['delimsize']):
        c.save_commands(entry='delimsize', value=f'{term_width}* auto')
    if '* auto' in str(config['center']):
        c.save_commands(entry='center', value=f'{term_width}* auto')


def ah_dictionary_request(url):
    try:
        reqs = requests_session_ah.get(url, timeout=10)
        soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
        word_check = soup.find('div', {'id': 'results'})

        if word_check.text == 'No word definition found':
            print(f'{err_c.color}Nie znaleziono podanego hasła w AH Dictionary\n{YEX.color}Szukam w idiomach...')
            return None

        return soup
    except ConnectionError:
        print(f'{err_c.color}Nie udało się połączyć ze słownikiem, sprawdź swoje połączenie i spróbuj ponownie')
    except requestsConnectError:
        print(f'{err_c.color}AH Dictionary zerwał połączenie\n'
              f'Zmień słownik lub zrestartuj program i spróbuj ponownie')
    except Timeout:
        print(f'{err_c.color}AH Dictionary nie odpowiada')
    except Exception:
        print(f'{err_c.color}Wystąpił nieoczekiwany błąd')
        raise


def ah_dictionary(query):
    global skip

    full_url = 'https://www.ahdictionary.com/word/search.html?q=' + query
    soup = ah_dictionary_request(full_url)
    if soup is None:
        skip = 1
        return [], [], [], []

    defs = []
    poses = []
    etyms = []
    phrase_list = []
    term_width = terminal_width()
    manage_display_parameters(term_width)

    indexing = 0
    # whether 'results for (phrase)' was printed
    results_for_printed = False

    tds = soup.find_all('td')
    for td in tds:
        print(f'{delimit_c.color}{get_conf_of("delimsize") * "-"}')

        hpaps = td.find('div', class_='rtseg')
        # hpaps = head phrase and phonetic spelling
        # example hpaps: bat·ter 1  (băt′ər)
        # example person hpaps: Monk  (mŭngk), (James) Arthur  Known as  "Art."  Born 1957.
        hpaps = hpaps.text.split('Share:')[0] \
            .replace('', '′').replace('', 'ōō').replace('', 'ōō').strip()

        phon_spell = '(' + hpaps.split(')')[0].split(' (')[-1].strip() + ')'
        if phon_spell.strip('()') == hpaps:
            phon_spell = ''
        # get rid of phonetic spelling and then clean up
        # (when hpaps is a person cleanup is necessary)
        head_word = hpaps.replace(phon_spell, '').replace('  ,', ',') \
            .replace('  ', ' ').replace('  ', ' ').replace(', ', ' ', 1).strip()
        # removes numbers from headwords. AHD uses NBSP before a number
        if ' ' in head_word:
            phrase_ = head_word.split(' ')
            part2 = phrase_[1].lstrip('1234567890')
            phrase_ = phrase_[0].replace('·', '') + part2
        else:
            phrase_ = head_word.replace('·', '')

        if not results_for_printed:
            ahd = 'AH Dictionary'
            print(f'{BOLD}{ahd.center(get_conf_of("center"))}{END}')
            if phrase_.lower() != query.lower():
                print(f' {BOLD}Wyniki dla {phrase_c.color}{phrase_.split()[0]}{END}')
            results_for_printed = True
        print(f' {phrase_c.color}{head_word.strip()}  {phon_c.color}{phon_spell}')

        gloss_blocks = td.find_all('div', class_='pseg')
        for block in gloss_blocks:
            definitions = block.find_all('div', class_=('ds-list', 'ds-single'))
            pos_label = block.find_all('i', recursive=False)
            # verbs always come with a 'tr.' or 'intr.' label,
            # additionally, verbs are supplied with an explicit 'v.'
            # that I want to ignore to avoid duplication
            pos_label = [x.text.strip() for x in pos_label
                         if x.text.strip() and x.text.strip() != 'v.']
            if pos_label:
                pos_label = ' '.join(pos_label)
                if pos_label in ('tr.', 'intr.'):
                    pos_label += 'v.'
                if not config['compact']:
                    print()
                print(f'{len(str(indexing)) * " "}{poslabel_c.color}{pos_label}')
            # Adds definitions and phrases
            for gloss in definitions:
                indexing += 1
                # 'all right' needs the first replace
                # 'long' needs the second one
                rex = gloss.text.replace('', '′').replace('', 'ōō').replace('', '′').strip()
                if config['filtered_dictionary']:
                    rex = filter_ahd(rex)
                # We have to find the private symbol
                ah_def_print(indexing, term_width, definition=rex)  # .replace('', ''))
                defs.append(rex)
                phrase_list.append(phrase_)

        print()
        # Adds parts of speech
        for pos in td.find_all('div', class_='runseg'):
            postring = pos.text.replace('', 'ōō').replace('', 'ōō').replace('', '′').replace('·', '').strip()
            print(f' {pos_c.color}{postring}')
            poses.append(postring)
        if poses:
            print()
        # Adds etymologies
        for etym in td.find_all('div', class_='etyseg'):
            print(f' {etym_c.color}'
                  f'{wrap_lines(etym.text, term_width, 0, 1, 1)}')
            etyms.append(etym.text)
    # So that newline is not printed in glosses without etymologies
    if etyms:
        print()
    return defs, poses, etyms, phrase_list


def hide_phrase_in(func):
    def wrapper(*args, **kwargs):
        def content_replace(a: str, b: str) -> str:
            return content.replace(a, b).replace(a.capitalize(), b).replace(a.upper(), b.upper())

        content, choice, hide = func(*args, **kwargs)
        if hide is None or not content or not config[hide]:
            return content, choice

        nonoes = (
            'the', 'and', 'a', 'is', 'an', 'it',
            'or', 'be', 'do', 'does', 'not', 'if'
        )

        words_in_phrase = phrase.lower().split()
        for word in words_in_phrase:
            if word.lower() in nonoes:
                continue

            if not config['hide_prepositions']:
                if word.lower() in data.prepositions:
                    continue

            content = content_replace(word, '...')
            if word.endswith('e'):
                content = content_replace(word[:-1] + 'ing', '...ing')
                if word.endswith('ie'):
                    content = content_replace(word[:-2] + 'ying', '...ying')
            elif word.endswith('y'):
                content = content_replace(word[:-1] + 'ies', '...ies')
                content = content_replace(word[:-1] + 'ied', '...ied')

        return content, choice

    return wrapper


@hide_phrase_in
def sentence_input(hide):
    global skip

    if not config['add_sentences']:
        return '', 0, hide

    sentence = input(f'{input_c.color}Dodaj przykładowe zdanie:{inputtext_c.color} ')
    if sentence.lower() == '-s':
        print(f'{GEX.color}Pominięto dodawanie zdania')
        sentence = ''
    if sentence.lower() == '-sc':
        skip = 1
        print(f'{GEX.color}Pominięto dodawanie karty')
        sentence = ''
    return sentence, 0, hide


def pick_phrase(choice, phrase_list):
    try:
        ch = int(choice)
        if len(phrase_list) >= ch > 0:
            return phrase_list[ch - 1]
        return phrase_list[0]
    except ValueError:
        return phrase_list[0]


def filter_range_tuples(tup):
    # when input is 2:3, 5, 6, qwerty, 7:9, tuples are:
    # ('2', '3'), (' 5'), (' 6'), ('qwerty'), ('7', '9')
    for val in tup:
        # zero is excluded in multi_choice function, otherwise tuples like:
        # ('0', '4') would be ignored, but I want them to produce: 1, 2, 3, 4
        if not val.strip().isnumeric():
            return False
    return True


def get_full_range(choice, content_list_len):
    # example input: 1:4:2, 4:0, d:3:7, 5:aaa, 1:6:2:8
    colon_sep_values = choice.split(',')
    colon_range_tuples = [tuple(t.split(':')) for t in colon_sep_values]
    # gets rid of invalid tuples eg: d:3:7, 5:aaa
    col_tuples = list(filter(filter_range_tuples, colon_range_tuples))
    # converts every tuple of len > 2 into tuples
    # with overlapping values: 2:8:5:6 -> (2,8) (8,5) (5,6)
    list_of_tuples = []
    for ctuple in col_tuples:
        if len(ctuple) == 1:
            list_of_tuples.append(ctuple)
            continue
        for t in range(0, len(ctuple) - 1):
            list_of_tuples.append(ctuple[0 + t:2 + t])

    full_range = []
    for ctuple in list_of_tuples:
        val1 = int(ctuple[0])
        # -1 allows for single inputs after the comma, eg: 5:6, 2, 3, 9
        val2 = int(ctuple[-1])
        if val1 > content_list_len and val2 > content_list_len:
            continue
        # check with content_list_len to ease the computation for the range function
        val1 = val1 if val1 <= content_list_len else content_list_len
        val2 = val2 if val2 <= content_list_len else content_list_len
        # check for reversed sequences
        if val1 > val2:
            rev = -1
        else:
            rev = 1
        # e.g. from val1 = 7 and val2 = 4 produce: 7, 6, 5, 4
        range_val = [x for x in range(val1, val2 + rev, rev)]
        full_range.extend(range_val)

    return full_range


def use_bulk_values(bulk_value, content_list_len):
    if ':' not in str(bulk_value):
        # bulk_value is an int
        return single_choice, bulk_value, bulk_value
    # bulk_value is a str
    full_range = get_full_range(bulk_value, content_list_len)
    choice = full_range[0] if full_range else 0
    return multi_choice, full_range, choice


@hide_phrase_in
def input_func(prompt_msg, add_element, bulk, content_list, hide=None, connector='<br>'):
    global skip

    params = (content_list, connector)
    bulk_value = config[bulk]

    if not config[add_element]:
        # range_choice = choice when range is not given
        func, range_choice, choice = use_bulk_values(bulk_value, len(content_list))
        return func(range_choice, *params), choice, hide

    choice = input(f'{input_c.color}{prompt_msg} [{bulk_value}]:{inputtext_c.color} ')

    if not choice.strip():
        func, range_choice, choice = use_bulk_values(bulk_value, len(content_list))
        chosen_cont = func(range_choice, *params)
    elif choice.isnumeric():
        chosen_cont = single_choice(int(choice), *params)
    elif choice.startswith('/'):
        chosen_cont = choice.replace('/', '', 1)
    elif choice.lower() == '-s':
        chosen_cont = ''
    elif choice.lower() in ('-1', 'all'):
        chosen_cont = single_choice(-1, *params)
    # choice with colons may include commas
    elif ':' in choice:
        full_range = get_full_range(choice, len(content_list))
        chosen_cont = multi_choice(full_range, content_list, connector)
        choice = full_range[0] if full_range else 0
    elif ',' in choice:
        mchoice = [int(x) for x in choice.split(',') if x.strip().isnumeric()]
        chosen_cont = multi_choice(mchoice, content_list, connector)
        choice = mchoice[0] if mchoice else 0
    else:
        skip = 1
        print(f'{GEX.color}Pominięto dodawanie karty')
        return '', 0, None

    return chosen_cont, choice, hide


def multi_choice(*args):
    choice = args[0]
    content_list = args[1]
    connector = args[2]

    content = []
    choice_no = []
    for ch in choice:
        if ch > len(content_list) or ch == 0:
            continue
        elem = content_list[ch - 1]
        if elem:
            content.append(elem)
            choice_no.append(str(ch))

    print(f'{YEX.color}Dodane elementy: {", ".join(choice_no)}')
    return connector.join(content)


def single_choice(choice, content_list, connector):
    if len(content_list) >= choice > 0:
        return content_list[choice - 1]
    elif choice > len(content_list) or choice == -1:
        no_blanks = [x for x in content_list if x != '']
        return connector.join(no_blanks)
    else:  # 0
        return ''


def wordnet_request(url):
    try:
        # WordNet doesn't load faster when using requests.Session(),
        # probably my implementation is wrong
        # though it might be headers like keep-alive or cookies, I don't know
        reqs_syn = requests.get(url, headers=USER_AGENT, timeout=10)
        syn_soup = BeautifulSoup(reqs_syn.content, 'lxml', from_encoding='iso-8859-1')
        header = syn_soup.find('h3').text

        if header.startswith('Your') or header.startswith('Sorry'):
            print(f'{err_c.color}Nie znaleziono {phrase_c.color}{phrase}{err_c.color} na {R}WordNecie')
            return None

        return syn_soup
    except ConnectionError:
        print(f'{err_c.color}Nie udało się połączyć z WordNetem, sprawdź swoje połączenie i spróbuj ponownie')
    except Timeout:
        print(f'{err_c.color}WordNet nie odpowiada, spróbuj nawiązać połączenie później')
    except requestsConnectError:
        print(f'{err_c.color}WordNet zerwał połączenie\n'
              f'zmień słownik lub zrestartuj program i spróbuj ponownie')
    except Exception:
        print(f'{err_c.color}Wystąpił nieoczekiwany błąd podczas wyświetlania WordNeta\n')
        raise


def wordnet(query):
    global skip_wordnet

    if not config['add_disambiguation']:
        # without skipping
        return [], []

    full_url = 'http://wordnetweb.princeton.edu/perl/webwn?s=' + query
    syn_soup = wordnet_request(full_url)
    if syn_soup is None:
        skip_wordnet = 1
        return [], []

    gsyn = []
    gpsyn = []

    if config['showdisamb']:
        print(f'{delimit_c.color}{get_conf_of("delimsize") * "-"}')
        print(f'{BOLD}{"WordNet".center(get_conf_of("center"))}{END}')
        if not config['compact']:
            print()

    syn_elems = syn_soup.find_all('li')
    for index, ele in enumerate(syn_elems, start=1):
        pos = '(' + ele.text.split(') ', 1)[0].split('(')[-1] + ')'
        syn = (ele.text.split(') ', 1)[-1].split(' (')[0]).strip()
        gloss = '(' + ((ele.text.rsplit(') ', 1)[0] + ')').strip('S: (').split(' (', 1)[-1])
        # Anki treats double quotes as escape characters when importing
        psyn = ele.text.rsplit(') ')[-1].replace('"', "'")
        if config['psyn_filter']:
            # phrase[:-1] is the most accurate filter as it caters to almost
            # all exceptions while having rather low false-positive ratio
            psyn = '; '.join([x for x in psyn.split('; ') if phrase[:-1].lower() in x.lower()])

        gpsyn.append(psyn)
        gsyn.append(syn)

        if config['showdisamb']:
            syn_tp = wrap_lines(syn, get_conf_of('textwidth'), len(str(index)),
                                indent=3, gap=4 + len(str(pos)))
            gloss_tp = wrap_lines(gloss, get_conf_of('textwidth'), len(str(index)),
                                  indent=3, gap=3)
            print(f'{index_c.color}{index} : {synpos_c.color}{pos} {syn_c.color}{syn_tp}')
            print(f'{(len(str(index))+3) * " "}{syngloss_c.color}{gloss_tp}')
            if psyn:
                for ps in psyn.split('; '):
                    psyn_tp = wrap_lines(ps, get_conf_of('textwidth'), len(str(index)),
                                         indent=4, gap=3)
                    print(f'{(len(str(index))+3) * " "}{psyn_c.color}{psyn_tp}')
            if not config['compact']:
                print()

    return gsyn, gpsyn


def farlex_idioms_request(url):
    try:
        reqs_idioms = requests.get(url, headers=USER_AGENT, timeout=10)
        soup = BeautifulSoup(reqs_idioms.content, 'lxml', from_encoding='utf-8')
        relevant_content = soup.find('section', {'data-src': 'FarlexIdi'})

        if relevant_content is None:
            print(f'{err_c.color}Nie znaleziono podanego hasła w Farlex Idioms')
            return None

        return relevant_content
    except ConnectionError:
        print(f'{err_c.color}Nie udało się połączyć ze słownikiem idiomów\n'
              f'sprawdź swoje połączenie i spróbuj ponownie')
    except Timeout:
        print(f'{err_c.color}Słownik idiomów nie odpowiada\n'
              f'spróbuj nawiązać połączenie później')
    except requestsConnectError:
        print(f'{err_c.color}Farlex zerwał połączenie\n'
              f'zmień słownik lub zrestartuj program i spróbuj ponownie')
    except Exception:
        print(f'{err_c.color}Wystąpił nieoczekiwany błąd podczas wyświetlania słownika idiomów\n')
        raise


def farlex_idioms(query):
    global phrase
    global skip

    full_url = 'https://idioms.thefreedictionary.com/' + query
    relevant_content = farlex_idioms_request(full_url)
    if relevant_content is None:
        skip = 1
        return [], [], []

    defs = []
    illusts = []
    phrase_list = []
    term_width = terminal_width()
    manage_display_parameters(term_width)

    illust_index = 0
    last_phrase = ''
    definition_divs = relevant_content.find_all('div', class_=('ds-single', 'ds-list'))
    # I have no idea how to extract immediate text from a div.
    # find_all(... text=True, recursive=False) doesn't work.
    for inx, definition in enumerate(definition_divs, start=1):
        idiom = definition.find_previous_sibling('h2')
        idiom = idiom.text.strip()
        phrase_list.append(idiom)

        if last_phrase == idiom:
            if not config['compact']:
                print()
        else:
            last_phrase = idiom
            print(f'{delimit_c.color}{get_conf_of("delimsize") * "-"}')
            if inx == 1:
                frl = 'Farlex Idioms'
                print(f'{BOLD}{frl.center(get_conf_of("center"))}{END}')
            print(f'  {phrase_c.color}{idiom}')

        idiom_def = definition.find(text=True, recursive=False)\
            .strip('1234567890. ').replace('"', "'")
        # if there is an <i> tag in between definition's index and definition
        # e.g. '2. <i>verb</i> ...'
        if len(str(idiom_def)) < 5:
            idiom_def = str(definition).split('">', 1)[1].rsplit('<span')[0]
            idiom_def = idiom_def.lstrip('1234567890. ').rstrip()
            idiom_def = idiom_def.replace('i>', '').replace('</', '>')

        idiom_def_tp = wrap_lines(idiom_def, term_width, len(str(inx)), indent=config['indent']+1, gap=3)
        print(f'{index_c.color}{inx} : {def1_c.color}{idiom_def_tp}')
        defs.append(idiom_def)

        illustrations = definition.find_all('span', class_='illustration')
        for illust in illustrations:
            illust_index += 1
            illust = "'" + illust.text.strip() + "'"
            illust_tp = wrap_lines(illust, term_width, len(str(inx)),
                                   indent=len(str(illust_index))+5, gap=len(str(illust_index))+4)
            print(f'{len(str(inx)) * " "}   {index_c.color}{illust_index} {pidiom_c.color}{illust_tp}')
            illusts.append(illust)
    print()
    return defs, illusts, phrase_list


def display_card(field_values):
    # field coloring
    color_of = {'definicja': def1_c.color, 'synonimy': syn_c.color, 'przyklady': psyn_c.color, 'phrase': phrase_c.color,
                'zdanie': '', 'czesci_mowy': pos_c.color, 'etymologia': etym_c.color, 'audio': '', 'sentence_audio': ''}
    delimit = get_conf_of('delimsize')
    centr = get_conf_of('center')
    options = (get_conf_of('textwidth'), 0, 0, 0)
    conf_fo = config['fieldorder'].items()

    try:
        print(f'\n{delimit_c.color}{delimit * "-"}')

        for field_number, field_name in conf_fo:
            for fi in wrap_lines(field_values[field_name], *options).split('\n'):
                print(f'{color_of[field_name]}{fi.center(centr)}')
            # d = delimitation
            if field_number == config['fieldorder_d']:
                print(f'{delimit_c.color}{delimit * "-"}')

        print(f'{delimit_c.color}{delimit * "-"}')
    except (NameError, KeyError):
        print(f'{err_c.color}\nDodawanie karty do pliku nie powiodło się\n'
              f'Spróbuj przywrócić domyślne ustawienia pól wpisując {R}-fo default\n')
        return 1  # skip


def save_card_to_file(field_vals):
    # replace sensitive characters with hard coded html escapes
    field_values = {key: val.replace("'", "&#39;").replace('"', '&quot;')
                    for key, val in field_vals.items()}

    try:
        with open('karty.txt', 'a', encoding='utf-8') as twor:
            twor.write(f'{field_values[config["fieldorder"]["1"]]}\t'
                       f'{field_values[config["fieldorder"]["2"]]}\t'
                       f'{field_values[config["fieldorder"]["3"]]}\t'
                       f'{field_values[config["fieldorder"]["4"]]}\t'
                       f'{field_values[config["fieldorder"]["5"]]}\t'
                       f'{field_values[config["fieldorder"]["6"]]}\t'
                       f'{field_values[config["fieldorder"]["7"]]}\t'
                       f'{field_values[config["fieldorder"]["8"]]}\t'
                       f'{field_values[config["fieldorder"]["9"]]}\n')
            print(f'{GEX.color}Karta pomyślnie zapisana do pliku\n')
    except (NameError, KeyError):
        print(f'{err_c.color}Dodawanie karty do pliku nie powiodło się\n'
              f'Spróbuj przywrócić domyślne ustawienia pól wpisując {R}-fo default\n')


def manage_dictionaries(_phrase, flags):
    global skip

    poses = []
    etyms = []
    illusts = []
    if 'i' in flags or '-idiom' in flags:
        defs, illusts, phrase_list = farlex_idioms(_phrase)
        _dict = 'farlex'
    else:
        defs, poses, etyms, phrase_list = ah_dictionary(_phrase)
        if not skip:
            _dict = 'ahd'
        else:
            skip = 0
            defs, illusts, phrase_list = farlex_idioms(_phrase)
            _dict = 'farlex'

    return _dict, defs, poses, etyms, phrase_list, illusts


def main():
    global phrase
    global skip
    global skip_wordnet

    if not os.path.exists('Karty_audio') and config['audio_path'] == 'Karty_audio':
        os.mkdir('Karty_audio')

    __version__ = 'v0.8.0-2'
    print(f'{BOLD}- Dodawacz kart do Anki {__version__} -{END}\n'
          f'Wpisz "--help", aby wyświetlić pomoc\n\n')

    while True:
        skip = 0
        skip_wordnet = 0
        phrase = ''

        link_word = search_interface()
        phrase = link_word[0]
        flags = link_word[1:]

        if phrase in ('-rec', '--record'):
            ffmpeg.capture_audio()
            continue

        if 'rec' in flags or '-record' in flags:
            sentence_audio = ffmpeg.capture_audio(phrase)
        else:
            sentence_audio = ''

        dictionary, definitions, parts_of_speech, etymologies, phrase_list, illustrations = \
            manage_dictionaries(phrase, flags)
        if skip:
            continue

        if not config['create_card']:
            wordnet(phrase)
            continue

        # input loop
        zdanie, _ = sentence_input('hide_sentence_word')
        if skip:
            continue

        # temporarily set phrase to the first element from the phrase_list
        # to always hide the correct query before input, e.g. preferred -> prefer
        phrase = phrase_list[0]
        definitions, choice = input_func(
            'Wybierz definicje', 'add_definitions', 'def_bulk', definitions, 'hide_definition_word')
        if skip:
            continue

        phrase = pick_phrase(choice, phrase_list)
        if dictionary == 'ahd':
            parts_of_speech, _ = input_func(
                'Wybierz części mowy', 'add_parts_of_speech', 'pos_bulk', parts_of_speech, connector=' | ')
            if skip:
                continue

            etymologies, _ = input_func(
                'Wybierz etymologie', 'add_etymologies', 'etym_bulk', etymologies)
            if skip:
                continue

            audio = search_for_audio(config['server'], phrase, flags)

            synonyms_list, examples_list = wordnet(phrase)
            if skip_wordnet:
                synonyms = ''
                examples = ''
            else:
                synonyms, _ = input_func(
                    'Wybierz synonimy', 'add_synonyms', 'syn_bulk', synonyms_list, 'hide_disamb_word', connector=' | ')
                if skip:
                    continue

                examples, _ = input_func(
                    'Wybierz przykłady', 'add_synonym_examples', 'psyn_bulk', examples_list, 'hide_disamb_word')
                if skip:
                    continue

                if config['merge_disambiguation']:
                    if not synonyms or not examples:
                        brk = ''
                    else:
                        brk = '<br>'
                    synonyms = synonyms + brk + examples
                    examples = ''
        else:
            parts_of_speech = ''
            etymologies = ''
            synonyms = ''
            examples, _ = input_func(
                'Wybierz przykłady', 'add_idiom_examples', 'pidiom_bulk', illustrations, 'hide_idiom_word')
            if skip:
                continue

            audio = search_for_audio('diki', phrase, flags)
            if config['merge_idioms']:
                if not definitions or not examples:
                    brk = ''
                else:
                    brk = '<br><br>'
                definitions = definitions + brk + examples
                examples = ''

        field_values = {
            'definicja': definitions, 'synonimy': synonyms, 'przyklady': examples, 'phrase': phrase,
            'zdanie': zdanie, 'czesci_mowy': parts_of_speech, 'etymologia': etymologies, 'audio': audio,
            'sentence_audio': sentence_audio}

        if config['showcard']:
            skip = display_card(field_values)
            if skip:
                continue
        print()

        if config['ankiconnect']:
            anki.create_card(field_values)
        if config['save_card']:
            save_card_to_file(field_values)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        # R so that the color from "inputtext" isn't displayed
        print(f'{R}\nUnicestwiony')
