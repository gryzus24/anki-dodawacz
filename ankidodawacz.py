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
from requests.exceptions import ConnectionError as RqConnectionError
from requests.exceptions import Timeout

import src.anki_interface as anki
import src.commands as c
import src.data as data
import src.ffmpeg_interface as ffmpeg
import src.help as h
from src.colors import \
    R, BOLD, END, YEX, GEX, \
    def1_c, def2_c, defsign_c, pos_c, etym_c, syn_c, psyn_c, \
    pidiom_c, syngloss_c, synpos_c, index_c, phrase_c, \
    phon_c, poslabel_c, inflection_c, err_c, delimit_c, input_c, inputtext_c
from src.data import config, input_configuration

if sys.platform.startswith('linux'):
    # For saving command history, this module doesn't work on windows
    import readline
    readline.read_init_file()

USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'
}

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
    '-hideas': c.set_free_value_commands,
    '--audio-path': c.set_audio_path, '-ap': c.set_audio_path,
    '-dupescope': c.set_text_value_commands,
    '-server': c.set_text_value_commands,
    '-quality': c.set_text_value_commands,
    '--add-note': anki.add_notes,
    '--field-order': c.change_field_order, '-fo': c.change_field_order,
    '-colors': c.set_colors, '-color': c.set_colors, '-c': c.set_colors,
    '--config-bulk': c.config_bulk, '--config-defaults': c.config_bulk,
    '-cd': c.config_bulk, '-cb': c.config_bulk,
    '--audio-device': ffmpeg.set_audio_device, '-device': ffmpeg.set_audio_device,
    # commands that take no arguments
    '-refresh': anki.refresh_notes,
    '--help': h.quick_help, '-help': h.quick_help, '-h': h.quick_help,
    '--help-bulk': h.bulk_help, '--help-defaults': h.bulk_help,
    '--help-commands': h.commands_help, '--help-command': h.commands_help,
    '--help-recording': h.recording_help,
    '-config': c.print_config_representation, '-conf': c.print_config_representation
}


def search_interface() -> str:
    while True:
        word = input(f'{input_c.color}Szukaj ${inputtext_c.color} ').strip()
        if not word:
            continue
        args = word.split()
        cmd = args[0]
        try:
            # don't forget to change the splice when adding/removing commands!
            if cmd in tuple(data.command_data)[:31]:
                # to avoid writing all of them in the commands dict above
                c.boolean_commands(*args)
            elif cmd in tuple(commands)[:27]:
                commands[cmd](*args)
            else:
                commands[cmd]()
        except KeyError:  # command not found
            return word


def handle_connection_exceptions(func):
    def wrapper(*args, **kwargs):
        dictionary_name = func.__name__.rsplit('_', 1)[0]
        try:
            result = func(*args, **kwargs)
        except Timeout:
            print(f'{err_c.color}{dictionary_name} nie odpowiada.')
        except RqConnectionError:
            print(f'{err_c.color}Połączenie z {dictionary_name} zostało zerwane.')
        except ConnectionError:
            print(f'{err_c.color}Nie udało się połączyć z {dictionary_name},\n'
                  f'sprawdź swoje połączenie i spróbuj ponownie.')
        except Exception:
            print(f'{err_c.color}Wystąpił nieoczekiwany błąd podczas łączenia się z {dictionary_name}.')
            raise
        else:
            return result

    return wrapper


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


@handle_connection_exceptions
def diki_request(full_url):
    reqs = requests.get(full_url, headers=USER_AGENT, timeout=10)
    soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    return soup.find_all('span', class_='audioIcon icon-sound dontprint soundOnClick')


def get_audio_from_diki(raw_phrase, flag, url='https://www.diki.pl/slownik-angielskiego?q='):
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


def ahdictionary_audio(query):
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
                try:  # temporary fix, this whole thing needs to be rewritten
                    lx_audio = pronunciations[audio_numb]
                except IndexError:
                    lx_audio = pronunciations
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
    available_flags = (
        'n', 'v', 'adj', 'noun', 'verb', 'adjective',
        'adv', 'abbr', 'adverb', 'abbreviation'
    )
    if server == 'diki':
        available_flags = available_flags[:6]

    try:
        flag = [x for x in flags if x in available_flags][0]
    except IndexError:
        return ''
    else:
        return flag


