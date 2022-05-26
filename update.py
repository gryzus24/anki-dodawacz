#!/usr/bin/env python3

from __future__ import annotations

import contextlib
from typing import Generator

import urllib3
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError

from src.__version__ import __version__
from src.colors import Color, R
from src.data import LINUX, ON_WINDOWS_CMD, ROOT_DIR, USER_AGENT, WINDOWS, config

http = urllib3.PoolManager(timeout=10, headers=USER_AGENT)


@contextlib.contextmanager
def _exit(rc: int) -> Generator[None, None, None]:
    try:
        yield
    finally:
        if ON_WINDOWS_CMD:
            import time
            time.sleep(2)
        raise SystemExit(rc)


def get_request(url: str) -> urllib3.HTTPResponse:
    try:
        response = http.urlopen('GET', url)
    except Exception as e:
        if isinstance(e.__context__, NewConnectionError):
            with _exit(1):
                print(f'{Color.err}Could not establish a connection,\n'
                      f'check your Internet connection and try again.')
        elif isinstance(e.__context__, ConnectTimeoutError):
            with _exit(1):
                print(f'{Color.err}Github is not responding')
        else:
            print(f'{Color.err}An unexpected error occurred.')
        raise
    else:
        if response.status != 200:
            with _exit(1):
                print(f'{Color.err}Could not retrieve the package.\n'
                      f'Non 200 status code.')
        return response


def main() -> None:
    import json
    import os
    import subprocess
    import sys
    import tempfile

    response_data = get_request('https://api.github.com/repos/gryzus24/anki-dodawacz/tags')

    latest_tag = json.loads(response_data.data.decode())[0]
    if latest_tag['name'].lstrip('v') == __version__:
        with _exit(0):
            print(f'{Color.GEX}You are using the latest version ({__version__}).')

    out_dir_name = f'anki-dodawacz-{latest_tag["name"]}'
    out_dir_path = os.path.join(os.path.dirname(ROOT_DIR), out_dir_name)
    if os.path.exists(out_dir_path):
        with _exit(1):
            print(f'{Color.err}Directory {out_dir_name!r} already exists.\nExiting...')

    if not LINUX and not WINDOWS:
        # There are too much os calls in this script. I'm not sure if it works on macOS.
        with _exit(1):
            print(f'{Color.err}update.py script does not work on {sys.platform!r}.\n')

    print(f'{Color.GEX}:: {R}Downloading the package...')
    archive = get_request(latest_tag['tarball_url'])

    print(f'{Color.GEX}:: {R}Extracting...')
    tfile = tempfile.NamedTemporaryFile(delete=False)
    try:
        # We cannot use the NamedTemporaryFile as a context manager because Windows
        # is unable to open the temporary file in the subprocess.
        tfile.write(archive.data)
        tfile.flush()
        tfile.close()
        os.mkdir(out_dir_path)
        process = subprocess.run(
            ['tar', '-xf', tfile.name, '--strip-components=1', '-C', out_dir_path]
        )
        if process.returncode != 0:
            try:
                os.rmdir(out_dir_path)
            except OSError:  # In case tar gets interrupted,
                pass         # otherwise the directory should be empty.
            with _exit(1):
                print(f'{Color.err}Could not extract archive.')
    finally:
        os.remove(tfile.name)

    print(f"{Color.YEX}:: {R}Copying 'config.json'...")
    with open(os.path.join(out_dir_path, 'config/config.json')) as f:
        new_config = json.load(f)
        for old_key, old_val in config.items():
            try:
                new_val = new_config[old_key]
            except KeyError:
                continue
            # To prevent new versions from reading old config data types.
            if isinstance(new_val, type(old_val)):
                new_config[old_key] = old_val
            else:
                print(f"{Color.err}:: {R}Could not copy '{old_key}': incompatible data type")

    with open(os.path.join(out_dir_path, 'config/config.json'), 'w') as f:
        json.dump(new_config, f, indent=0)

    if os.path.exists('cards.txt'):
        print(f"{Color.YEX}:: {R}Copying 'cards.txt'...")
        with \
                open(os.path.join(out_dir_path, 'cards.txt'), 'w', encoding='utf-8') as new_cards, \
                open('cards.txt', encoding='utf-8') as cards:
            new_cards.writelines(cards.readlines())

    if not config['-ankiconnect'] and config['audio_path'] == 'Cards_audio' and os.path.exists('Cards_audio'):
        print(f"{Color.YEX}:: {R}The 'Cards_audio' directory has to be moved manually.")

    with _exit(0):
        print(f'\n{Color.GEX}Updated successfully\n'
              f'Program saved to {out_dir_path!r}')


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
