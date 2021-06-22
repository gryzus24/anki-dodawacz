import json  # Dla ankiconnect invoke
import os
import os.path
import re
import sys
import urllib.request
from itertools import zip_longest
from urllib.error import URLError

import requests
import yaml
from bs4 import BeautifulSoup
from colorama import Fore
from requests.exceptions import Timeout

import komendy as k
import notatki
from komendy import BOLD, END

if sys.platform.startswith('linux'):
    # Zapisywanie historii komend. Ten moduł jest niepotrzebny i nie działa na windowsie
    import readline
    readline.read_init_file()

# Nie trzeba tu try i except, bo config jest otwierany pierwszy w komendy.py
with open("config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.Loader)

if not os.path.exists('Karty_audio') and config['save_path'] == 'Karty_audio':
    os.mkdir('Karty_audio')  # Aby nie trzeba było tworzyć folderu ręcznie

try:
    with open("ankiconnect.yml", "r") as a:
        ankiconf = yaml.load(a, Loader=yaml.Loader)
except FileNotFoundError:
    with open("ankiconnect.yml", "w") as a:
        a.write('{}')

__version__ = 'v0.6.0-11'

print(f"""{BOLD}- Dodawacz kart do Anki {__version__} -{END}\n
Wpisz "--help", aby wyświetlić pomoc\n\n""")

requests_session_ah = requests.Session()

# Ustawia kolory
YEX = k.colors[config['attention_c']]
GEX = Fore.LIGHTGREEN_EX
R = Fore.RESET

syn_color = k.colors[config['syn_c']]
psyn_color = k.colors[config['psyn_c']]
pidiom_color = k.colors[config['pidiom_c']]
def1_color = k.colors[config['def1_c']]
def2_color = k.colors[config['def2_c']]
index_color = k.colors[config['index_c']]
word_color = k.colors[config['word_c']]
pos_color = k.colors[config['pos_c']]
etym_color = k.colors[config['etym_c']]
synpos_color = k.colors[config['synpos_c']]
syndef_color = k.colors[config['syndef_c']]
error_color = k.colors[config['error_c']]
delimit_color = k.colors[config['delimit_c']]

inputtext_color = ''
input_color = ''
if sys.platform.startswith('linux'):
    inputtext_color = k.colors[config['inputtext_c']]
    input_color = k.colors[config['input_c']]
    # Aby nie kombinować z robieniem tych kolorów na windowsie,
    # bo to wymaga rozwiązań co tylko zaśmiecają kod
    # i powodują denerwujący wizualny bug podczas zmiany wielkości okna


def delete_last_card():
    try:
        with open('karty.txt', 'r') as read:
            lines = read.readlines()
        with open('karty.txt', 'w') as write:
            deleted_line = lines.pop().replace('\n', '')
            new_file = ''.join(lines)
            write.write(new_file)
        print(f'{YEX}Usunięto z karty.txt: \n{R}"{deleted_line[:64]}..."')
    except IndexError:
        print(f'{error_color}Plik {R}karty.txt {error_color}jest pusty, nie ma co usuwać')
    except FileNotFoundError:
        print(f'{error_color}Plik {R}karty.txt {error_color}nie istnieje, nie ma co usuwać')
    except UnicodeDecodeError:
        print(f'{error_color}Usuwanie karty nie powiodło się z powodu nieznanego znaku (prawdopodobnie w etymologii)')  # wolfram
    except Exception:
        print(f'{error_color}Coś poszło nie tak podczas usuwania karty, ale karty są {GEX}bezpieczne')
        raise


# Komendy i input słowa
def save_commands(komenda, wartosc):
    if komenda == '-all':
        for command in list(dict.values(k.search_commands))[:9]:
            config[command] = wartosc
    else:
        config[komenda] = wartosc
    with open("config.yml", "w") as conf_file:
        yaml.dump(config, conf_file)


def config_bulk():
    input_list = ('Wartość dla definicji', 'Wartość dla części mowy',
                  'Wartość dla etymologii', 'Wartość dla synonimów',
                  'Wartość dla przykładów synonimów', 'Wartość dla przykładów idiomów')
    values_to_save = []
    print(f'{BOLD}Konfiguracja bulk, podaj wartość >= -1{END}')
    try:
        for input_msg, command in zip(input_list, k.bulk_cmds):
            value = int(input(f'{input_color}{input_msg}:{inputtext_color} '))
            if value >= -1:
                values_to_save.append(value)
                print(f'{GEX}OK')
            else:
                values_to_save.append(0)
                print(f'{error_color}Podano nieobsługiwaną wartość\n'
                      f'{R}{input_msg} {error_color}zmieniona na: {R}0')
    except ValueError:
        print(f'{YEX}Opuszczam konfigurację\nWprowadzone zmiany nie zostaną zapisane')
        return None

    print(f'\n{GEX}Konfiguracja masowego dodawania zapisana pomyślnie')
    for cmd, value_ts, input_mesg in zip(k.bulk_cmds, values_to_save, input_list):
        print(f'{input_mesg}: {value_ts}')
        save_commands(komenda=cmd, wartosc=value_ts)
    print()


def print_config():
    commands = list(dict.keys(k.search_commands))
    commands.pop(16)      # usuwa -all
    cmds = commands[:15]  # pierwsza kolumna do -mergeidiom
    cmds.insert(10, '')   # blank po -karty
    cmds.insert(14, '')   # blank po -bulkfsyn
    # druga kolumna wszystko co pozostało
    sndcolumn = commands[15:29]
    sndcolumn.insert(30, '')  # blank po -center
    sndcolumn.insert(31, f'{BOLD}[config ankiconnect]{END}')
    sndcolumn += commands[29:35]
    # trzecia kolumna
    thrcolumn = k.bulk_cmds + commands[35:]
    thrcolumn.insert(6, '')
    thrcolumn.insert(7, f'{BOLD}[config audio]{END}')
    print(f'\n{R}{BOLD}[config dodawania]      [config miscellaneous]      [config bulk]{END}')
    for first_column_cmd, second_column_cmd, third_column_cmd in zip_longest(cmds, sndcolumn, thrcolumn, fillvalue=''):
        # pierwsza kolumna
        config_cmd = config.get(k.search_commands.get(first_column_cmd, ''), '')
        cmd_color = k.bool_colors.get(config_cmd, '')

        # druga kolumna
        config_cmd_misc = '  ' + str(config.get(k.search_commands.get(second_column_cmd, ''), ''))
        cmd_color_misc = k.bool_colors.get(config.get(k.search_commands.get(second_column_cmd, ''), ''), '')
        if '*' in config_cmd_misc:
            config_cmd_misc = config_cmd_misc.lstrip()

        # trzecia kolumna
        blk_conf = config.get(third_column_cmd.lstrip('-'), '')
        if str(blk_conf).isnumeric():  # Aby wartość z minusem była left-aligned
            blk_conf = ' ' + str(blk_conf)

        print(f'{first_column_cmd:14s}{cmd_color}{str(config_cmd):10s}{R}'
              f'{second_column_cmd:14s}{cmd_color_misc}{config_cmd_misc:14s}{R}'
              f'{third_column_cmd:11s}{blk_conf}')

    print(f'\n--audio-path: {config.get("save_path", "")}')
    print('\nkonfiguracja kolorów --config-colors\n')


def kolory(komenda, wartosc):
    msg_color = k.colors[wartosc]
    print(f'{R}{k.color_message[komenda]} ustawiony na: {msg_color}{wartosc}')
    save_commands(komenda=komenda.strip('-').replace('-', '_'), wartosc=wartosc)


def set_width_settings(command, value):
    try:
        term_width_auto = str(os.get_terminal_size()).lstrip('os.terminal_size(columns=').split(',')[0]
        term_width = int(term_width_auto)
        term_er = False
    except OSError:
        term_er = True
    else:
        if value == 'auto' and not command == '-indent':
            print(f'{GEX}OK')
            return save_commands(komenda=command.strip('-'), wartosc=f'{term_width}* auto')
    max_val = 382  # 4k monospace 12
    if command == '-indent':
        max_val = conf_to_int(config['textwidth']) // 2
    try:
        val = int(value)
        if 0 <= val <= max_val:
            print(f'{GEX}OK')
            val = val
        elif val > max_val:
            print(f'{error_color}Wartość nie może być większa niż {R}{max_val}\n'
                  f'{YEX}Ustawiono: {R}{max_val}')
            val = max_val
        else:
            print(f'{error_color}Wartość nie może być ujemna\n{YEX}Ustawiono: {R}0')
            val = 0
        save_commands(komenda=command.strip('-'), wartosc=val)
    except ValueError:
        if not term_er and not command == '-indent':
            print(f'''{error_color}Nieobsługiwana wartość
podaj liczbę w przedziale od {R}0{error_color} do {R}{max_val}{error_color} lub {R}auto''')
        else:
            print(f'''{error_color}Nieobsługiwana wartość
podaj liczbę w przedziale od {R}0{error_color} do {R}{max_val}''')


def add_notes(note_name):
    note_config = notatki.available_notes.get(note_name)
    if note_config is not None:
        resp = create_note(note_config)
        if resp is not None:
            print(f'\n{resp}\n')
        else:
            print()
    else:
        available_notes = ', '.join(notatki.available_notes.keys())
        if note_name != '':
            print(f'{error_color}Notatka {R}"{note_name}" {error_color}nie została znaleziona')
        print(f'{R}{BOLD}Dostępne notatki to:{END}\n{available_notes}\n')


def change_fields_order(numb, field_name):
    default_field_order = {'1': 'definicja', '2': 'synonimy', '3': 'przyklady', '4': 'phrase',
                           '5': 'zdanie', '6': 'czesci_mowy', '7': 'etymologia', '8': 'audio'}
    field_order = config['fieldorder']
    if numb in default_field_order and field_name in default_field_order.values():
        field_order[numb] = field_name
    elif numb == 'd' and field_name in default_field_order:
        save_commands(komenda='fieldorder_d', wartosc=str(field_name))
    elif numb == 'default':
        field_order = default_field_order
        save_commands(komenda='fieldorder_d', wartosc='3')
        print(f'{GEX}Przywrócono domyślną kolejność pól:')
    elif numb == '-' and field_name == '-':
        print(f'{BOLD}Aktualna kolejność pól:{END}')
    else:
        print(f'{error_color}Podano nieprawidłowe parametry')
        return None
    save_commands(komenda='fieldorder', wartosc=field_order)
    for numb, numb_def in zip(field_order, default_field_order):
        yex = ''
        default = ''
        # wyświetla domyślną konfigurację pól
        if field_order[numb] != default_field_order[numb_def]:
            yex = YEX
            default = f'# {default_field_order[numb_def]}'
        printe = '{}{}{}{:20s}{}{}{}'.format(yex, numb, ': ', field_order[numb], END, R, default)
        if numb == '1':
            print(f' {BOLD}{printe}')
        else:
            print(f' {printe}')
        if numb == config['fieldorder_d']:
            print(f' {delimit_color}D: -----------{R}')


def refresh_notes():
    try:
        with open('ankiconnect.yml', 'w') as ank:
            ank.write('{}')
    except FileNotFoundError:
        print(f'{error_color}Plik {R}ankiconnect.yml{error_color} nie istnieje')
    else:
        organize_notes(k.base_fields, adqt_mf_config={}, print_errors=False)
        print(f'{YEX}Notatki przebudowane')


def komendo(word):
    one_word_commands = {'-colors': k.pokaz_dostepne_kolory, '-color': k.pokaz_dostepne_kolory,
                         '--delete-last': delete_last_card, '--delete-recent': delete_last_card,
                         '--config-bulk': config_bulk, '-conf': print_config, '-config': print_config,
                         '-h': k.help_command, '--help': k.help_command, '--help-bulk': k.help_bulk_command,
                         '--help-commands': k.help_commands_command, '--help-command': k.help_commands_command,
                         '--help-colors': k.color_command, '--help-color': k.color_command,
                         '--config-colors': k.color_command, '--config-color': k.color_command}
    loc_word = word + ' '
    cmd_tuple = loc_word.split(' ')
    cmd_tuple[0] = cmd_tuple[0].lower()
    if cmd_tuple[0] in k.search_commands:
        if cmd_tuple[0] in ('-textwidth', '-indent', '-delimsize', '-center'):
            set_width_settings(command=cmd_tuple[0], value=cmd_tuple[1])
        elif cmd_tuple[0] == '-note' or cmd_tuple[0] == '-deck':
            value = " ".join(cmd_tuple[1:]).strip()
            msgdiff = {'-note': 'według', '-deck': 'do'}
            save_commands(cmd_tuple[0].lstrip('-'), value)
            print(f'{YEX}Karty będą dodawane {msgdiff[cmd_tuple[0]]}: {R}"{value}"')
        elif cmd_tuple[0] == '-tags':
            tagi = "".join(cmd_tuple[1:]).strip(', ').lower().replace(',', ', ')  # tagi w anki są zawsze lowercase
            save_commands(cmd_tuple[0].lstrip('-'), tagi)
            print(f'{YEX}Tagi dla AnkiConnect: {R}"{tagi}"')
        elif cmd_tuple[0] == '-dupscope':
            # ten strip, aby wywalić te znaki jak sie je przypadkowo naciśnie przy wciskaniu enter
            scope_val = cmd_tuple[1].strip(r"']\,. ").lower()
            msgdiff = {'deck': 'talii', 'collection': 'całej kolekcji'}
            if scope_val == 'deck' or scope_val == 'collection':
                save_commands(cmd_tuple[0].lstrip('-'), scope_val)
                print(f'{YEX}Duplikaty sprawdzane w obrębie {R}{msgdiff[scope_val]}')
            else:
                print(f'{BOLD}Dostępne opcje:{END}\n'
                      f'deck, collection\n')
        elif cmd_tuple[0] == '-server':
            server_val = cmd_tuple[1].strip(r"']\,. ").lower()
            if cmd_tuple[1] in ('ahd', 'lexico', 'diki'):
                save_commands(cmd_tuple[0].lstrip('-'), server_val)
                print(f'{YEX}Preferowany serwer audio dla AHD: {R}{server_val}')
            else:
                print(f'{BOLD}Dostępne serwery audio:{END}\n'
                      f'ahd, lexico, diki\n')

        elif cmd_tuple[1] in k.commands_values:
            komenda = k.search_commands[cmd_tuple[0]]
            wartosc = k.commands_values[cmd_tuple[1]]
            msg_color = k.bool_colors[wartosc]
            msg = k.commands_msg[cmd_tuple[0]]
            print(f'{R}{msg}{msg_color}{wartosc}')
            save_commands(komenda, wartosc)
        else:
            print(f'{error_color}Nieprawidłowa wartość{R}\nUżyj "{cmd_tuple[0]} [on/off]"')
    elif cmd_tuple[0] in one_word_commands:
        one_word_commands[cmd_tuple[0]]()
    elif cmd_tuple[0] == '--add-note':
        add_notes(note_name=cmd_tuple[1])
    elif cmd_tuple[0] == '-notes' and cmd_tuple[1] in ('refresh', 'r'):
        refresh_notes()
    elif cmd_tuple[0] in ('-fieldsorder', '-fieldorder', '-fo'):
        try:
            numb = cmd_tuple[1].lower().strip(r"']\,. ")
            field_name = cmd_tuple[2].lower().strip(r"']\,. ")
        except IndexError:
            numb = '-'
            field_name = '-'
        change_fields_order(numb, field_name)
        print()
    elif cmd_tuple[0] == '--audio-path' or cmd_tuple[0] == '--save-path':
        print(f'{YEX}Pliki audio będą zapisywane w: {R}"{cmd_tuple[1]}"')
        save_commands(komenda='save_path', wartosc=cmd_tuple[1])
    elif cmd_tuple[0] in k.color_commands:
        if cmd_tuple[1] in k.colors:
            kolory(komenda=cmd_tuple[0], wartosc=cmd_tuple[1])
        else:
            print(f'{error_color}Nie znaleziono koloru{R}\n'
                  f'Aby wyświetlić listę dostępnych kolorów wpisz "-colors"')
    else:
        return word


def szukaj():
    word = input(f'{input_color}Szukaj:{inputtext_color} ').strip()
    word = komendo(word)
    if word == '':
        return None
    return word


def get_audio_response(audio_link, audiofile_name):
    try:
        with open(os.path.join(config['save_path'], audiofile_name), 'wb') as file:
            response = requests_session_ah.get(audio_link)
            file.write(response.content)
        return f'[sound:{audiofile_name}]'
    except IsADirectoryError:  # jest to efekt zapisywania pliku o nazwie ''
        return ''
    except FileNotFoundError:
        print(f"{error_color}Zapisywanie pliku audio {R}{audiofile_name} {error_color}nie powiodło się\n"
              f"Aktualna ścieżka zapisu audio to {R}{config['save_path']}\n"
              f"{error_color}Upewnij się, że taki folder istnieje i spróbuj ponownie\n")
        return ''
    except Exception:
        print(f'{error_color}Wystąpił nieoczekiwany błąd podczas zapisywania audio')
        raise


def request_diki(url):
    reqs = requests.get(url)
    audiosoup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    url_boxes = audiosoup.findAll('span', {'class': 'audioIcon icon-sound dontprint soundOnClick'})
    return url_boxes


def find_audiofile_name_in_diki(url_boxes, dk_filename):
    url_box = url_boxes
    for recording in url_boxes:
        if dk_filename in str(recording):
            url_box = recording
            break
    return url_box


def audio_diki(url, diki_link, partial_check):
    full_url = url + diki_link
    url_boxes = request_diki(full_url)
    dk_filename = '_'.join(diki_link.split(' '))
    url_box = find_audiofile_name_in_diki(url_boxes, dk_filename)
    # dla wyrażeń typu: burst the bubble of (somebody)
    # diki preferuje użycie formy "somebody's" zamiast "of"
    # pozbycie się "of" daje pożądany wynik
    if 'of' in diki_link and url_box == url_boxes:  # nie wiem jak najlepiej sprawdzić identity tutaj
        diki_link = diki_link.replace(' of', '')
        full_url = url + diki_link
        # url_box zamiast url_boxes, aby handling przeszedł dalej,
        # bo usunięcie " of" nie zmieni zachowania find_audiofile_name_in_diki
        url_box = request_diki(full_url)
    try:
        end_of_url = str(url_box).split('data-audio-url=')[1]
        end_of_url = end_of_url.split(' tabindex')[0].strip('"')
        audiofile_name = end_of_url.split('/')[-1]
        # Aby diki nie linkowało audio pierwszego słowa z idiomu
        # dla wyrażeń typu: as ..., if ...
        last_word_in_af = diki_link.split(' ')[-1]
        audiofile_name_bare = audiofile_name.split('.mp3')[0]
        audiofile_added_in_full = audiofile_name_bare.endswith(last_word_in_af)
        # to oznacza, że dk_filename zostało znalezione,
        # jak nie zostanie znalezione to wyniki z linii 398 i 400 są listami
        if url_box != url_boxes:
            pass
        # dla wyrażeń typu: account for, abide by
        elif len(audiofile_name_bare.split('_')) >= len(diki_link.split(' ')) and\
                audiofile_name_bare.split('_')[-1] in ('something', 'somebody'):
            pass
        # gdy partial_check is true, lepsze nic niż rydz
        elif not audiofile_added_in_full and not partial_check or\
                len(audiofile_name.split('.mp3')[0]) < 4 and len(diki_link.split(' ')) > 2 and partial_check:
            raise IndexError
    except IndexError:
        if not partial_check:
            print(f"{error_color}Diki nie posiada pożądanego audio\n{YEX}Spróbuję dodać co łaska...")
            paren_numb = phrase.count(')')
            if paren_numb == 1:
                if phrase.startswith('('):
                    attempt = phrase.split(') ')[-1]
                elif phrase.endswith(')'):
                    attempt = phrase.split(' (')[0]
                else:
                    attempt = phrase.split(' (')[0] + phrase.split(')')[-1]
            elif paren_numb > 1:
                # dla wyrażeń typu: boil (something) down to (something) -> boil down to
                # albo: Zip (up) your lip(s) -> Zip your lip
                split_phrase = phrase.split('(')
                second_sp = ''
                for sp in split_phrase[:2]:
                    second_sp = sp.split(') ')[-1]
                attempt = split_phrase[0] + second_sp.rstrip()
            else:
                longest_word = max(diki_link.split(), key=len)
                if longest_word not in ('somebody', 'something'):
                    attempt = longest_word
                else:
                    attempt = phrase
            return audio_diki(url='https://www.diki.pl/slownik-angielskiego?q=', diki_link=attempt, partial_check=True)
        else:
            print(f"{error_color}Nie udało się pozyskać audio\nKarta zostanie dodana bez audio")
            return '', ''
    else:
        audio_link = 'https://www.diki.pl' + end_of_url
        if partial_check:
            print(f'{GEX}Sukces')
        return audio_link, audiofile_name


def audio_ahd(url):
    reqs = requests_session_ah.get(url)
    soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    audio_raw = soup.find('a', {'target': '_blank'}).get('href')
    if audio_raw == 'http://www.hmhco.com':
        print(f"{error_color}AHD nie posiada pożądanego audio\n{YEX}Sprawdzam diki...")
        return audio_diki(url='https://www.diki.pl/slownik-angielskiego?q=', diki_link=phrase, partial_check=True)
    audiofile_name = audio_raw.split('/')[-1]
    audiofile_name = audiofile_name.split('.')[0] + '.wav'
    audio_link = 'https://www.ahdictionary.com'
    audio_link += audio_raw
    return audio_link, audiofile_name


def audio_lexico(url):
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    audio_url_box = soup.find('a', class_='speaker')
    if audio_url_box is None:
        print(f"{error_color}Lexico nie posiada pożądanego audio\n{YEX}Sprawdzam diki...")
        return audio_diki(url='https://www.diki.pl/slownik-angielskiego?q=', diki_link=phrase, partial_check=True)
    full_audio_link = str(audio_url_box).split('src="')[-1].split('">')[0]
    audiofile_name = full_audio_link.split('/')[-1]
    return full_audio_link, audiofile_name


def search_for_audio(server):
    if config['dodaj_audio']:
        try:
            if server == 'ahd':
                audio_link, audiofile_name = audio_ahd(url='https://www.ahdictionary.com/word/search.html?q=' + phrase)
            elif server == 'lexico':
                lexico_url = 'https://www.lexico.com/definition/'
                audio_link, audiofile_name = audio_lexico(url=lexico_url + phrase.replace(' ', '_'))
            else:
                diki_link = phrase.replace('(', '').replace(')', '')
                diki_link = diki_link.replace(' or something', '').replace('someone', 'somebody')
                audio_link, audiofile_name = audio_diki(url='https://www.diki.pl/slownik-angielskiego?q=',
                                                        diki_link=diki_link, partial_check=False)
            return get_audio_response(audio_link, audiofile_name)
        except Exception:
            print(f'{error_color}Wystąpił problem podczas szukania pliku audio')
            raise
    return ''


def print_elems(string, term_width, index_width, indento, gap, break_allowed):
    br = ''
    if break_allowed and config['break']:
        br = '\n'
    if config['wrap_text']:
        wrapped_text = ''
        indent = indento + index_width
        string_divided = string.split(' ')
        real_width = int(term_width) - index_width - gap  # gap to przerwa między indeksami, a definicją
        if len(string) > real_width:
            # individual line length
            indiv_llen = 0
            for word, nextword in zip(string_divided, string_divided[1:]):
                indiv_llen += len(word) + 1  # 1 to spacja, która znika przy string.split(' ')
                if len(nextword) + 1 + indiv_llen > real_width:
                    wrapped_text += word + '\n' + indent * ' '
                    indiv_llen = indento - gap
                else:
                    wrapped_text += word + ' '
                    # definicja + ostatnie słowo
            return wrapped_text + string_divided[-1] + br
    return string + br


# Kolorowanie bazując na enumeracji
def ah_def_print(indexing, term_width, definition):
    definition_aw = print_elems(definition, term_width, index_width=len(str(indexing)), indento=config['indent'],
                                gap=2, break_allowed=True)
    if indexing % 2 == 1:
        print(f"{index_color}{indexing}  {def1_color}{definition_aw}")
    else:
        print(f"{index_color}{indexing}  {def2_color}{definition_aw}")


def terminal_width():
    try:
        term_width = str(config['textwidth'])
    except KeyError:
        print(f'{error_color}Plik {R}config.yml{error_color} jest niekompletny\n'
              f'Wypełnij plik konfiguracyjny')
        return 79
    try:
        term_width_auto = str(os.get_terminal_size()).lstrip('os.terminal_size(columns=').split(',')[0]
        term_width_auto = int(term_width_auto)
    except OSError:
        if '* auto' in term_width:
            print(f'''{error_color}Wystąpił problem podczas pozyskiwania szerokości okna
aby wybrać szerokość inną niż {R}{term_width.rstrip('* auto')}{error_color} użyj {R}-textwidth [wartość]''')
            save_commands(komenda='textwidth', wartosc=term_width.rstrip('* auto'))
        return int(term_width.rstrip('* auto'))
    else:
        if '* auto' in term_width:
            save_commands(komenda='textwidth', wartosc=f'{term_width_auto}* auto')
            term_width = int(term_width_auto)
            return term_width
        elif int(term_width.rstrip('* auto')) > term_width_auto:
            term_width = term_width_auto
        return conf_to_int(term_width)


# Funkcja do konwertowania configu dla f'' stringów
def conf_to_int(conf_val):
    string = str(conf_val).rstrip('* auto')
    return int(string)


# Rysowanie AHD
def rysuj_slownik(url):
    global phrase
    global skip_check
    term_width = terminal_width()
    if config['indent'] > term_width // 2:
        save_commands(komenda='indent', wartosc=term_width // 2)
    if '* auto' in str(config['delimsize']):
        save_commands(komenda='delimsize', wartosc=f'{term_width}* auto')
    if '* auto' in str(config['center']):
        save_commands(komenda='center', wartosc=f'{term_width}* auto')
    try:
        reqs = requests_session_ah.get(url, timeout=10)
        soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
        word_check = soup.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
        if len(word_check) == 0:
            print(f'{error_color}Nie znaleziono podanego hasła w AH Dictionary\n{YEX}Szukam w idiomach...')
            skip_check = 1
        else:
            indexing = 0
            correct_word_index = 0
            for td in soup.find_all('td'):
                meanings_in_td = td.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
                print(f'{delimit_color}{conf_to_int(config["delimsize"]) * "-"}')
                for meaning_num in td.find_all('font', {'color': '#006595'}, 'sup'):
                    # Rysuje bat·ter 1, bat·ter 2 itd.
                    # Aby przy wyszukiwaniu nieprawidłowego wpisu, np. "impeachment" zamiast "impeach", dodało "impeach"
                    correct_word_index += 1
                    if correct_word_index == 1 or correct_word_index == 2:  # Aby preferować lowercase wersję słowa
                        correct_word0 = meaning_num.text
                        correct_word1 = correct_word0.replace('·', '')
                        correct_word_to_print = re.sub(r'\d', '', correct_word1).strip()
                        phrase = correct_word_to_print.strip('-–')
                        if correct_word_index == 1:
                            wdg = f'{BOLD}Wyniki dla {word_color}{correct_word_to_print}{END}'
                            # RESET i BOLD jest brane pod uwagę przy center
                            print(wdg.center(conf_to_int(config['center']) + 12))
                    print(f'  {word_color}{meaning_num.text}')
                for meaning in meanings_in_td:  # Rysuje definicje
                    indexing += 1
                    rex0 = re.sub("[.][a-z][.]", ".", meaning.text)
                    rex1 = re.sub("[0-9][.]", "", rex0)
                    rex2 = re.sub("\\A[1-9]", "", rex1)
                    rex3 = re.sub("\\A\\sa[.]", "", rex2)
                    rex4_tp = rex3.strip()  # to print
                    rex5 = rex4_tp.split(' See Usage Note at')[0]
                    rex5 = rex5.split(' See Synonyms at')[0]

                    if config['pokazuj_filtrowany_slownik']:
                        ah_def_print(indexing, term_width, definition=rex4_tp)  # .replace('', '')) trzeba to znaleźć
                    else:
                        ah_def_print(indexing, term_width, definition=meaning.text)

                    definicja.append(hide_phrase_in(rex5, hide='ukryj_slowo_w_definicji'))

                print()
                for pos in td.find_all(class_='runseg'):  # Dodaje części mowy
                    postring = pos.text.replace('', 'oo').replace('', 'oo').replace('', '′').replace('·', '').strip()
                    print(f'{pos_color}{postring}')
                    czesci_mowy.append(postring)
                if not str(czesci_mowy).startswith('[]'):
                    print()
                for etym in td.find_all(class_='etyseg'):  # Dodaje etymologie
                    print(f'{etym_color}'
                          f'{print_elems(etym.text, term_width, index_width=0, indento=0, gap=0, break_allowed=False)}')
                    etymologia.append(etym.text)
            # Aby przy hasłach bez etymologii lub części mowy nie było niepotrzebnych spacji
            if not str(etymologia).startswith('[]'):
                print()
    except ConnectionError:
        print(f'{error_color}Nie udało się połączyć ze słownikiem, sprawdź swoje połączenie i spróbuj ponownie')
        skip_check = 1
    except Timeout:
        print(f'{error_color}AH Dictionary nie odpowiada')
        skip_check = 1
    except Exception:
        print(f'{error_color}Wystąpił nieoczekiwany błąd')
        raise


def ogarnij_zdanie(exsentence):
    global skip_check
    if exsentence == '-s':
        print(f'{GEX}Pominięto dodawanie zdania')
        return ''
    elif exsentence == '':
        return ''
    elif exsentence == '-sc':
        skip_check = 1
        print(f'{GEX}Pominięto dodawanie karty')
    else:
        return hide_phrase_in(exsentence, hide='ukryj_slowo_w_zdaniu')


def zdanie_input():
    if config['dodaj_wlasne_zdanie']:
        exsentence = str(input(f'{input_color}Dodaj przykładowe zdanie:{inputtext_color} '))
        return exsentence
    return ''


# Sprawdzanie co wpisano w polach input
def input_func(choice, elem_content, hide, connector, boolean_choice):
    if choice.isnumeric() or choice == '-1':
        return singular_choice(int(choice), elem_content, connector, boolean_choice)
    elif choice == '' or choice == '-s':
        return singular_choice(0, elem_content, connector, boolean_choice)
    elif choice == 'all':
        return singular_choice(-1, elem_content, connector, boolean_choice)

    elif choice.startswith('/'):
        return hide_phrase_in(choice.replace('/', '', 1), hide)
    elif ',' in choice:
        return multiple_choice(choice.strip().split(','), elem_content, connector)
    return singular_choice(-2, elem_content, connector, boolean_choice)


# Adekwatne pola input dla pól wyboru
def disamb_input_syn():
    if config['dodaj_synonimy']:
        if config['bulk_add'] and not config['bulk_free_syn']:
            return str(config['syn_blk'])
        if not config['bulk_add'] or config['bulk_free_syn']:
            wybor_disamb_syn = input(f'{input_color}Wybierz grupę synonimów:{inputtext_color} ')
            return wybor_disamb_syn
    return 0


def disamb_input_przyklady():
    if config['dodaj_przyklady_synonimow']:
        if config['bulk_add']:
            return str(config['psyn_blk'])
        wybor_disamb_przyklady = input(f'{input_color}Wybierz grupę przykładów:{inputtext_color} ')
        return wybor_disamb_przyklady
    return 0


def farlex_input_przyklady():
    if config['dodaj_przyklady_idiomow']:
        if config['bulk_add']:
            return str(config['pidiom_blk'])
        wybor_przykladow_idiomow = input(f'{input_color}Wybierz przykład:{inputtext_color} ')
        return wybor_przykladow_idiomow
    return 0


def etymologia_input():
    if config['dodaj_etymologie']:
        if config['bulk_add']:
            return str(config['etym_blk'])
        wybor_etymologii = input(f'{input_color}Wybierz etymologię:{inputtext_color} ')
        return wybor_etymologii
    return 0


def czesci_mowy_input():
    if config['dodaj_czesci_mowy']:
        if config['bulk_add']:
            return str(config['pos_blk'])
        wybor_czesci_mowy = input(f'{input_color}Dołączyć części mowy? [1/0]:{inputtext_color} ')
        return wybor_czesci_mowy
    return 0


def definicje_input():
    if config['dodaj_definicje']:
        if config['bulk_add'] and not config['bulk_free_def']:
            return str(config['def_blk'])
        if not config['bulk_add'] or config['bulk_free_def']:
            wybor_definicji = input(f'{input_color}\nWybierz definicję:{inputtext_color} ')
            return wybor_definicji
    return 0


def multiple_choice(wybor, elem_content, connector):
    content_list = []
    choice_nr = ''
    for choice in wybor:
        try:
            if int(choice) > 0:
                if elem_content[int(choice) - 1] != '':
                    content_list.append(elem_content[int(choice) - 1])
                choice_nr += choice.strip() + ', '
        except (ValueError, IndexError, TypeError):
            continue
    print(f'{YEX}Dodane elementy: {choice_nr.rstrip(", ")}')
    return connector.join(content_list)


# Bierze wybór z input_func i wydaje adekwatne informacje na kartę
def singular_choice(wybor, elem_content, connector, boolean_choice):
    global skip_check
    if len(elem_content) >= wybor > 0 and not boolean_choice:
        return elem_content[wybor - 1]
    elif wybor > len(elem_content) or wybor == -1 or boolean_choice and wybor >= 1:
        no_blanks = [x for x in elem_content if x != '']
        return connector.join(no_blanks)
    elif wybor == -2:
        skip_check = 1
        print(f'{GEX}Pominięto dodawanie karty')
    else:  # czyli 0
        return ''


def rysuj_synonimy(syn_soup):
    syn_stream = []
    for synline in syn_soup.find_all('li'):
        syn_stream.append(synline.text)
    for index, ele in enumerate(syn_stream, start=1):
        przyklady0 = re.findall(r'\"(.+?)\"', ele)
        przyklady1 = re.sub("[][]", "", str(przyklady0))  # do dodania na kartę
        przyklady2 = re.sub("',", "'\n   ", przyklady1)
        przyklady4 = re.sub(r"\A[']", "\n    '", przyklady2)  # do narysowania
        synonimy0, sep, tail = ele.partition('"')  # oddziela synonimy od przykładów
        synonimy1 = synonimy0.replace("S:", "")  # do rysowania synonimów z kategoryzacją wordnetu

        syndef0 = synonimy1.split('(', 2)[2]
        syndef = '(' + syndef0
        pos = synonimy1.split(')')[0]
        pos = pos + ')'

        synonimy2 = re.sub(r"\([^()]*\)", "", synonimy1)  # usuwa pierwszy miot nawiasów
        synonimy3 = re.sub(r"\(.*\)", "", synonimy2)  # usuwa resztę nawiasów
        synonimy4 = re.sub(r"\s{2}", "", synonimy3)

        grupa_przykladow.append(hide_phrase_in(przyklady1, hide='ukryj_slowo_w_disamb'))
        grupa_synonimow.append(hide_phrase_in(synonimy4, hide='ukryj_slowo_w_disamb'))

        if config['showdisamb']:
            syn_tp = print_elems(synonimy4 + '\n   ', term_width=conf_to_int(config['textwidth']),
                                 index_width=len(str(index)),
                                 indento=3, gap=3 + len(str(pos)), break_allowed=False)
            syndef_tp = print_elems(syndef, term_width=conf_to_int(config['textwidth']), index_width=len(str(index)),
                                    indento=3, gap=3, break_allowed=False)
            print(f'{index_color}{index} : {synpos_color}{pos.lstrip()} {syn_color}{syn_tp} {syndef_color}'
                  f'{syndef_tp}{psyn_color}{przyklady4}\n')  # przykładów się nie opłaca zawijać
        else:
            ''


def disambiguator(url_synsearch):
    global skip_check_disamb
    try:
        # Wordnet nie zyskuje na szybkości gdy użyjemy requests.Session(),
        # może dlatego, że połączenie nie jest Keep-alive.
        # Albo nie ma ciasteczka, które by to połączenie przyspieszyło
        reqs_syn = requests.get(url_synsearch, timeout=10)
        syn_soup = BeautifulSoup(reqs_syn.content, 'lxml', from_encoding='iso-8859-1')
        no_word = syn_soup.find('h3')
        if len(str(no_word)) == 48 or len(str(no_word)) == 117:
            print(f'{error_color}\nNie znaleziono {word_color}{phrase}{error_color} na {R}WordNecie')
            skip_check_disamb = 1
        else:
            if config['showdisamb']:
                print(f'{delimit_color}{conf_to_int(config["delimsize"]) * "-"}')
                print(f'{Fore.LIGHTWHITE_EX}{"WordNet".center(conf_to_int(config["center"]))}\n')
            rysuj_synonimy(syn_soup)
    except ConnectionError:
        print(f'{error_color}Nie udało się połączyć z WordNetem, sprawdź swoje połączenie i spróbuj ponownie')
        skip_check_disamb = 1
    except Timeout:
        print(f'{error_color}WordNet nie odpowiada, spróbuj nawiązać połączenie później')
        skip_check_disamb = 1
    except Exception:
        print(f'{error_color}Wystąpił nieoczekiwany błąd podczas wyświetlania WordNetu\n')
        raise


def hide_phrase_in(content, hide):
    if hide == '':
        return content
    if config[hide]:
        hidden_content = content
        nonoes = (
            'a', 'A', 'an', 'An', 'the', 'The', 'or', 'Or', 'be', 'Be',
            'do', 'Do', 'does', 'Does', 'not', 'Not', 'if', 'If'
        )
        prepositions = ()
        if hide == 'ukryj_slowo_w_idiom' and not config['ukryj_przyimki']:
            prepositions = (
                'about', 'above', 'across', 'after', 'against', 'along', 'among', 'around', 'as', 'at', 'before',
                'behind', 'below', 'beneath', 'beside', 'between', 'beyond', 'by', 'despite', 'down', 'during', 'except',
                'for', 'from', 'in', 'inside', 'into', 'like', 'near', 'of', 'off', 'on', 'onto', 'opposite', 'out',
                'outside', 'over', 'past', 'round', 'since', 'than', 'through', 'to', 'towards', 'under', 'underneath',
                'unlike', 'until', 'up', 'upon', 'via', 'with', 'within', 'without'
            )
        words_th = phrase.lower().split(' ')
        words_th_s_exceptions = (x.rstrip('y')+'ies' for x in words_th if x.endswith('y'))
        words_th_ing_exceptions = (x.rstrip('e')+'ing' for x in words_th if x.endswith('e') and x not in prepositions and x not in nonoes)
        words_th_ing_exceptions2 = (x.rstrip('ie')+'ying' for x in words_th if x.endswith('ie'))
        words_th_ed_exceptions = (x.rstrip('y')+'ied' for x in words_th if x.endswith('y'))

        for word_th in words_th:
            if word_th not in nonoes and word_th not in prepositions:
                hidden_content = hidden_content.replace(word_th, '...').replace(word_th.capitalize(), '...')

        for wthse in words_th_s_exceptions:
            hidden_content = hidden_content.replace(wthse, '...s').replace(wthse.capitalize(), '...s')

        for wthinge in words_th_ing_exceptions:
            hidden_content = hidden_content.replace(wthinge, '...ing').replace(wthinge.capitalize(), '...ing')

        for wthinge2 in words_th_ing_exceptions2:
            hidden_content = hidden_content.replace(wthinge2, '...ying').replace(wthinge2.capitalize(), '...ying')

        for wthede in words_th_ed_exceptions:
            hidden_content = hidden_content.replace(wthede, '...ed').replace(wthede.capitalize(), '...ed')
        return hidden_content
    else:
        return content


def farlex_idioms(url_idiomsearch):
    global skip_check
    global phrase
    try:
        reqs_idioms = requests.get(url_idiomsearch, timeout=10)
        idiom_soup = BeautifulSoup(reqs_idioms.content, 'lxml', from_encoding='utf-8')
        idiom_div = idiom_soup.find('section', {'data-src': 'FarlexIdi'})
        try:
            idiom = idiom_div.h2.text
        except AttributeError:
            print(f'{error_color}Nie znaleziono podanego hasła')
            skip_check = 1
        else:
            indek = 0
            idiom_defs = idiom_div.findAll(class_=('ds-list', 'ds-single'))
            print(f'{conf_to_int(config["delimsize"])*"-"}')
            print(f'  {word_color}{idiom}')
            phrase = idiom
            for inx, defin in enumerate(idiom_defs, start=1):
                idiom_definition = defin.find(text=True, recursive=False)
                if len(str(idiom_definition)) < 5:
                    idiom_definition = str(defin).split('</i> ')[-1]
                    idiom_definition = idiom_definition.split(' <span class=')[0]
                idiom_def = re.sub(r'\d. ', '', str(idiom_definition))
                idiom_def = re.sub(r'\A\d', '', idiom_def)  # aby po indeksach większych od 9 nic nie zostało
                idiom_def = idiom_def.split(' In this usage, a noun or pronoun')[0]
                idiom_def = idiom_def.split(' In this usage, a reflexive pronoun')[0]
                idiom_def = idiom_def.split(' A noun or pronoun can be used between')[0]
                idiom_def = idiom_def.split(' A noun or pronoun does not have to')[0]
                idiom_def = idiom_def.replace('is be used between', 'is used between')  # czy "be used between" to błąd?
                idiom_def = idiom_def.replace('. In this usage, the phrase is typically written as one word', ' (typically written as one word)')
                idiom_def = idiom_def.replace('. In this usage, the phrase is commonly written as one word', ' (commonly written as one word)')
                idiom_def_tp = print_elems(idiom_def.strip(),
                                           term_width=conf_to_int(config['textwidth']),
                                           index_width=len(str(inx)), indento=config['indent']+1,
                                           gap=3, break_allowed=False)

                definicja.append(hide_phrase_in(idiom_def, hide='ukryj_slowo_w_idiom'))

                if indek == 0:
                    print(f'{index_color}{inx} : {def1_color}{idiom_def_tp}')
                else:
                    print(f'\n{index_color}{inx} : {def1_color}{idiom_def_tp}')

                idiom_illustrations = defin.findAll('span', {'class': 'illustration'})
                for illustration in idiom_illustrations:
                    indek += 1
                    illustration_tp = print_elems(illustration.text,
                                                  term_width=conf_to_int(config['textwidth']),
                                                  index_width=len(str(inx)), indento=config['indent']+4,
                                                  gap=8, break_allowed=False)

                    ilustracje.append(hide_phrase_in(illustration.text, hide='ukryj_slowo_w_idiom'))

                    print(f"{index_color}    {indek} {pidiom_color}'{illustration_tp}'")
            print()
    except ConnectionError:
        print(f'{error_color}Nie udało się połączyć ze słownikiem idiomów, sprawdź swoje połączenie i spróbuj ponownie')
        skip_check = 1
    except Timeout:
        print(f'{error_color}Słownik idiomów nie odpowiada, spróbuj nawiązać połączenie później')
        skip_check = 1
    except Exception:
        print(f'{error_color}Wystąpił nieoczekiwany błąd podczas wyświetlania słownika idiomów\n')
        raise


def request(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def invoke(action, **params):
    requestjson = json.dumps(request(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', requestjson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is None:
        return response['result']
    if response['error'].startswith('model was not found:'):
        return 'no note'
    if response['error'].startswith('cannot create note because it is empty'):
        return 'empty'
    if response['error'].startswith('cannot create note because it is a duplicate'):
        return 'duplicate'
    if response['error'].startswith('collection is not available'):
        return 'out of reach'
    if response['error'].startswith('deck was not found'):
        return 'no deck'
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def organize_notes(base_fields, adqt_mf_config, print_errors):
    usable_fields = invoke('modelFieldNames', modelName=config['note'])
    if usable_fields == 'no note':
        if print_errors:
            print(f'{error_color}Nie znaleziono notatki {R}{config["note"]}{error_color}\n'
                  f'Aby zmienić notatkę użyj {R}-note [nazwa notatki]')
        return 'no note'
    if usable_fields == 'out of reach':
        if print_errors:
            print(f'{error_color}Karta nie została dodana, bo kolekcja jest nieosiągalna\n'
                  f'Sprawdź czy Anki jest w pełni otwarte')
        return 'out of reach'

    for ufield in usable_fields:
        for base_field in base_fields:
            if base_field in ufield.lower().split()[0]:
                adqt_mf_config[ufield] = base_fields[base_field]
                break

    if adqt_mf_config != {}:  # aby puste notatki nie były zapisywane w ankiconf
        ankiconf[config['note']] = adqt_mf_config
        with open('ankiconnect.yml', 'w') as ank:
            yaml.dump(ankiconf, ank)


# Tworzenie karty
def utworz_karte():
    field_values = {'definicja': definicja, 'synonimy': synonimy, 'przyklady': przyklady, 'phrase': phrase,
                    'zdanie': zdanie, 'czesci_mowy': czesci_mowy, 'etymologia': etymologia, 'audio': audio}
    if config['ankiconnect']:
        adqt_model_fields = {}
        try:
            fields_ankiconf = ankiconf.get(config['note'], '')
            organize_err = ''  # aby wiadomości błędów się nie powielały
            if fields_ankiconf == {} or config['note'] not in ankiconf:  # aby nie sprawdzać dla znajomej notatki
                organize_err = organize_notes(k.base_fields, adqt_mf_config={}, print_errors=True)

            config_note = ankiconf.get(config['note'], '')
            # przywołanie pól notatki z ankiconf
            for field in config_note:
                adqt_model_fields[field] = field_values[config_note[field]]
            # r to id karty, albo error
            r = invoke('addNote', note={'deckName': config['deck'], 'modelName': config['note'], 'fields': adqt_model_fields,
                                        'options': {'allowDuplicate': config['duplicates'], 'duplicateScope': config['dupscope']},
                                        'tags': config['tags'].split(', ')})
            if r == 'empty':
                print(f'{error_color}Karta nie została dodana\n'
                      f'Pierwsze pole notatki nie zostało wypełnione\n'
                      f'Sprawdź czy notatka {R}{config["note"]}{error_color} zawiera wymagane pola\n'
                      f'lub jeżeli nazwy pól aktualnej notatki zostały zmienione, wpisz {R}-notes r')
            if r == 'duplicate':
                print(f'{error_color}Karta nie została dodana, bo jest duplikatem\n'
                      f'Zezwól na dodawanie duplikatów wpisując {R}-duplicates on\n'
                      f'{error_color}lub zmień zasięg sprawdzania duplikatów {R}-dupscope [deck/collection]')
            if r == 'out of reach' and organize_err != 'out of reach':
                print(f'{error_color}Karta nie została dodana, bo kolekcja jest nieosiągalna\n'
                      f'Sprawdź czy Anki jest w pełni otwarte')
            if r == 'no deck':
                print(f'{error_color}Karta nie została dodana, bo talia {R}{config["deck"]}{error_color} nie istnieje\n'
                      f'Aby zmienić talię wpisz {R}-deck [nazwa talii]')
            if r == 'no note' and organize_err != 'no note':
                print(f'{error_color}Karta nie została dodana\n'
                      f'Nie znaleziono notatki {R}{config["note"]}{error_color}\n'
                      f'Aby zmienić notatkę użyj {R}-note [nazwa notatki]')
            if r not in ('no note', 'duplicate', 'out of reach', 'empty', 'no deck'):
                print(f'{GEX}Karta dodana pomyślnie\n'
                      f'{YEX}Wykorzystane pola:')
                added_fields = (x for x in adqt_model_fields if adqt_model_fields[x].strip() != '')
                for afield in added_fields:
                    print(f'- {afield}')
                print()
        except URLError:
            print(f'{error_color}Nie udało się połączyć z AnkiConnect\n'
                  f'Otwórz Anki i spróbuj ponownie\n')
        except AttributeError:
            print(f'{error_color}Karta nie została dodana, bo plik "ankiconnect.yml" był pusty\n'
                  f'Zrestartuj program i spróbuj dodać ponownie')
            with open('ankiconnect.yml', 'w') as ank:
                ank.write('{}')
    try:
        with open('karty.txt', 'a', encoding='utf-8') as twor:
            twor.write(f'{field_values[config["fieldorder"]["1"]]}\t'
                       f'{field_values[config["fieldorder"]["2"]]}\t'
                       f'{field_values[config["fieldorder"]["3"]]}\t'
                       f'{field_values[config["fieldorder"]["4"]]}\t'
                       f'{field_values[config["fieldorder"]["5"]]}\t'
                       f'{field_values[config["fieldorder"]["6"]]}\t'
                       f'{field_values[config["fieldorder"]["7"]]}\t'
                       f'{field_values[config["fieldorder"]["8"]]}\n')
            print(f'{YEX}Karta zapisana do pliku\n')
    except (NameError, KeyError):
        print(f'{error_color}Dodawanie karty do pliku nie powiodło się\n'
              f'Spróbuj przywrócić domyślne ustawienia pól wpisując {R}-fo default\n')


def wyswietl_karte():
    field_values = {'definicja': definicja, 'synonimy': synonimy, 'przyklady': przyklady, 'phrase': phrase,
                    'zdanie': zdanie, 'czesci_mowy': czesci_mowy, 'etymologia': etymologia, 'audio': audio}
    ctf = {'definicja': def1_color, 'synonimy': syn_color, 'przyklady': psyn_color, 'phrase': word_color,
           'zdanie': '', 'czesci_mowy': pos_color, 'etymologia': etym_color, 'audio': ''}
    delimit = conf_to_int(config['delimsize'])
    centr = conf_to_int(config['center'])
    options = (conf_to_int(config['textwidth']), 0, 0, 0, False)

    try:
        print(f'\n{delimit_color}{delimit * "-"}')
        for field in config['fieldorder']:
            for fi in print_elems(field_values[config['fieldorder'][field]], *options).split('\n'):
                print(f'{ctf[config["fieldorder"][field]]}{fi.center(centr)}')
            if field == config['fieldorder_d']:
                print(f'{delimit_color}{delimit * "-"}')
        print(f'{delimit_color}{delimit * "-"}')
    except (NameError, KeyError):
        print(f'{error_color}\nDodawanie karty do pliku nie powiodło się\n'
              f'Spróbuj przywrócić domyślne ustawienia pól wpisując {R}-fo default\n')
        return 1  # skip_check


def create_note(note_config):
    try:
        connected = invoke('modelNames')
        if connected == 'out of reach':
            return f'{error_color}Wybierz profil, aby dodać notatkę'
    except URLError:
        return f'{error_color}Włącz Anki, aby dodać notatkę'
    try:
        if note_config['modelName'] in connected:
            return f'{YEX}Notatka {R}"{note_config["modelName"]}"{YEX} już znajduje się w bazie notatek'

        result = invoke('createModel',
                        modelName=note_config['modelName'],
                        inOrderFields=note_config['fields'],
                        css=note_config['css'],
                        cardTemplates=[{'Name': note_config['cardName'],
                                        'Front': note_config['front'],
                                        'Back': note_config['back']}])
        if result == 'out of reach':
            return f'{error_color}Nie można nawiązać połączenia z Anki\n' \
                   f'Notatka nie została utworzona'
        else:
            print(f'{GEX}\nNotatka utworzona pomyślnie\n')

        note_ok = input(f'{YEX}Chcesz ustawić {R}"{note_config["modelName"]}" {YEX}jako -note?{R} [T/n]: ')

        if note_ok.lower() in ('1', 't', 'y', 'tak', 'yes', ''):
            config['note'] = note_config['modelName']
            with open('config.yml', 'w') as conf_f:
                yaml.dump(config, conf_f)
        return None
    except URLError:
        return f'{error_color}Nie można nawiązać połączenia z Anki' \
               f'Notatka nie została utworzona'


start = True
try:
    while start:
        # Wszystkie pola muszą być resetowane, bo gdy zmieniamy ustawienia dodawania
        # to niektóre pola będą zapisywane na karcie nie zważając na zmiany ustawień
        skip_check = 0
        skip_check_disamb = 0
        farlex = False
        phrase = ''
        zdanie = ''
        audio = ''
        synonimy = ''
        przyklady = ''
        definicja = []
        czesci_mowy = []
        etymologia = []
        grupa_przykladow = []
        grupa_synonimow = []
        ilustracje = []
        while True:
            link_word = szukaj()
            if link_word is None:
                continue
            break
        while skip_check == 0:
            if not link_word.startswith('-idi'):
                rysuj_slownik('https://www.ahdictionary.com/word/search.html?q=' + link_word)
                if skip_check == 1:
                    skip_check = 0
                    farlex_idioms(url_idiomsearch='https://idioms.thefreedictionary.com/' + link_word)
                    farlex = True
                    if skip_check == 1:
                        break
            else:
                farlex_idioms(url_idiomsearch='https://idioms.thefreedictionary.com/' + link_word.replace('-idi ', ''))
                farlex = True
                if skip_check == 1:
                    break
            if config['tworz_karte']:
                if not farlex:
                    audio = search_for_audio(server=config['server'])
                    zdanie = ogarnij_zdanie(zdanie_input())  # Aby wyłączyć dodawanie zdania w bulk wystarczy -pz off
                    if skip_check == 1:  # ten skip_check jest niemożliwy przy bulk
                        break
                    definicja = input_func(choice=definicje_input(), elem_content=definicja,
                                           hide='ukryj_slowo_w_definicji', connector='<br>', boolean_choice=False)
                    if skip_check == 1:
                        break
                    czesci_mowy = input_func(choice=czesci_mowy_input(), elem_content=czesci_mowy,
                                             hide='', connector=' | ', boolean_choice=True)
                    if skip_check == 1:
                        break
                    etymologia = input_func(choice=etymologia_input(), elem_content=etymologia,
                                            hide='', connector='<br>', boolean_choice=False)
                    if skip_check == 1:
                        break
                    if config['disambiguation']:
                        disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + phrase)
                    if not config['bulk_add'] or config['bulk_add'] and \
                            (config['syn_blk'] != 0 or config['psyn_blk'] != 0 or config['bulk_free_syn']):
                        if skip_check_disamb == 0:
                            synonimy = input_func(choice=disamb_input_syn(), elem_content=grupa_synonimow,
                                                  hide='ukryj_slowo_w_disamb', connector=' | ', boolean_choice=False)
                            if skip_check == 1:
                                break
                            przyklady = input_func(choice=disamb_input_przyklady(), elem_content=grupa_przykladow,
                                                   hide='ukryj_slowo_w_disamb', connector='<br>', boolean_choice=False)
                            if skip_check == 1:
                                break
                        if config['mergedisamb']:
                            brek = '<br>'
                            if synonimy == '' or przyklady == '':
                                brek = ''
                            synonimy = synonimy + brek + przyklady
                            przyklady = ''
                else:
                    audio = search_for_audio(server='diki')
                    zdanie = ogarnij_zdanie(zdanie_input())
                    if skip_check == 1:
                        break
                    definicja = input_func(choice=definicje_input(), elem_content=definicja,
                                           hide='ukryj_slowo_w_definicji', connector='<br>', boolean_choice=False)
                    if skip_check == 1:
                        break
                    czesci_mowy = ''
                    etymologia = ''
                    przyklady = input_func(choice=farlex_input_przyklady(), elem_content=ilustracje,
                                           hide='ukryj_slowo_w_idiom', connector='<br>', boolean_choice=False)
                    if skip_check == 1:
                        break
                    if config['mergeidiom']:
                        brek = '<br><br>'
                        if definicja == '' or przyklady == '':
                            brek = ''
                        definicja = definicja + brek + przyklady
                        przyklady = ''
                if config['showcard']:
                    skip_check = wyswietl_karte()
                    if skip_check == 1:
                        break
                print()
                utworz_karte()
            else:
                if config['disambiguation']:
                    disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + phrase)
            break
except KeyboardInterrupt:
    print(f'{R}\nZakończono')  # R musi tu być, aby kolory z "inputtext" nie wchodziły