def search_for_audio(server, phrase_, flags):
    if not config['add_audio']:
        return ''

    if server == 'ahd':
        audio_link, audiofile_name = ahdictionary_audio(phrase_)
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

    def trivial_wrap():
        wrapped_text = ''
        current_llen = 0
        for word in string_divided:
            # >= guarantees one character right-side padding
            if current_llen + len(word) >= real_width:
                wrapped_text = wrapped_text.rstrip()
                wrapped_text += '\n' + indent_ * ' '
                current_llen = indent - gap

            wrapped_text += word + ' '
            current_llen += len(word) + 1

        return wrapped_text.rstrip()

    def justification_wrap():
        wrapped_text = ''
        line = ''

        # -1 because last space before wrapping is ignored in justification
        spaces_between_words = -1
        current_llen = 0
        for word in string_divided:
            if current_llen + len(word) >= real_width:
                line = line.rstrip()
                filling = real_width - current_llen
                if spaces_between_words > 0:
                    set_spaces = ' '
                    while filling > 0:
                        if filling <= spaces_between_words:
                            line = line.replace(set_spaces, set_spaces + ' ', filling)
                            break

                        line = line.replace(set_spaces, set_spaces + ' ', spaces_between_words)
                        filling -= spaces_between_words
                        set_spaces += ' '

                wrapped_text += line + '\n' + indent_ * ' '
                line = ''
                spaces_between_words = -1
                current_llen = indent - gap

            spaces_between_words += 1
            line += word + ' '
            current_llen += len(word) + 1

        return wrapped_text + line.rstrip()

    # Gap is the gap between indexes and strings
    real_width = int(term_width) - index_width - gap
    if len(string) <= real_width:
        return string

    if term_width < 67:
        # mitigate the one character right-side padding
        real_width += 1

    string_divided = string.split()
    indent_ = indent + index_width
    if config['text_justification']:
        return justification_wrap()
    else:
        return trivial_wrap()


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


def definition_cleanup(definition):
    rex = definition.lstrip('1234567890.')
    rex = rex.split(' See Usage Note at')[0]
    rex = rex.split(' See Synonyms at')[0]
    for letter in 'abcdefghijklmn':
        rex = rex.replace(f":{letter}. ", ": *")
        rex = rex.replace(f".{letter}. ", ". *")
        rex = rex.replace(f" {letter}. ", " ")
        # when definition has an example with a '?' there's no space in between
        rex = rex.replace(f"?{letter}. ", "? *")
    # private unicode characters cleanup, example words containing them:
    # long, all right
    rex = rex.strip().replace('', 'ˌ').replace('', 'ōō')
    return rex.replace('  ', ' # ')


