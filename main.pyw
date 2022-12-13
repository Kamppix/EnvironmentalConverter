'''
Main module for Pixel Music Packer.
'''

import os
import sys
from time import sleep
import datetime
import re
import shutil
import json
from urllib.error import URLError
from threading import Thread
import ffmpeg
from pytube.contrib.playlist import Playlist
from pydub.silence import detect_leading_silence
from pydub import AudioSegment
import window


def log(line):
    '''
    Print a line with a timestamp to the console and the window log box.
    '''
    line = '[' + str(datetime.datetime.now().strftime("%H:%M:%S")) + ']: ' + line
    print(line)

    app = window.Application.instance()
    if app is not None:
        app.log(line)


def start_thread(target = None, args = ()):
    '''
    Run a function in a separate thread.
    '''
    thread = Thread(target = target, args = args)
    thread.start()
    return thread


def convert_filename(name):
    '''
    Convert a filename into something a Minecraft resource pack can use.
    '''
    name = name.strip().lower().replace('-', '_').replace(' ', '_')
    while '__' in name:
        name = name.replace('__', '_')
    name = re.sub(r'[^a-z0-9/._-]', '', name)
    while name[:-4].endswith('.'):
        name = name[:-5] + name[-4:]
    return name

def from_files(sources, target):
    '''
    Start a new thread for creating a music pack from local files.
    '''
    start_thread(create_from_files, (sources, target))

def from_youtube(playlist, selected, target):
    '''
    Start a new thread for creating a music pack from local files.
    '''
    start_thread(create_from_youtube, (playlist, selected, target))

def from_terraria(source, target):
    '''
    Start a new thread for creating a music pack from local files.
    '''
    start_thread(create_from_terraria, (source, target))

def create_from_files(sources, target):
    '''
    Create a music pack from local files.
    '''
    sounds_folder, sounds_target = init_target(target, False)

    # Copy pack icon
    pack_png = os.path.join(os.path.dirname(sources[0]), 'pack.png')
    if os.path.exists(pack_png) and os.path.isfile(pack_png):
        shutil.copy(pack_png, os.path.join(target, 'pack.png'))
        log('Copied "pack.png".')

    # Copy music
    with open(sounds_target, 'r+') as sounds_file:
        sounds_data = json.load(sounds_file)
        key_list = list(sounds_data.keys())
        for i,file_path in enumerate(sources):
            if file_path.endswith('--'):
                sounds_data.pop(key_list[i])
                continue

            filename = convert_filename(os.path.basename(os.path.normpath(file_path)))
            name = filename[:-4]
            sounds_data[key_list[i]]['sounds'][0]['name'] = 'environmentalmusic:' + name
            target_file = os.path.join(sounds_folder, name + '.ogg')

            if filename.endswith('.mp3') or filename.endswith('.wav'):
                # Convert to OGG
                log('Converting "' + filename + '" to OGG...')
                (
                    ffmpeg.input(file_path)
                    .output(target_file)
                    .run(quiet=True, overwrite_output=True,
                         cmd=os.path.join(os.getcwd(), 'ffmpeg.exe'))
                )
            else:
                # Copy file
                shutil.copy(file_path, target_file)
                log('Copied "' + filename + '".')
                continue

        log('Writing sounds.json...')
        sounds_file.seek(0)
        json.dump(sounds_data, sounds_file, indent = 2)
        sounds_file.truncate()

    log('Music pack creation successful!')


def create_from_youtube(playlist, selected, target):
    '''
    Create a music pack from a YouTube playlist.
    '''
    log('Creating music pack from playlist...')

    sounds_folder, sounds_target = init_target(target, False)

    filenames = download_videos(playlist, selected, sounds_folder)

    with open(sounds_target, 'r+') as sounds_file:
        log('Writing sounds.json...')
        sounds_data = json.load(sounds_file)
        key_list = list(sounds_data.keys())
        for i,name in enumerate(filenames):
            if name is None:
                sounds_data.pop(key_list[i])
                continue
            sounds_data[key_list[i]]['sounds'][0]['name'] = 'environmentalmusic:' + name

        sounds_file.seek(0)
        json.dump(sounds_data, sounds_file, indent = 2)
        sounds_file.truncate()

    log('Music pack creation successful!')


