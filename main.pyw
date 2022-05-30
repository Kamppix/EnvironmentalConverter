import os, datetime, re, shutil, json, ffmpeg
from time import sleep
from urllib.error import URLError
from pytube.contrib.playlist import Playlist
from pydub.silence import detect_leading_silence
from pydub import AudioSegment
from sys import platform
from threading import Thread
import window


class Logger:
    def log(line):
        '''Print a line with a timestamp to the console and the window log box.'''

        line = '[' + str(datetime.datetime.now().strftime("%H:%M:%S")) + ']: ' + line
        print(line)
        
        app = window.Application.instance()
        if app is not None:
            app.log(line)


class NewThread(Thread):
    def __init__(self, target = None, args = ()):
        super().__init__(target = target, args = args)
        self.start()


class MusicPack:
    def convert_filename(name):
        name = name.strip().lower().replace('-', '_').replace(' ', '_')
        while '__' in name:
            name = name.replace('__', '_')
        name = re.sub(r'[^a-z0-9/._-]', '', name)
        return name

    def from_files(sources, target):
        NewThread(target = MusicPack.create_from_files, args = (sources, target))

    def from_youtube(playlist, selected, target):
        NewThread(target = Youtube.create_pack, args = (playlist, selected, target))

    def from_terraria(source, target):
        NewThread(target = MusicPack.create_from_terraria, args = (source, target))
    
    def create_from_files(sources, target):
        sounds_folder, sounds_target = MusicPack.init_target(target, False)

        # Copy pack icon
        pack_png = os.path.join(os.path.dirname(sources[0]), 'pack.png')
        if os.path.exists(pack_png) and os.path.isfile(pack_png):
            shutil.copy(pack_png, os.path.join(target, 'pack.png'))
            Logger.log('Copied "pack.png"')
        
        # Copy music
        with open(sounds_target, 'r+') as sounds_file:
            sounds_data = json.load(sounds_file)
            key_list = list(sounds_data.keys())
            for i in range(len(sources)):
                file_path = sources[i]
                if file_path.endswith('--'):
                    sounds_data.pop(key_list[i])
                    continue

                filename = MusicPack.convert_filename(os.path.basename(os.path.normpath(file_path)))
                name = filename[:-4]
                sounds_data[key_list[i]]['sounds'][0]['name'] = 'environmentalmusic:' + name
                target_file = os.path.join(sounds_folder, name + '.ogg')
                   
                if filename.endswith('.mp3') or filename.endswith('.wav'):
                    # Convert to OGG
                    Logger.log('Converting "' + filename + '" to OGG...')
                    (
                        ffmpeg.input(file_path)
                        .output(target_file)
                        .run(quiet=True, overwrite_output=True, cmd=os.path.join(os.getcwd(), 'ffmpeg.exe'))
                    )
                else:
                    # Copy file
                    shutil.copy(file_path, target_file)
                    Logger.log('Copied "' + filename + '"')
                    continue

            Logger.log('Writing sounds.json...')
            sounds_file.seek(0)
            json.dump(sounds_data, sounds_file, indent = 2)
            sounds_file.truncate()
                    
        Logger.log('Music pack creation successful!')
    
    def create_from_terraria(source, target):
        Logger.log('Converting Terraria music pack...')
        sounds_folder, sounds_target = MusicPack.init_target(target, True)
        
        # Copy pack icon
        icon_source = os.path.join(source, 'icon.png')
        if os.path.exists(icon_source):
            icon_target = os.path.join(target, 'pack.png')
            shutil.copy(icon_source, icon_target)
            Logger.log('Copied pack icon')

        # Copy music
        music_source = os.path.join(source, 'Content', 'Music')
        with open(sounds_target) as sounds_file:
            sounds_data = json.load(sounds_file)
            for _, event in sounds_data.items():
                for sound in event['sounds']:
                    music_name = sound['name'][19:]
                    filename = os.path.join(music_source, music_name)
                    if os.path.exists(filename + '.mp3'):
                        file_path = filename + '.mp3'
                        Logger.log('Converting "' + music_name + '.mp3" to OGG...')
                    elif os.path.exists(filename + '.wav'):
                        file_path = filename + '.wav'
                        Logger.log('Converting "' + music_name + '.wav" to OGG...')
                    elif os.path.exists(filename + '.ogg'):
                        file_path = filename + '.ogg'
                        shutil.copy(file_path, sounds_folder)
                        Logger.log('Copied "' + music_name + '.ogg"')
                        continue
                    else:
                        continue
                    
                    # Convert to OGG
                    (
                        ffmpeg.input(file_path)
                        .output(os.path.join(sounds_folder, music_name + '.ogg'))
                        .run(quiet=True, overwrite_output=True, cmd=os.path.join(os.getcwd(), 'ffmpeg.exe'))
                    )
                    
        Logger.log('Music pack conversion successful!')
    
    def init_target(target, is_terraria):
        sounds_folder = os.path.join(target, 'assets', 'environmentalmusic', 'sounds')
        if not os.path.exists(sounds_folder):
            os.makedirs(sounds_folder)

        Logger.log('Copying template files...')
        # Copy files from music pack template
        template_source = os.path.join(os.getcwd(), 'template')
        pack_source = os.path.join(template_source, 'pack.mcmeta')
        if is_terraria:
            sounds_source = os.path.join(template_source, 'assets', 'environmentalmusic', 'sounds_terraria.json')
        else:
            sounds_source = os.path.join(template_source, 'assets', 'environmentalmusic', 'sounds.json')

        pack_target = os.path.join(target, 'pack.mcmeta')
        sounds_target = os.path.join(target, 'assets', 'environmentalmusic', 'sounds.json')

        shutil.copy(pack_source, pack_target)
        shutil.copy(sounds_source, sounds_target)
    
        return sounds_folder, sounds_target
        