def manage_display_parameters(term_width):
    if config['indent'] > term_width // 2:
        c.save_commands(entry='indent', value=term_width // 2)
    if '* auto' in str(config['delimsize']):
        c.save_commands(entry='delimsize', value=f'{term_width}* auto')
    if '* auto' in str(config['center']):
        c.save_commands(entry='center', value=f'{term_width}* auto')


def get_phrase_and_phonetic_spelling(headword_elements: list) -> tuple:
    phrase_elements = []
    phonetics = []
    for elem in headword_elements:
        if elem.isnumeric():
            continue
        elif elem.istitle():
            phrase_elements.append(elem)
            continue

        for char in '(,)':
            if char in elem:
                phonetics.append(elem)
                break
        else:
            phrase_elements.append(elem)

    return phrase_elements, phonetics


def expand_labels(label_set: set) -> set:
    # Expanding these sets offers more leeway when specifying flags
    for item in label_set.copy():
        try:
            label_set.update(data.labels[item])
        except KeyError:
            pass
    return label_set


def eval_label_skip(labels: set, flags: set, *, exclude_immediately: bool) -> bool:
    # when config['nolabel_filter'] is True
    if not flags:
        return False

    labels = {x.replace(' ', '').replace('.', '').lower() for x in labels}
    if not labels:
        labels.add('nolabel')

    expanded_labels = expand_labels(labels)

    for flag in flags:
        # "else" doesn't execute if break occurs
        if flag.startswith('!'):
            break
    else:
        for flag in flags:
            # check inclusive flags
            if flag in expanded_labels:
                return False
        return True

    # check exclusive flags
    if exclude_immediately:
        for flag in flags:
            if flag.replace('!', '', 1) in expanded_labels:
                return True
        return False
    else:
        _flags = {x.strip('!') for x in flags}
        if 'v' in _flags:
            _flags.update(('intransitive', 'transitive', 'intr', 'tr',
                           'intrv', 'trv', 'vintr', 'vtr', 'v', 'verb'))
        expanded_flags = expand_labels(_flags)
        if expanded_labels.intersection(expanded_flags) == expanded_labels:
            return True
        return False


def phrase_tenses_to_print(phrase_tenses: list) -> str:
    skip_next = False
    pht = []
    for i, elem in enumerate(phrase_tenses):
        if elem == 'or':
            pht.pop()
            ored = ' '.join((phrase_tenses[i - 1], phrase_tenses[i], phrase_tenses[i + 1]))
            pht.append(ored)
            skip_next = True
        elif elem == 'also':
            alsoed = ' '.join((phrase_tenses[i], phrase_tenses[i + 1]))
            pht.append(alsoed)
            skip_next = True
        else:
            if skip_next:
                skip_next = False
                continue
            pht.append(elem)

    return ' * '.join(pht)


def get_phrase_tenses(contents) -> list:
    return [
        x.string.strip(', ') for x in contents
        if x.string is not None and x.string.strip(', ') and
        ('<b>' in str(x) or x.string.strip(', ') in ('or', 'also'))
    ]


def ahd_to_ipa_translation(ahd_phonetics: str, th: str) -> str:
    # AHD has its own phonetic alphabet that can be translated into IPA.
    # diphthongs
    ahd_phonetics = ahd_phonetics.replace('ch', 't∫')\
        .replace('sh', 'ʃ').replace('îr', 'ɪəɹ')\
        .replace('ng', 'ŋ').replace('ou', 'aʊ')\
        .replace('oi', 'ɔɪ').replace('ər', 'ɚ')\
        .replace('ûr', 'ɝ').replace('th', th)\
        .replace('âr', 'ɛəɹ').replace('zh', 'ʒ')\
        .replace('l', 'ɫ').replace('n', 'ən')\
        .replace('r', 'ʊəɹ').replace('ôr', 'ɔəɹ')
    # consonants and vowels
    ahd_phonetics = ahd_phonetics.translate(data.AHD_IPA_translation)
    # accentuation and hyphenation
    ahd_phonetics = ahd_phonetics.replace('-', 'ˈ').replace('′', '-').replace('', 'ˌ')
    # AHD uses 'ē' to represent both 'i' and "i:",
    # IPA uses 'i' at the end of the word most of the time
    ahd_phonetics = ahd_phonetics.replace('i:/', 'i/')
    return ahd_phonetics


@handle_connection_exceptions
def ahdictionary_request(url):
    reqs = requests_session_ah.get(url, timeout=10)
    soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    word_check = soup.find('div', {'id': 'results'})

    if word_check.text == 'No word definition found':
        return None
    return soup


def ahdictionary(query, *flags):
    def skip_this_td():
        _td_pos_labels = set()
        for lblock in labeled_blocks:
            lbls = lblock.find_all('i', recursive=False)
            lbls = {x.text.strip() for x in lbls}
            _td_pos_labels.update(lbls)

        # th is an artifact of <i>th</i> quirk in AHD pronunciation variant
        _td_pos_labels.discard('th')
        if not _td_pos_labels:
            if config['nolabel_filter']:
                return True

        exclude_condition = True if len(labeled_blocks) == 1 else False
        skip_current_td = eval_label_skip(_td_pos_labels, flags, exclude_immediately=exclude_condition)
        if skip_current_td:
            return True
        return False

    global skip

    full_url = 'https://www.ahdictionary.com/word/search.html?q=' + query
    soup = ahdictionary_request(full_url)
    if soup is None:
        print(f'{err_c.color}Nie znaleziono {R}"{query}"{err_c.color} w AH Dictionary')
        skip = 1
        return None, None, None, None

    defs = []
    poses = []
    etyms = []
    phrase_list = []

    term_width = terminal_width()
    manage_display_parameters(term_width)

    if config['ahd_filter']:
        filter_subdefs = True
    else:
        if 'f' in flags or 'fahd' in flags:
            filter_subdefs = True
        else:
            filter_subdefs = False

    subindex = 0
    # whether 'results for (phrase)' was printed
    results_for_printed = False

    tds = soup.find_all('td')
    if flags or config['nolabel_filter']:
        flags = {
            x.replace(' ', '').replace('.', '').lower()
            for x in flags
            if x.replace('!', '').replace(' ', '').replace('.', '').lower() not in
            ('f', 'fahd', 'ahd', 'rec', 'record')}  # 'i' and "idiom" flags cannot end up here

        for td in tds:
            labeled_blocks = td.find_all('div', class_='pseg', recursive=False)
            if not skip_this_td():
                break
        else:
            flags = ()  # display all definitions

    for td in tds:
        # also used when printing definitions
        labeled_blocks = td.find_all('div', class_='pseg', recursive=False)

        if flags or config['nolabel_filter']:
            if skip_this_td():
                continue

        print(f'{delimit_c.color}{get_conf_of("delimsize") * "-"}')
        # example header: bat·ter 1  (băt′ər)
        # example person header: Monk  (mŭngk), (James) Arthur  Known as  "Art."  Born 1957.
        header = td.find('div', class_='rtseg', recursive=False)
        # AHD uses italicized "th" to represent 'ð' and normal "th" to represent 'θ'
        th = 'ð' if header.find('i') else 'θ'
        header = (header.text.split('\n', 1)[0]).split()
        _phrase, phon_spell = get_phrase_and_phonetic_spelling(header)

        _phrase = ' '.join(_phrase)
        no_accents_phrase = _phrase.replace('·', '')

        phon_spell = ' '.join(phon_spell)
        phon_spell = phon_spell.rstrip(',')
        if config['convert_to_ipa']:
            phon_spell = ahd_to_ipa_translation(phon_spell, th)
        else:
            phon_spell = phon_spell.replace('-', 'ˈ')\
                .replace('′', '-').replace('', 'ˌ')\
                .replace('', 'ōō').replace('', 'ōō')

        if not results_for_printed:
            ahd = 'AH Dictionary (filtered)' if filter_subdefs else 'AH Dictionary'

            print(f'{BOLD}{ahd.center(get_conf_of("center"))}{END}')
            if no_accents_phrase.lower() != query.lower():
                print(f' {BOLD}Wyniki dla {phrase_c.color}{no_accents_phrase}{END}')
            results_for_printed = True

        if len(_phrase) + len(phon_spell) + 3 > term_width:
            print(f' {phrase_c.color}{_phrase}\n{phon_c.color}{phon_spell}')
        else:
            print(f' {phrase_c.color}{_phrase}  {phon_c.color}{phon_spell}')

        for block in labeled_blocks:
            # Gather part of speech labels
            pos_labels = block.find_all('i', recursive=False)
            pos_labels = {x.text.strip() for x in pos_labels if x.text.strip()}
            pos_labels.discard('th')

            if config['nolabel_filter'] and not pos_labels:
                continue

            # part of speech labels from a single block
            skip_current_block = eval_label_skip(pos_labels, flags, exclude_immediately=True)
            if skip_current_block:
                continue

            # Gather phrase tenses
            phrase_tenses = get_phrase_tenses(block.contents[1:])
            phrase_tenses_tp = phrase_tenses_to_print(phrase_tenses)

            if pos_labels:
                print()
            pos_label = ' '.join(pos_labels)
            print(f' {poslabel_c.color}{pos_label}', end='')

            if len(pos_label) + len(phrase_tenses_tp) + 3 > term_width:
                print(f'\n {inflection_c.color}{phrase_tenses_tp}')
            else:
                print(f'  {inflection_c.color}{phrase_tenses_tp}')

            # Add definitions and corresponding phrases
            definitions = block.find_all('div', class_=('ds-list', 'ds-single'), recursive=False)
            for root_definition in definitions:
                root_definition = definition_cleanup(root_definition.text)

                subdefinitions = root_definition.split('*')
                for i, subdefinition in enumerate(subdefinitions):
                    subindex += 1
                    # strip an occasional leftover octothorpe
                    subdefinition = subdefinition.strip('# ')
                    subdef_to_print = wrap_lines(subdefinition, term_width, len(str(subindex)),
                                                 indent=config['indent'], gap=2)
                    if i == 0:
                        sign = '>'
                    else:
                        sign = ' '

                    if subindex % 2 == 1:
                        print(f'{defsign_c.color}{sign}{index_c.color}{subindex} {def1_c.color}{subdef_to_print}')
                    else:
                        print(f'{defsign_c.color}{sign}{index_c.color}{subindex} {def2_c.color}{subdef_to_print}')

                    defs.append(subdefinition)
                    phrase_list.append(no_accents_phrase)
                    if filter_subdefs:
                        break

        # Add parts of speech
        parts_of_speech = td.find_all('div', class_='runseg', recursive=False)
        if parts_of_speech:
            print()
            td_pos = ''
            for pos in parts_of_speech:
                # removing ',' makes parts of speech with multiple spelling variants get
                # their phonetic spelling correctly detected
                postring = pos.text.replace(',', '').split()
                postring, phon_spell = get_phrase_and_phonetic_spelling(postring)

                # accentuation and hyphenation
                postring = ', '.join(postring).replace('·', 'ˈ').replace('′', '-').replace('', 'ˌ')
                phon_spell = ' '.join(phon_spell).rstrip(',')

                if config['convert_to_ipa']:
                    # this is very general, I have no idea how to differentiate these correctly
                    th = 'ð' if postring.startswith('th') else 'θ'
                    phon_spell = ahd_to_ipa_translation(phon_spell, th)
                else:
                    phon_spell = phon_spell.replace('-', 'ˈ')\
                        .replace('′', '-').replace('', 'ˌ')\
                        .replace('', 'ōō').replace('', 'ōō')

                print(f' {pos_c.color}{postring}  {phon_c.color}{phon_spell}')
                td_pos += f'{postring} | '
            poses.append(td_pos.rstrip('| '))

        # Add etymologies
        etymologies = td.find_all('div', class_='etyseg', recursive=False)
        if etymologies:
            print()
            for etym in etymologies:
                print(f' {etym_c.color}'
                      f'{wrap_lines(etym.text, term_width, 0, 1, 1)}')
                etyms.append(etym.text.strip())
    print()
    return defs, poses, etyms, phrase_list


def hide_phrase_in(func):
    def wrapper(*args, **kwargs):
        def content_replace(a: str, b: str) -> str:
            return content.replace(a, b).replace(a.capitalize(), b).replace(a.upper(), b.upper())

        content, choice, hide = func(*args, **kwargs)
        if not hide or not config[hide] or not content:
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
                if word.lower() in data.PREPOSITIONS:
                    continue

            # "Ω" is a placeholder
            content = content_replace(word, f"{config['hideas']}Ω")
            if word.endswith('e'):
                content = content_replace(word[:-1] + 'ing', f'{config["hideas"]}Ωing')
                if word.endswith('ie'):
                    content = content_replace(word[:-2] + 'ying', f'{config["hideas"]}Ωying')
            elif word.endswith('y'):
                content = content_replace(word[:-1] + 'ies', f'{config["hideas"]}Ωies')
                content = content_replace(word[:-1] + 'ied', f'{config["hideas"]}Ωied')

        if config['keep_endings']:
            content = content.replace('Ω', '')
        else:
            # e.g. from "We weren't ...Ωed for this." -> "We weren't ... for this."
            split_content = content.split('Ω')
            temp = [split_content[0].strip()]
            for elem in split_content[1:]:
                for letter in elem:
                    if letter == ' ':
                        break
                    elem = elem.replace(letter, '', 1)
                temp.append(elem.strip())
            content = ' '.join(temp)

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


def map_specifiers_to_inputs(range_tuples: tuple) -> tuple:
    # yields (input_values, specifiers)
    for tup in range_tuples:
        if len(tup) <= 3:  # if len(tuple with specifiers) <= 3
            yield tup[:-1], tup[-1]
        else:
            # e.g. from ('1', '3', '5', '234') -> ('1', '3', '234'), ('3', '5', '234')
            for i, _ in enumerate(tup[:-2]):
                yield tup[0 + i:2 + i], tup[-1]


def filter_tuples(tup: tuple) -> bool:
    # tuples for input: 2:3, 5.41., 6.2, asdf...3, 7:9.123:
    # ('2', '3', ''), ('5', '41.'), ('6', '2'), ('asdf', '..3'), ('7', '9', '123')

    if not tup[-1].isnumeric():
        if tup[-1]:
            return False
        # else: pass when specifier == ''

    for value in tup[:-1]:
        # zero is excluded in multi_choice function, otherwise tuples like:
        # ('0', '4') would be ignored, but I want them to produce: 1, 2, 3, 4
        if not value.isnumeric():
            return False
    return True


def parse_inputs(inputs: list, content_length: int) -> tuple:
    # example valid inputs: 1:4:2.1, 4:0.234, 1:6:2:8, 4, 6, 5.2
    # example invalid inputs: 1:5:2.3.1, 4:-1, 1:6:2:s, 4., 6.., 5.asd
    input_block = []
    # '' = no specifiers
    for _input in inputs:
        head, _, specifiers = _input.partition('.')
        tup = head.split(':')
        # specifiers are always referenced by [-1]
        tup.append(specifiers)
        input_block.append(tuple(tup))

    # get rid of invalid inputs
    valid_range_tuples = tuple(filter(filter_tuples, input_block))
    if not valid_range_tuples:
        return None, 1

    input_blocks = []
    for _input, specifiers in map_specifiers_to_inputs(valid_range_tuples):
        val1 = int(_input[0])
        # [-1] allows for single inputs after the comma, e.g.: 5:6, 2, 3, 9
        val2 = int(_input[-1])
        if val1 > content_length and val2 > content_length:
            continue
        # check with length to ease the computation for the range function
        val1 = val1 if val1 <= content_length else content_length
        val2 = val2 if val2 <= content_length else content_length
        # check for reversed sequences
        if val1 > val2:
            rev = -1
        else:
            rev = 1
        # e.g. from val1 = 7 and val2 = 4 produce: 7, 6, 5, 4
        input_block = [x for x in range(val1, val2 + rev, rev)]
        input_block.append(specifiers)

        input_blocks.append(input_block)

    if not input_blocks or input_blocks[0][0] == 0:
        phrase_choice = 1
    else:
        phrase_choice = input_blocks[0][0]

    return input_blocks, phrase_choice


def print_added_elements(message: str, elements='') -> None:
    if config['showadded']:
        print(f'{YEX.color}{message}: {R}{elements}')


@hide_phrase_in
def input_field(content_list, prompt, add_field, bulk_element, hide, connector, **options):
    global skip

    default_value = config[bulk_element]
    content_length = len(content_list)

    if not config[add_field]:
        input_choice = default_value
    else:
        input_choice = input(f'{input_c.color}{prompt} [{default_value}]:{inputtext_c.color} ')
        if not input_choice.strip():
            input_choice = default_value

    if input_choice.startswith('/'):
        users_element = input_choice.replace('/', '', 1)
        print_added_elements('Dodano', users_element)
        return users_element, 1, hide

    input_choice = input_choice.replace(' ', '').lower()
    if input_choice in ('0', '-s', '-0'):
        return '', 1, False
    elif input_choice.startswith('-1'):
        input_choice = input_choice.replace('-1', f'1:{content_length}')
    elif input_choice.isnumeric() and int(input_choice) > content_length != 0:
        # remove occasional blanks from WordNet
        content_list = [x for x in content_list if x]
        print_added_elements('Dodane elementy', 'wszystkie')
        return connector.join(content_list), 1, hide

    input_choice = input_choice.replace('-all', f'{content_length}:1')
    input_choice = input_choice.replace('all', f'1:{content_length}')

    input_elements = input_choice.split(',')
    input_blocks, phrase_choice = parse_inputs(input_elements, content_length)
    if input_blocks is None:
        skip = 1
        print(f'{GEX.color}Pominięto dodawanie karty')
        return '', 1, False

    chosen_content_list = add_elements(input_blocks, content_list, **options)
    return connector.join(chosen_content_list), phrase_choice, hide


def add_elements(parsed_inputs: list, content_list: list, spec_split: str) -> list:
    content = []
    valid_choices = []

    for input_block in parsed_inputs:
        choices = input_block[:-1]
        specifiers = input_block[-1].lstrip('0')

        for choice in choices:
            if choice == 0 or choice > len(content_list):
                continue

            content_element = content_list[choice - 1]
            if not content_element:
                continue

            if not specifiers:
                content.append(content_element)
                valid_choices.append(choice)
                continue

            sliced_content_element = (content_element.strip('. ')).split(spec_split)
            if len(sliced_content_element) == 1:
                content.append(content_element)
                valid_choices.append(choice)
                continue

            element = []
            for specifier in specifiers:
                if int(specifier) == 0 or int(specifier) > len(sliced_content_element):
                    continue

                slice_of_content = sliced_content_element[int(specifier) - 1].strip('. ')
                valid_choices.append(f'{choice}.{specifier}')
                element.append(slice_of_content)

            # to properly join elements specified in reversed order
            element = (spec_split + ' ').join(element)
            if element.startswith('['):  # closing bracket in etymologies
                element += ']'
            content.append(element)

    print_added_elements('Dodane elementy', ', '.join(map(str, valid_choices)))
    return content


@handle_connection_exceptions
def wordnet_request(url):
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


def wordnet(query):
    global skip_wordnet

    if not config['add_disambiguation'] or \
            (not config['add_synonyms'] and not config['add_synonym_examples']) and \
            (config['syn_bulk'] == '0' and config['psyn_bulk'] == '0') and \
            config['create_card']:
        # without skipping
        return [], []

    full_url = 'http://wordnetweb.princeton.edu/perl/webwn?s=' + query
    syn_soup = wordnet_request(full_url)
    if syn_soup is None:
        skip_wordnet = 1
        return [], []

    gsyn = []
    gpsyn = []
    textwidth = get_conf_of('textwidth')

    print(f'{delimit_c.color}{get_conf_of("delimsize") * "-"}')
    print(f'{BOLD}{"WordNet".center(get_conf_of("center"))}{END}\n')

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

        syn_tp = wrap_lines(syn, textwidth, len(str(index)),
                            indent=3, gap=4 + len(str(pos)))
        gloss_tp = wrap_lines(gloss, textwidth, len(str(index)),
                              indent=3, gap=3)
        print(f'{index_c.color}{index} : {synpos_c.color}{pos} {syn_c.color}{syn_tp}')
        print(f'{(len(str(index))+3) * " "}{syngloss_c.color}{gloss_tp}')
        if psyn:
            for ps in psyn.split('; '):
                psyn_tp = wrap_lines(ps, textwidth, len(str(index)),
                                     indent=4, gap=3)
                print(f'{(len(str(index))+3) * " "}{psyn_c.color}{psyn_tp}')
        print()

    return gsyn, gpsyn


@handle_connection_exceptions
def farlex_idioms_request(url):
    reqs_idioms = requests.get(url, headers=USER_AGENT, timeout=10)
    soup = BeautifulSoup(reqs_idioms.content, 'lxml', from_encoding='utf-8')
    relevant_content = soup.find('section', {'data-src': 'FarlexIdi'})

    if relevant_content is None:
        return None
    return relevant_content


def farlex_idioms(query):
    global skip

    full_url = 'https://idioms.thefreedictionary.com/' + query
    relevant_content = farlex_idioms_request(full_url)
    if relevant_content is None:
        print(f'{err_c.color}Nie znaleziono {R}"{query}"{err_c.color} w Farlex Idioms')
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
            print()
        else:
            last_phrase = idiom
            print(f'{delimit_c.color}{get_conf_of("delimsize") * "-"}')
            if inx == 1:
                frl = 'Farlex Idioms'
                print(f'{BOLD}{frl.center(get_conf_of("center"))}{END}')
            print(f'  {phrase_c.color}{idiom}')

        idiom_def = definition.find(text=True, recursive=False)\
            .lstrip('1234567890. ').replace('"', "'")
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

    try:
        print(f'\n{delimit_c.color}{delimit * "-"}')

        for field_number, field_name in config['fieldorder'].items():
            formatted_lines = field_values[field_name].replace('<br>', '\n').split('\n')
            for line in formatted_lines:
                sublines = wrap_lines(line, *options).split('\n')
                for subline in sublines:
                    print(f'{color_of[field_name]}{subline.center(centr)}')

            if field_number == config['fieldorder_d']:  # d = delimitation
                print(f'{delimit_c.color}{delimit * "-"}')

        print(f'{delimit_c.color}{delimit * "-"}')
    except (NameError, KeyError):
        print(f'{err_c.color}\nDodawanie karty do pliku nie powiodło się\n'
              f'Spróbuj przywrócić domyślne ustawienia pól wpisując {R}-fo default\n')
        return 1  # skip


def merge_fields(field_to_merge_into: str, mergee: str, connector: str) -> tuple:
    if not field_to_merge_into or not mergee:
        connector = ''

    merged_field = field_to_merge_into + connector + mergee
    return merged_field, ''


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
    if 'i' in flags or 'idiom' in flags:
        defs, illusts, phrase_list = farlex_idioms(_phrase)
        _dict = 'farlex'
    elif 'ahd' in flags:
        defs, poses, etyms, phrase_list = ahdictionary(_phrase, *flags)
        _dict = 'ahd'
    else:
        defs, poses, etyms, phrase_list = ahdictionary(_phrase, *flags)
        if not skip:
            _dict = 'ahd'
        else:
            print(f'{YEX.color}Szukam w Farlex Idioms...')
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

    __version__ = 'v0.9.2-1'
    print(f'{BOLD}- Dodawacz kart do Anki {__version__} -{END}\n'
          'Wpisz "--help", aby wyświetlić pomoc\n\n')

    while True:
        skip = 0
        skip_wordnet = 0
        phrase = ''

        link_word = search_interface()
        phrase, *flags = link_word.split(' -')
        flags = [x.strip('-') for x in flags]

        if phrase in ('-rec', '--record'):
            ffmpeg.capture_audio()
            continue

        if 'rec' in flags or 'record' in flags:
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

        # input fields loop
        zdanie, _ = sentence_input('hide_sentence_word')
        if skip:
            continue
        # temporarily set phrase to the first element from the phrase_list
        # to always hide the correct query before input, e.g. preferred -> prefer
        phrase = phrase_list[0]

        if dictionary == 'ahd':
            definitions, choice = input_field(definitions, **input_configuration['ahd_definitions'])
            if skip:
                continue

            phrase = phrase_list[choice - 1]

            parts_of_speech, _ = input_field(parts_of_speech, **input_configuration['parts_of_speech'])
            if skip:
                continue

            etymologies, _ = input_field(etymologies, **input_configuration['etymologies'])
            if skip:
                continue

            audio = search_for_audio(config['server'], phrase, flags)

            synonyms_list, examples_list = wordnet(phrase)
            if skip_wordnet:
                synonyms = ''
                examples = ''
            else:
                synonyms, _ = input_field(synonyms_list, **input_configuration['wordnet_synonyms'])
                if skip:
                    continue

                examples, _ = input_field(examples_list, **input_configuration['wordnet_synonym_examples'])
                if skip:
                    continue

                if config['merge_disambiguation']:
                    synonyms, examples = merge_fields(synonyms, examples, '<br>')
        else:
            definitions, choice = input_field(definitions, **input_configuration['farlex_idioms'])
            if skip:
                continue

            phrase = phrase_list[choice - 1]

            parts_of_speech = ''
            etymologies = ''
            synonyms = ''
            examples, _ = input_field(illustrations, **input_configuration['idiom_examples'])
            if skip:
                continue

            audio = search_for_audio('diki', phrase, flags)
            if config['merge_idioms']:
                definitions, examples = merge_fields(definitions, examples, '<br><br>')

        field_values = {
            'definicja': definitions, 'synonimy': synonyms, 'przyklady': examples, 'phrase': phrase,
            'zdanie': zdanie, 'czesci_mowy': parts_of_speech, 'etymologia': etymologies, 'audio': audio,
            'sentence_audio': sentence_audio}

        if config['displaycard']:
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
    except (KeyboardInterrupt, EOFError):
        # R so that the color from "inputtext" isn't displayed
        print(f'{R}\nUnicestwiony')
