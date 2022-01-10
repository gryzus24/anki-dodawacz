#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile

import urllib3
from urllib3.exceptions import NewConnectionError, ConnectTimeoutError

from src.__version__ import __version__
from src.colors import R, GEX, YEX, err_c
from src.data import config, ROOT_DIR, USER_AGENT, WINDOWS, LINUX, ON_WINDOWS_CMD


class Exit(Exception):
    def __init__(self, err_msg):
        print(f'{err_c}{err_msg}')
        # Sleep to prevent terminal window from closing instantaneously
        # when running the script by double clicking the file on Windows
        if ON_WINDOWS_CMD:
            import time
            time.sleep(2)
        raise SystemExit(1)


def get_request():
    def wrapper(url, **kwargs):
        try:
            http = urllib3.PoolManager(num_pools=1, timeout=10, headers=USER_AGENT)
            response = http.urlopen('GET', url, **kwargs)
        except Exception as e:
            if isinstance(e.__context__, NewConnectionError):
                raise Exit('Could not establish a connection,\n'
                           'check your Internet connection and try again.')
            elif isinstance(e.__context__, ConnectTimeoutError):
                raise Exit('Github is not responding')
            else:
                print(f'{err_c}An unexpected error occurred.')
                raise
        else:
            if response.status != 200:
                raise Exit('Could not retrieve the package.\n'
                           'Non 200 status code.')
            return response

    return wrapper


def main():
    safe_get = get_request()
    response = safe_get('https://api.github.com/repos/gryzus24/anki-dodawacz/tags')

    latest_tag = json.loads(response.data.decode())[0]
    if latest_tag['name'] == __version__:
        print(f'{GEX}You are using the latest version ({__version__}).')
        return 0

    out_dir_name = f'anki-dodawacz-{latest_tag["name"]}'
    out_dir_path = os.path.join(os.path.dirname(ROOT_DIR), out_dir_name)
    if os.path.exists(out_dir_path):
        raise Exit(f'Directory {out_dir_name!r} already exists.\n'
                   f'Aborting the installation...')

    if LINUX or WINDOWS:
        new_release_url = latest_tag['tarball_url']
    else:
        # There are too much os calls in this script. I'm not sure if it works on macOS.
        raise Exit(f'update.py script does not work on {sys.platform!r}.\n')

    print(f'{GEX}:: {R}Downloading the package...')
    archive = safe_get(new_release_url)

    print(f'{GEX}:: {R}Extracting...')
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
            raise Exit('Could not extract archive.')
    finally:
        os.remove(tfile.name)

    print(f"{YEX}:: {R}Copying 'config.json'...")
    with open(os.path.join(out_dir_path, 'config/config.json'), 'r') as f:
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
                print(f"{err_c}:: {R}Could not copy '{old_key}': incompatible data type")

    with open(os.path.join(out_dir_path, 'config/config.json'), 'w') as f:
        json.dump(new_config, f, indent=0)

    if os.path.exists('cards.txt'):
        print(f"{YEX}:: {R}Copying 'cards.txt'...")
        with \
                open(os.path.join(out_dir_path, 'cards.txt'), 'w', encoding='utf-8') as new_cards, \
                open('cards.txt', 'r', encoding='utf-8') as cards:
            new_cards.writelines(cards.readlines())

    if not config['ankiconnect'] and config['audio_path'] == 'Cards_audio' and os.path.exists('Cards_audio'):
        print(f"{YEX}:: {R}The 'Cards_audio' directory has to be moved manually.")

    print(f'\n{GEX}Updated successfully\n'
          f'Program saved to {out_dir_path!r}')


if __name__ == '__main__':
    try:
        e = main()
        if ON_WINDOWS_CMD:
            import time
            time.sleep(2)
        raise SystemExit(e)
    except (KeyboardInterrupt, EOFError):
        print()
        raise SystemExit
