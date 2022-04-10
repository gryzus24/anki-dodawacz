# Copyright 2021-2022 Gryzus
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

from __future__ import annotations

import datetime
import os
import subprocess
import sys

from src.colors import R, Color
from src.commands import save_command
from src.data import LINUX, WINDOWS, config
from src.input_fields import choose_item

if WINDOWS:
    def find_devices() -> list[str]:
        process = subprocess.run('ffmpeg -hide_banner -list_devices true -f dshow -i dummy',
                                 shell=True, capture_output=True, text=True)
        # not sure whether list_devices can come out as stdout, it's always a stderr
        if not process.stdout:
            audio_devices = process.stderr.splitlines()[:-1]
        else:
            audio_devices = process.stdout.splitlines()[:-1]

        audio_devices = [x.split(']')[-1].strip() for x in audio_devices]
        audio_devices = [x for x in audio_devices if '"' in x and '@' not in x]
        audio_devices.insert(0, 'default')
        return audio_devices

elif LINUX:
    def find_devices() -> list[str]:
        process = subprocess.run('pactl list sources | grep alsa_output',
                                 shell=True, capture_output=True, text=True)
        audio_devices = process.stdout.splitlines()[:-1]
        audio_devices = [x.split(':')[-1].strip()
                         for x in audio_devices if x.endswith('monitor')]
        audio_devices.insert(0, 'default')
        return audio_devices

else:
    def find_devices() -> list[str]:
        return []


def record(filepath: str) -> subprocess.CompletedProcess:
    if LINUX:
        ffmpeg_settings = {
            'format': 'pulse',
            'device': config['audio_device']
        }
    elif WINDOWS:
        ffmpeg_settings = {
            'format': 'dshow',
            'device': f"audio={config['audio_device']}"
        }
    else:
        raise NameError  # os not supported

    print(f'{Color.YEX}Recording started...\n'
          f'{R}press [q] to stop and save')
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


def set_audio_device() -> str | None:
    try:
        audio_devices = find_devices()
        if not audio_devices:
            return f'No devices found\n' \
                   f'audio recording might not be available on {sys.platform!r}'
    except FileNotFoundError:
        return 'Could not locate FFmpeg\n' \
               "Place the FFmpeg binary alongside the program or in $PATH"

    print('Choose your desktop output device:')
    for i, device in enumerate(audio_devices, start=1):
        print(f"{Color.index}{i} {R}{device}")

    audio_device = choose_item('\nDevice', audio_devices)
    if audio_device is None:
        return 'Invalid input, leaving...'

    save_command('audio_device', audio_device)
    print(f'{Color.GEX}Chosen device:\n'
          f'{R}{audio_device}\n')
    return None


def capture_audio(*args: str) -> str:
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
        print(f'{Color.err}Audio recording is not available on {sys.platform!r}')
        return ''
    except FileNotFoundError:
        print(f'{Color.err}Could not locate FFmpeg\n'
              "Place the FFmpeg binary alongside the program or in $PATH")
        return ''

    if 'Output file is empty' in result.stderr:
        print(f'{Color.err}Recording failed: empty output file\n'
              'Try recording a longer excerpt')
        subprocess.run(('rm', filepath))
        return ''
    elif 'Queue input is backward in time' in result.stderr:
        pass
    elif result.stderr or result.returncode == 1:
        print(f'{Color.err}Recording failed:')
        print(result.stderr)
        return ''

    print(f'{Color.GEX}Recorded successfully:\n'
          f'{R}{filepath}')
    return f"[sound:{date}_sentence{metadata}{recording_no}.mp3]"