class Youtube():
    def create_pack(playlist, selected, target):
        Logger.log('Creating music pack from playlist...')

        sounds_folder, sounds_target = MusicPack.init_target(target, False)

        filenames = Youtube.get_videos(playlist, selected, sounds_folder)
        
        with open(sounds_target, 'r+') as sounds_file:
            Logger.log('Writing sounds.json...')
            sounds_data = json.load(sounds_file)
            key_list = list(sounds_data.keys())
            for i in range(len(filenames)):
                name = filenames[i]
                if name is None:
                    sounds_data.pop(key_list[i])
                    continue
                sounds_data[key_list[i]]['sounds'][0]['name'] = 'environmentalmusic:' + name

            sounds_file.seek(0)
            json.dump(sounds_data, sounds_file, indent = 2)
            sounds_file.truncate()

        Logger.log('Music pack creation successful!')


    def get_videos(playlist: Playlist, selected, sounds_folder):
        '''Download videos from given Playlist object and convert them into OGG files in a resource pack.'''

        Logger.log('Getting videos from playlist "' + playlist.title + '"...')

        videos = playlist.videos
        filenames = {}

        for i in range(len(videos)):
            if i in selected:
                video = videos[i]
                title = video.title

                name = MusicPack.convert_filename(title) + '.ogg'

                for j in range(len(selected)):
                    if selected[j] == i:
                        filenames[j] = name[:-4]
                    elif selected[j] == -1:
                        filenames[j] = None

                if os.path.exists(os.path.join(sounds_folder, name)):
                    Logger.log('"' + name + '" already exists')
                    continue

                while True:
                    try:
                        # Extract only audio
                        video = video.streams.filter(only_audio=True).first()
                        # Download file
                        Logger.log('Downloading "' + title + '"...')
                        temp_mp4 = video.download(output_path = sounds_folder)
                        break
                    except (ConnectionResetError, URLError) as e:
                        Logger.log('Connection to YouTube lost. Trying again in 3 seconds...')
                        sleep(3)

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
                path = os.path.join(sounds_folder, name)
                stripped.export(path, format='ogg')
                Logger.log('Exported to "' + path + '"')

                # Delete temporary files
                os.remove(temp_mp4)
                os.remove(temp_ogg)

        Logger.log('Playlist downloaded')
        return filenames


def main():
    Logger.log('Program started')
    #youtube.create_pack('https://youtube.com/playlist?list=PLmEInNWnJt01tuqpoOseR77UWqhcP1vrY', 'E:\Programming\Python\EnvironmentalCreator\output')
    if not platform.startswith('win32' or 'linux' or 'darwin'):
        Logger.log('Unsupported OS (' + platform + ') detected! Exiting program...')
        exit()

    window.Application(Logger, MusicPack)
    Logger.log('Exiting program...')


if __name__ == "__main__":
    main()
