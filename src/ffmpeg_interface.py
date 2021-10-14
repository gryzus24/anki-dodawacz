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

import datetime
import os.path
import subprocess
import sys

from src.colors import R, YEX, GEX, index_c, err_c
from src.commands import save_command
from src.data import config

if sys.platform.startswith('win'):
    def find_devices() -> list:
        audio_devices = subprocess.run('ffmpeg -hide_banner -list_devices true -f dshow -i dummy',
                                       shell=True, capture_output=True, text=True)
        # not sure whether list_devices can come out as stdout, it's always a stderr
        if not audio_devices.stdout:
            audio_devices = audio_devices.stderr.splitlines()[:-1]
        else:
            audio_devices = audio_devices.stdout.splitlines()[:-1]

        audio_devices = [x.split(']')[-1].strip() for x in audio_devices]
        audio_devices = [x for x in audio_devices if '"' in x and '@' not in x]
        audio_devices.insert(0, 'default')
        return audio_devices

elif sys.platform.startswith('linux'):
    def find_devices() -> list:
        audio_devices = subprocess.run('pactl list sources | grep alsa_output',
                                       shell=True, capture_output=True, text=True)
        audio_devices = audio_devices.stdout.splitlines()[:-1]
        audio_devices = [x.split(':')[-1].strip()
                         for x in audio_devices if x.endswith('monitor')]
        audio_devices.insert(0, 'default')
        return audio_devices

else:
    def find_devices() -> None:
        return None


def record(filepath: str):
    if sys.platform.startswith('linux'):
        ffmpeg_settings = {
            'format': 'pulse',
            'device': config['audio_device']
        }
    elif sys.platform.startswith('win'):
        ffmpeg_settings = {
            'format': 'dshow',
            'device': f"audio={config['audio_device']}"
        }
    else:
        raise NameError  # os not supported

    print(f'{YEX.color}Rozpoczęto nagrywanie...\n'
          f'{R}wciśnij [q], aby zakończyć i zapisać')
    result = subprocess.run((
        'ffmpeg',
        '-hide_banner',
        '-loglevel', 'warning',
        '-use_wallclock_as_timestamps', '1',
        '-fflags', '+igndts',
        '-f', ffmpeg_settings['format'],
        '-channel_layout', 'stereo',
        '-i', ffmpeg_settings['device'],
        '-acodec', 'libmp3lame',
        '-q:a', config['recqual'],
        filepath
    ), capture_output=True, text=True)
    return result


def set_audio_device():
    try:
        audio_devices = find_devices()
        if audio_devices is None:
            return 'Nagrywanie audio niedostępne na obecnym systemie operacyjnym'
    except FileNotFoundError:
        return 'Ffmpeg nie został odnaleziony\n' \
               'Umieść ffmpeg w folderze z programem lub $PATH'

    print('Wybierz urządzenie do przechwytywania audio poprzez ffmpeg:\n')
    for index, a in enumerate(audio_devices, start=1):
        print(f"{index_c.color}{index} {R}{a}")

    choice = input('Wybierz urządzenie [1]: ').strip()
    if not choice:
        choice = 1
    else:
        try:
            choice = int(choice)
            if choice < 1 or choice > len(audio_devices):
                raise ValueError
        except ValueError:
            return 'Nieprawidłowa wartość, opuszczam konfigurację'

    audio_device = audio_devices[choice - 1]
    save_command('audio_device', audio_device)
    print(f'{GEX.color}Urządzenie przechwytujące audio ustawiono:\n'
          f'{R}{audio_device}\n')


def capture_audio(*args) -> str:
    try:
        arg = args[0].lower()
    except IndexError:  # no arguments
        metadata = '_'
    else:
        metadata = '_' + arg.strip('_- ').replace('.', '_').replace("'", "").replace('"', '')

    date = str(datetime.date.today()).replace('-', '_')
    savedir = config['audio_path']
    recording_no = 0
    filepath = os.path.join(savedir, f"{date}_sentence{metadata}{recording_no}.mp3")
    # e.g. filename: 2021_8_12_sentence_0.mp3
    # with metadata: 2021_8_12_sentence_tower_0.mp3

    while os.path.exists(filepath):
        recording_no += 1
        filepath = os.path.join(savedir, f"{date}_sentence{metadata}{recording_no}.mp3")

    try:
        result = record(filepath)
    except NameError:  # if os is not linux or win
        print(f'{err_c.color}Nagrywanie audio niedostępne na obecnym systemie operacyjnym')
        return ''
    except FileNotFoundError:
        print(f'{err_c.color}Ffmpeg nie został odnaleziony\n'
              f'Umieść ffmpeg w folderze z programem lub $PATH')
        return ''

    if 'Output file is empty' in result.stderr:
        print(f'{err_c.color}Nagrywanie nie powiodło się: pusty plik wyjściowy\n'
              f'Spróbuj nagrać dłuższy odcinek')
        subprocess.run(('rm', filepath))
        return ''
    elif 'Queue input is backward in time' in result.stderr:
        pass
    elif result.stderr or result.returncode == 1:
        print(f'{err_c.color}Nagrywanie nie powiodło się:')
        print(result.stderr)
        return ''

    print(f'{GEX.color}Nagranie pomyślnie zapisane jako:\n'
          f'{R}{filepath}')
    return f"[sound:{date}_sentence{metadata}{recording_no}.mp3]"