import os, time, shutil, ffmpeg
from urllib.error import URLError
from pytube.contrib.playlist import Playlist
from pydub.silence import detect_leading_silence
from pydub import AudioSegment
from main import Logger, MusicPack
from time import sleep


TERRARIA_URL = 'https://youtube.com/playlist?list=PLmEInNWnJt01A24SN36oWl4OufV4L6Oex'


def create_pack(url, target):
    playlist = Playlist(url)
    try:
        title = playlist.title
    except KeyError:
        Logger.log('Invalid playlist URL')
        return

    Logger.log('Creating music pack from URL...')
    
    is_terraria = False
    if playlist == Playlist(TERRARIA_URL):
        is_terraria = True

    target_path = os.path.join(target, title)
    sounds_folder = os.path.join(target_path, 'assets', 'environmentalmusic', 'sounds')
    if not os.path.exists(sounds_folder):
        os.makedirs(sounds_folder)

    Logger.log('Copying template files...')
    if is_terraria:
        source = os.path.join(os.getcwd(), 'music_packs', 'Terraria Music Pack')
    else:
        source = os.path.join(os.getcwd(), 'music_packs', 'template')

    pack_source = os.path.join(source, 'pack.mcmeta')
    sounds_source = os.path.join(source, 'assets', 'environmentalmusic', 'sounds.json')

    pack_target = os.path.join(target_path, 'pack.mcmeta')
    sounds_target = os.path.join(target_path, 'assets', 'environmentalmusic', 'sounds.json')

    shutil.copy(pack_source, pack_target)
    shutil.copy(sounds_source, sounds_target)

    while True:
        try:
            get_videos(playlist, target)
            break
        except (ConnectionResetError, URLError) as e:
            Logger.log('Connection to YouTube reset.\nTrying again in 5 seconds...')
            time.sleep(5)

    Logger.log('Music pack creation successful!')


def get_videos(playlist: Playlist, target):
    '''Download videos from given Playlist object and convert them into OGG files in a resource pack.'''

    Logger.log('Getting videos from playlist "' + playlist.title + '"...')
    sounds_path = os.path.join(target, playlist.title, 'assets', 'environmentalmusic', 'sounds')

    videos = playlist.videos

    for video in videos:
        title = video.title
        name = MusicPack.convert_filename(title)

        if os.path.exists(os.path.join(sounds_path, name)):
            Logger.log('"' + name + '" already exists')
            continue

        # Extract only audio
        Logger.log('Downloading "' + title + '"...')
        video = video.streams.filter(only_audio=True).first()

        # Download file
        temp_mp4 = video.download(output_path = sounds_path)

        base, ext = os.path.splitext(temp_mp4)
        temp_ogg = base + '.ogg'
        
        # Convert to .ogg
        Logger.log('Converting to OGG...')
        (
            ffmpeg.input(temp_mp4)
            .output(temp_ogg)
            .run(quiet=True, overwrite_output=True, cmd=os.path.join(os.getcwd(), 'ffmpeg.exe'))
        )

        # Strip silence
        Logger.log('Stripping silence...')
        trim_leading_silence: AudioSegment = lambda x: x[detect_leading_silence(x) :]
        trim_trailing_silence: AudioSegment = lambda x: trim_leading_silence(x.reverse()).reverse()
        strip_silence: AudioSegment = lambda x: trim_trailing_silence(trim_leading_silence(x))

        sound = AudioSegment.from_file(temp_ogg)
        stripped = strip_silence(sound)
        # stripped.apply_gain_stereo(-4)
        path = os.path.join(sounds_path, name)
        stripped.export(path, format='ogg')
        Logger.log('Exported to "' + path + '"')

        # Delete temporary files
        os.remove(temp_mp4)
        os.remove(temp_ogg)

    Logger.log('Playlist downloaded')