def create_from_terraria(source, target):
    '''
    Create a music pack from a Terraria music pack.
    '''
    log('Converting Terraria music pack...')
    sounds_folder, sounds_target = init_target(target, True)

    # Copy pack icon
    icon_source = os.path.join(source, 'icon.png')
    if os.path.exists(icon_source):
        icon_target = os.path.join(target, 'pack.png')
        shutil.copy(icon_source, icon_target)
        log('Copied pack icon.')

    # Copy music
    music_source = os.path.join(source, 'Content', 'Music')
    with open(sounds_target, 'r') as sounds_file:
        sounds_data = json.load(sounds_file)
        for _, event in sounds_data.items():
            for sound in event['sounds']:
                music_name = sound['name'][19:]
                filename = os.path.join(music_source, music_name)
                if os.path.exists(filename + '.mp3'):
                    file_path = filename + '.mp3'
                    log('Converting "' + music_name + '.mp3" to OGG...')
                elif os.path.exists(filename + '.wav'):
                    file_path = filename + '.wav'
                    log('Converting "' + music_name + '.wav" to OGG...')
                elif os.path.exists(filename + '.ogg'):
                    file_path = filename + '.ogg'
                    shutil.copy(file_path, sounds_folder)
                    log('Copied "' + music_name + '.ogg"')
                    continue
                else:
                    continue

                # Convert to OGG
                (
                    ffmpeg.input(file_path)
                    .output(os.path.join(sounds_folder, music_name + '.ogg'))
                    .run(quiet=True, overwrite_output=True,
                         cmd=os.path.join(os.getcwd(), 'ffmpeg.exe'))
                )

    log('Music pack conversion successful!')

def init_target(target, is_terraria):
    '''
    Create target directory and copy template files inside it.
    '''
    sounds_folder = os.path.join(target, 'assets', 'environmentalmusic', 'sounds')
    if not os.path.exists(sounds_folder):
        os.makedirs(sounds_folder)

    log('Copying template files...')
    # Copy files from music pack template
    template_source = os.path.join(os.getcwd(), 'template_pack')
    pack_source = os.path.join(template_source, 'pack.mcmeta')
    if is_terraria:
        sounds_source = os.path.join(template_source, 'assets',
                                     'environmentalmusic', 'sounds_terraria.json')
    else:
        sounds_source = os.path.join(template_source, 'assets',
                                     'environmentalmusic', 'sounds.json')

    pack_target = os.path.join(target, 'pack.mcmeta')
    sounds_target = os.path.join(target, 'assets', 'environmentalmusic', 'sounds.json')

    shutil.copy(pack_source, pack_target)
    shutil.copy(sounds_source, sounds_target)

    return sounds_folder, sounds_target


def download_videos(playlist: Playlist, selected, sounds_folder):
    '''
    Download videos from given Playlist object and
    convert them into OGG files in a resource pack.
    '''
    log('Getting videos from playlist "' + playlist.title + '"...')

    videos = playlist.videos
    filenames = {}

    for i,video in enumerate(videos):
        if i in selected:
            title = video.title
            name = convert_filename(title) + '.ogg'

            for j,num in enumerate(selected):
                if num == i:
                    filenames[j] = name[:-4]
                elif num == -1:
                    filenames[j] = None

            if os.path.exists(os.path.join(sounds_folder, name)):
                log('"' + name + '" already exists')
                continue

            while True:
                try:
                    # Extract only audio
                    video = video.streams.filter(only_audio=True).first()
                    # Download file
                    log('Downloading "' + title + '"...')
                    temp_mp4 = video.download(output_path = sounds_folder)
                    break
                except (ConnectionResetError, URLError):
                    log('Connection to YouTube lost. Trying again in 3 seconds...')
                    sleep(3)

            base, _ = os.path.splitext(temp_mp4)
            temp_ogg = base + '.ogg'

            # Convert to .ogg
            log('Converting to OGG...')
            (
                ffmpeg.input(temp_mp4)
                .output(temp_ogg)
                .run(quiet=True, overwrite_output=True, cmd=os.path.join(os.getcwd(), 'ffmpeg.exe'))
            )

            # Strip silence
            log('Stripping silence...')
            sound = strip_silence(AudioSegment.from_file(temp_ogg))

            # Export
            path = os.path.join(sounds_folder, name)
            sound.export(path, format='ogg')
            log('Exported to "' + path + '"')

            # Delete temporary files
            os.remove(temp_mp4)
            os.remove(temp_ogg)

    log('Playlist downloaded')
    return filenames


def strip_silence(sound: AudioSegment):
    '''
    Strip out the silence from the start and end of an `AudioSegment`.
    '''
    sound = sound[detect_leading_silence(sound):].reverse()
    sound = sound[detect_leading_silence(sound):].reverse()
    return sound


def main():
    '''
    Main function of the program.
    '''
    log('Program started.')
    if sys.platform == 'win32':
        window.Application()
    else:
        log('Unsupported OS detected!')
    log('Exiting program...')


if __name__ == "__main__":
    main()
