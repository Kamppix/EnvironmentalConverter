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
        name = re.sub(r'[^a-z0-9/._-]', '', name)
        return name

    def from_files(sources, target):
        NewThread(target = MusicPack.create_from_files, args = (sources, target))

    def from_youtube(url, target):
        NewThread(target = youtube.create_pack, args = (url, target))

    def from_terraria(source, target):
        NewThread(target = MusicPack.create_from_terraria, args = (source, target))
    
    def create_from_files(sources: list[str], target):
        sounds_folder, sounds_target = MusicPack.init_target(target, False)
        
        Logger.log('Creating music pack...')
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

        pack_png = os.path.join(os.path.dirname(sources[0]), 'pack.png')
        if os.path.exists(pack_png) and os.path.isfile(pack_png):
            shutil.copy(pack_png, os.path.join(target, 'pack.png'))
            Logger.log('Copied "pack.png"')
                    
        Logger.log('Music pack creation successful!')
    
    def create_from_terraria(source, target):
        sounds_folder, sounds_target = MusicPack.init_target(target, True)
        
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
    
    def init_target(target, is_terraria):
        sounds_folder = os.path.join(target, 'assets', 'environmentalmusic', 'sounds')
        if not os.path.exists(sounds_folder):
            os.makedirs(sounds_folder)

        Logger.log('Copying template files...')
        # Copy files from music pack template
        template_source = os.path.join(os.getcwd(), 'music_packs', 'template')
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
