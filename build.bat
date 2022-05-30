pyinstaller --onefile --icon=app_icon.ico --clean main.pyw
md bin
copy "dist\main.exe" "bin\PixelMusicPacker.exe" /y
copy "app_icon.ico" "bin\app_icon.ico" /y
copy "ffmpeg.exe" "bin\ffmpeg.exe" /y
copy "run.bat" "bin\run.bat" /y
xcopy "template_pack\" "bin\template_pack\" /y /e /i
rmdir dist /s /q
rmdir build /s /q
rmdir __pycache__ /s /q
del main.spec
