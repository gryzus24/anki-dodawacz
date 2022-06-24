from __future__ import annotations

import datetime
import os
import subprocess
import sys

from src.colors import Color, R
from src.data import LINUX, WINDOWS, config

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


def _record(filepath: str) -> subprocess.CompletedProcess[str]:
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

    print(f'{Color.heed}Recording started...\n'
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
        '-q:a', str(config['-recqual']),
        filepath
    ), capture_output=True, text=True)
    return result


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
        result = _record(filepath)
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

    print(f'{Color.success}Recorded successfully:\n'
          f'{R}{filepath}')
    return f"[sound:{date}_sentence{metadata}{recording_no}.mp3]"
