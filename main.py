import os, datetime, re, shutil, json, ffmpeg, youtube
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
        name = re.sub(r'[^a-z0-9/._-]', '', name) + '.ogg'
        return name

    def from_files(sources, target):
        pass

    def from_youtube(url, target):
        NewThread(target = youtube.create_pack, args = (url, target))

    def from_terraria(source, target):
        shutil.rmtree(target)
        Logger.log('Removed the existing directory and its contents')
        NewThread(target = MusicPack.create_from_terraria, args = (source, target))
    
    def create_from_terraria(source, target):
        sounds_folder = os.path.join(target, 'assets', 'environmentalmusic', 'sounds')
        if not os.path.exists(sounds_folder):
            os.makedirs(sounds_folder)

        Logger.log('Copying template files...')
        # Copy files from music pack template
        template_source = os.path.join(os.getcwd(), 'music_packs', 'template')
        pack_source = os.path.join(template_source, 'pack.mcmeta')
        sounds_source = os.path.join(template_source, 'assets', 'environmentalmusic', 'sounds_terraria.json')

        pack_target = os.path.join(target, 'pack.mcmeta')
        sounds_target = os.path.join(target, 'assets', 'environmentalmusic', 'sounds.json')

        shutil.copy(pack_source, pack_target)
        shutil.copy(sounds_source, sounds_target)
        
        Logger.log('Copying music pack files...')
        # Copy pack icon
        icon_source = os.path.join(source, 'icon.png')
        if os.path.exists(icon_source):
            icon_target = os.path.join(target, 'pack.png')
            shutil.copy(icon_source, icon_target)

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
