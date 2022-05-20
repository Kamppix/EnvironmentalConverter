from pytube.contrib.playlist import Playlist
import ffmpeg
import os
from pydub.silence import detect_leading_silence
from pydub import AudioSegment
import re
import time
import shutil

TERRARIA = "https://youtube.com/playlist?list=PLmEInNWnJt01A24SN36oWl4OufV4L6Oex"


def get_videos(playlist: Playlist):
    """
    Downloads videos, converts them to .ogg from given Playlist object into a resource pack folder.
    """
    print("Getting videos from playlist: " + playlist.title)
    sounds_path = os.getcwd() + os.sep + "resourcepacks" + os.sep + playlist.title + os.sep + "assets" + os.sep + "environmentalmusic" + os.sep + "sounds"

    videos = playlist.videos

    for video in videos:
        title = video.title
        name = title.strip().lower().replace("-", "_").replace(" ", "_")
        while '__' in name:
            name = name.replace("__", "_")
        name = re.sub(r'[^a-z0-9/._-]', '', name) + ".ogg"

        # extract only audio
        print('Downloading ' + title + "...")
        video = video.streams.filter(only_audio=True).first()

        # download the file
        temp_mp4 = video.download(output_path = sounds_path)

        base, ext = os.path.splitext(temp_mp4)
        temp_ogg = base + ".ogg"

        if os.path.exists(sounds_path + os.sep + name):
            print(".ogg already exists!")
            # Delete temporary files
            os.remove(temp_mp4)
            os.remove(temp_ogg)
            continue
        
        # Convert to .ogg
        print("Converting to .ogg...")
        stream = ffmpeg.input(temp_mp4)
        stream = ffmpeg.output(stream, temp_ogg)
        ffmpeg.run(stream, quiet=True, overwrite_output=True)

        # Strip silence
        print("Stripping .ogg...")
        trim_leading_silence: AudioSegment = lambda x: x[detect_leading_silence(x) :]
        trim_trailing_silence: AudioSegment = lambda x: trim_leading_silence(x.reverse()).reverse()
        strip_silence: AudioSegment = lambda x: trim_trailing_silence(trim_leading_silence(x))

        sound = AudioSegment.from_file(temp_ogg)
        stripped = strip_silence(sound)
        # stripped.apply_gain_stereo(-4)
        path = sounds_path + os.sep + name
        stripped.export(path, format="ogg")

        # Delete temporary files
        os.remove(temp_mp4)
        os.remove(temp_ogg)

    print("Playlist downloaded!")
    return playlist.title


def main():
    print("Choose playlist to download: (C)ustom, (T)erraria.")
    choice = input(">> ").lower().strip()
    if choice == "custom" or choice == "c":
        url = input("Give playlist URL: ").strip()
    elif choice == "terraria" or choice == "t":
        url = TERRARIA
    elif choice == "q":
        print("Quitting...")
        exit()
    else:
        print("Invalid input!")
        main()

    playlist = Playlist(url)

    while True:
        try:
            title = get_videos(playlist)
        except ConnectionResetError as e:
            print(e)
            time.sleep(60)
        break

    if choice == "custom" or choice == "c":
        print("Copying template files")
        source = os.getcwd() + os.sep + "resourcepacks" + os.sep + "template" + os.sep
        pack_source = source + "pack.mcmeta"
        sounds_source = source + "assets" + os.sep + "environmentalmusic" + os.sep + "sounds.json"

        target = os.getcwd() + os.sep + "resourcepacks" + os.sep + title + os.sep
        pack_target = target + "pack.mcmeta"
        sounds_target = target + "assets" + os.sep + "environmentalmusic" + os.sep + "sounds.json"

        shutil.copy(pack_source, pack_target)
        shutil.copy(sounds_source, sounds_target)

    print("SUCCESS!")
    return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nQuitting...")
