#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile

import requests
from requests.exceptions import ConnectionError as RqConnectionError
from requests.exceptions import Timeout

from ankidodawacz import __version__
from ankidodawacz import config, R, GEX, YEX, err_c
from src.data import ROOT_DIR, WINDOWS, LINUX


class Exit(Exception):
    def __init__(self, err_msg):
        print(f'{err_c.color}{err_msg}')
        # Sleep to prevent terminal window from closing instantaneously
        # when running the script by double clicking the file on Windows
        if WINDOWS:
            import time
            time.sleep(2)
        raise SystemExit(1)


def get_request(session):
    def wrapper(url, **kwargs):
        try:
            response = session.get(url, **kwargs)
        except Timeout:
            raise Exit('Github nie odpowiada.')
        except RqConnectionError:
            raise Exit('Połączenie z serwerem zostało zerwane.')
        except ConnectionError:
            raise Exit('Nie udało się połączyć z serwerem,\n'
                       'sprawdź swoje połączenie i spróbuj ponownie.')
        except Exception:
            print(f'{err_c.color}Wystąpił nieoczekiwany błąd.')
            raise
        else:
            if response.status_code != 200:
                raise Exit('Nie udało się pozyskać danych z repozytorium.\n'
                           'Przerywam aktualizację...')
            return response

    return wrapper


def main():
    safe_get = get_request(requests.Session())
    response = safe_get('https://api.github.com/repos/gryzus24/anki-dodawacz/tags')

    try:
        latest_tag = response.json()[0]
    except Exception:
        # .json() may raise multiple `DecodeError` type exceptions.
        # [0] may raise IndexError, in either case program should abort.
        raise Exit('Nie udało się pozyskać tagów.\n'
                   'Przerywam aktualizację...')

    if latest_tag['name'] == __version__:
        print(f'{GEX.color}Korzystasz z najnowszej wersji ({__version__}).')
        return 0

    out_dir_name = f'anki-dodawacz-{latest_tag["name"]}'
    out_dir_path = os.path.join(os.path.dirname(ROOT_DIR), out_dir_name)
    if os.path.exists(out_dir_path):
        raise Exit(f'Folder o nazwie {out_dir_name!r} już istnieje.\n'
                   f'Przerywam aktualizację...')

    if LINUX or WINDOWS:
        new_release_url = latest_tag['tarball_url']
    else:
        # There are too much os calls in this script. I'm not sure if it works on macOS.
        raise Exit(f'Automatyczna aktualizacja niedostępna na {sys.platform!r}.')

    print(f'{GEX.color}:: {R}Pobieram archiwum...')
    archive = safe_get(new_release_url)

    print(f'{GEX.color}:: {R}Rozpakowuję...')
    tfile = tempfile.NamedTemporaryFile(delete=False)
    try:
        # We cannot use the NamedTemporaryFile as a context manager because Windows
        # is unable to open the temporary file in the subprocess.
        tfile.write(archive.content)
        tfile.flush()
        tfile.close()
        os.mkdir(out_dir_path)
        process = subprocess.run(
            ['tar', '-xvf', tfile.name, '--strip-components=1', '-C', out_dir_path]
        )
        if process.returncode != 0:
            try:
                os.rmdir(out_dir_path)
            except OSError:  # In case tar gets interrupted,
                pass         # otherwise the directory should be empty.
            raise Exit('Błąd podczas rozpakowywania archiwum.')
    finally:
        os.remove(tfile.name)

    print(f"{GEX.color}:: {R}Przenoszę zawartość 'config.json'...")
    with open(os.path.join(out_dir_path, 'config/config.json'), 'r') as f:
        new_config = json.load(f)
        for key, val in config.items():
            new_config[key] = val
    with open(os.path.join(out_dir_path, 'config/config.json'), 'w') as f:
        json.dump(new_config, f, indent=0)

    if os.path.exists('karty.txt'):
        print(f"{GEX.color}:: {R}Przenoszę zawartość 'karty.txt'...")
        with \
                open(os.path.join(out_dir_path, 'karty.txt'), 'w') as new_cards, \
                open('karty.txt', 'r') as cards:
            new_cards.writelines(cards.readlines())

    if os.path.exists('Karty_audio') and config['audio_path'] == 'Karty_audio':
        print(f"{YEX.color}:: {R}Zawartość folderu 'Karty_audio' musi zostać przeniesiona manualnie.")

    print(f'\n{GEX.color}Aktualizacja zakończona pomyślnie.\n'
          f'Program zapisany w: {out_dir_path!r}')


if __name__ == '__main__':
    try:
        e = main()
        if WINDOWS:
            import time
            time.sleep(2)
        raise SystemExit(e)
    except (KeyboardInterrupt, EOFError):
        print('\nUnicestwiony')
        raise SystemExit
