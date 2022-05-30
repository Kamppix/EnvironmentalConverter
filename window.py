import os, shutil, json
from sys import platform
from time import sleep
from main import NewThread
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QTabWidget, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QStyle, QTextEdit, QGridLayout, QComboBox, QFrame, QLineEdit, QMessageBox, QScrollArea, QSizePolicy
from PyQt6.QtGui import QIcon, QTextOption, QTextCursor
from PyQt6.QtCore import Qt
from pytube.contrib.playlist import Playlist
from urllib.error import URLError


SYSTEM_PATHS = {'win32': { 'minecraft': os.path.join(os.getenv('AppData'), '.minecraft', 'resourcepacks'), 'terraria': 'C:\Program Files (x86)\Steam\steamapps\workshop\content\\105600' },
                'darwin': { 'minecraft': '~/Library/Application Support/minecraft/resourcepacks', 'terraria': '~/Library/Application Support/Steam/steamapps/workshop/content/105600' },
                'linux': { 'minecraft': '~/.minecraft/resourcepacks', 'terraria': '~/.steam/steam/steamapps/workshop/content/105600' }}


app_instance = None


class Label(QLabel):
    '''A label placed on the left side of a TextField to describe its contents.'''
    def __init__(self, text, parent):
        super().__init__(text, parent)
        self.setFixedSize(73, 26)


class TextField(QLineEdit):
    '''An editable field of text for file paths and URLs.'''
    def __init__(self, text, parent):
        super().__init__(text, parent)
        self.setFixedHeight(26)
        self.textChanged.connect(self.text_changed_event)
    
    def text_changed_event(self):
        if self.objectName() == 'files_source_path':
            file_paths = None
            try:
                file_paths = [f.path for f in os.scandir(self.text()) if f.is_file() and (f.name.endswith('.ogg') or f.name.endswith('.mp3') or f.name.endswith('.wav'))]
            except FileNotFoundError:
                pass
            
            for selector in self.parent().parent().findChildren(FileSelector, 'files_selector'):
                selector.set_files(file_paths)
            
        elif self.objectName() == 'terraria_source_path':
            pack_paths = None
            try:
                pack_paths = [f.path for f in os.scandir(self.text()) if f.is_dir()]
            except FileNotFoundError:
                pass
            self.parent().parent().findChild(MusicPackSelector, 'terraria_music_packs').set_packs(pack_paths)


class FetchVideosButton(QPushButton):
    def __init__(self, parent):
        super().__init__(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload), '', parent)
        self.setObjectName('youtube_fetch_button')
        self.setFixedSize(26, 26)
        self.setToolTip('Fetch playlist')
        self.clicked.connect(self.button_pushed)

    def button_pushed(self):
        NewThread(target = self.fetch)

    def fetch(self):
        Logger.log('Fetching playlist data...')
        video_titles = None
        url = self.parent().findChild(TextField, 'youtube_source_url').text()
        while True:
            try:
                self.playlist = Playlist(url)
                video_titles = [v.title for v in self.playlist.videos]
                Logger.log('Found playlist "' + self.playlist.title + '" with ' + str(len(video_titles)) + ' videos')
                for selector in self.parent().parent().findChildren(VideoSelector, 'video_selector'):
                    selector.set_videos(video_titles)
                break
            except (ConnectionResetError, URLError):
                Logger.log('Connection to YouTube lost. Trying again in 3 seconds...')
                sleep(3)
            except KeyError:
                Logger.log('Invalid playlist URL!')
                return
            

class MusicPackSelector(QComboBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('terraria_music_packs')
        self.addItem('--')
        self.folders = []
    
    def set_packs(self, paths):
        self.folders.clear()
        for _ in range(self.count() - 1):
            self.removeItem(1)
        
        if paths is not None:
            items = []
            for path in paths:
                if os.path.exists(os.path.join(path, 'Content', 'Music', 'Music_1.ogg')) or os.path.exists(os.path.join(path, 'Content', 'Music', 'Music_1.mp3')) or os.path.exists(os.path.join(path, 'Content', 'Music', 'Music_1.wav')):
                    try:
                        with open(os.path.join(path, 'pack.json')) as pack_file:
                            items.append(json.load(pack_file)['Name'])
                            self.folders.append(os.path.basename(os.path.normpath(path)))
                    except (FileNotFoundError, json.JSONDecodeError):
                        pass
            self.addItems(items)
    
    def current_folder(self):
        if len(self.folders) > 1 and self.currentIndex() > 0:
            return self.folders[self.currentIndex() - 1]


class SelectFolderDialog(QFileDialog):
    def __init__(self, parent, title, path):
        super().__init__(parent, title, path)
        self.setFileMode(QFileDialog.FileMode.Directory)

    def path(self):
        if (self.exec() and self.selectedFiles()[0] is not None):
            return self.selectedFiles()[0].replace('/', os.sep)


class BrowseButton(QPushButton):
    def __init__(self, parent):
        super().__init__(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon), '', parent)
        self.setFixedSize(26, 26)
        self.setToolTip('Browse')
        self.clicked.connect(self.clicked_event)

    def clicked_event(self):
        if self.objectName() == 'files_browse_button':
            files_source_path = self.parent().findChild(TextField, 'files_source_path')
            files_source_path.setText(SelectFolderDialog(self.parent(), 'Select source folder', files_source_path.text()).path() or files_source_path.text())
            
        elif self.objectName() == 'terraria_browse_button':
            terraria_source_path = self.parent().findChild(TextField, 'terraria_source_path')
            terraria_source_path.setText(SelectFolderDialog(self.parent(), 'Select Terraria resource pack folder', terraria_source_path.text()).path() or terraria_source_path.text())

        elif self.objectName() == 'target_browse_button':
            target_path = self.parent().findChild(TextField, 'target_path')
            target_path.setText(SelectFolderDialog(self.parent(), 'Select output folder', target_path.text()).path() or target_path.text())


class CreateButton(QPushButton):
    def __init__(self, parent):
        super().__init__('Create', parent)
        self.setFixedHeight(26)
        self.setToolTip('Create music pack')
        self.clicked.connect(self.clicked_event)

    def clicked_event(self):
        index = self.parent().parent().findChild(QTabWidget, 'tabs').currentIndex()
        if index == 0:
            pack_name = self.parent().parent().findChild(TextField, 'files_pack_name').text()
            if len(pack_name) == 0 or string_contains_characters(pack_name, '\\/:*?"<>|'):
                Logger.log('Invalid pack name!')
            else:
                target = os.path.join(self.parent().findChild(TextField, 'target_path').text(), pack_name)
                if os.path.exists(target) and Application.overwrite_pack(self):
                    shutil.rmtree(target)
                    Logger.log('Removed the existing directory and its contents')
                if not os.path.exists(target):
                    source_folder = self.parent().parent().findChild(TextField, 'files_source_path').text()
                    MusicPack.from_files([os.path.join(source_folder, s.current_file()) for s in self.parent().parent().findChild(AppTab, 'files_tab').findChildren(FileSelector, 'files_selector')], target)
                

        elif index == 1:
            playlist = self.parent().parent().findChild(FetchVideosButton, 'youtube_fetch_button').playlist
            pack_name = self.parent().parent().findChild(TextField, 'youtube_pack_name').text()

            if len(pack_name) == 0 or string_contains_characters(pack_name, '\\/:*?"<>|'):
                Logger.log('Invalid pack name!')
            else:
                target = os.path.join(self.parent().findChild(TextField, 'target_path').text(), pack_name)
                if os.path.exists(target) and Application.overwrite_pack(self):
                    shutil.rmtree(target)
                    Logger.log('Removed the existing directory and its contents')
                if not os.path.exists(target):
                    MusicPack.from_youtube(playlist, [s.currentIndex() - 1 for s in self.parent().parent().findChild(AppTab, 'youtube_tab').findChildren(VideoSelector, 'video_selector')], target)
            
        elif index == 2:
            selected_pack = self.parent().parent().findChild(MusicPackSelector, 'terraria_music_packs').current_folder()
            if selected_pack is not None:
                source = os.path.join(self.parent().parent().findChild(TextField, 'terraria_source_path').text(), selected_pack)
                with open(os.path.join(source, 'pack.json')) as pack_file:
                    title = json.load(pack_file)['Name']
                target = os.path.join(self.parent().findChild(TextField, 'target_path').text(), title)
                if os.path.exists(target) and Application.overwrite_pack(self):
                    shutil.rmtree(target)
                    Logger.log('Removed the existing directory and its contents')
                if not os.path.exists(target):
                    MusicPack.from_terraria(source, target)


class LogBox(QTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('log_box')
        self.setFixedHeight(100)
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.setLineWrapColumnOrWidth(self.parent().parent().width() - 36)
        self.setFrameShape(QFrame.Shape.Box)
        self.textChanged.connect(self.auto_scroll)
    
    def auto_scroll(self):
        self.moveCursor(QTextCursor.MoveOperation.End)


class VideoSelector(QComboBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('video_selector')
        self.setFixedWidth(360)
        self.addItem('--')
    
    def set_videos(self, titles):
        for _ in range(self.count() - 1):
            self.removeItem(1)
        
        if titles is not None:
            for title in titles:
                self.addItem(title)


class VideoAssignRow(QWidget):
    def __init__(self, title, parent):
        super().__init__(parent)
        self.setFixedSize(480, 40)
        row = QHBoxLayout(self)
        self.setLayout(row)

        label = QLabel(title + ':', self)
        label.setFixedWidth(100)
        row.addWidget(label)
        videos = VideoSelector(self)
        row.addWidget(videos)


class FileSelector(QComboBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('files_selector')
        self.setFixedWidth(360)
        self.addItem('--')
    
    def set_files(self, paths):
        for _ in range(self.count() - 1):
            self.removeItem(1)
        
        if paths is not None:
            for path in paths:
                self.addItem(os.path.basename(os.path.normpath(path)))
    
    def current_file(self):
        return self.currentText()


class FileAssignRow(QWidget):
    def __init__(self, title, parent):
        super().__init__(parent)
        self.setFixedSize(480, 40)
        row = QHBoxLayout(self)
        self.setLayout(row)

        label = QLabel(title + ':', self)
        label.setFixedWidth(100)
        row.addWidget(label)
        files = FileSelector(self)
        row.addWidget(files)


class MusicAssigner(QScrollArea):
    def __init__(self, row, parent):
        super().__init__(parent)
        self.setFixedHeight(155)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setWidgetResizable(True)
        child = QWidget(self)
        v_box = QVBoxLayout(child)
        v_box.setSpacing(0)
        v_box.setContentsMargins(0, 0, 0, 0)
        v_box.setAlignment(Qt.AlignmentFlag.AlignLeft)
        v_box.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinAndMaxSize)
        child.setLayout(v_box)
        self.setWidget(child)

        with open(os.path.join(os.getcwd(), 'music_packs', 'template', 'assets', 'environmentalmusic', 'sounds.json')) as sounds_file:
            sounds_data = json.load(sounds_file)
            for event, _ in sounds_data.items():
                v_box.addWidget(row(event[6:].replace('_', ' ').capitalize(), self))


class AppTab(QWidget):
    def __init__(self, parent: QMainWindow, index: int):
        super().__init__(parent)
        v_box = QVBoxLayout(self)

        # Create source row
        row = QWidget(self)
        v_box.addWidget(row)
        grid = QGridLayout(row)
        row.setLayout(grid)

        if index == 0:
            self.setObjectName('files_tab')

            grid.addWidget(Label('Source folder:', self), 0, 0)

            source_path = TextField(os.getcwd(), self)
            source_path.setObjectName('files_source_path')
            grid.addWidget(source_path, 0, 1)

            browse_source_button = BrowseButton(self)
            browse_source_button.setObjectName('files_browse_button')
            grid.addWidget(browse_source_button, 0, 2)

            grid.addWidget(Label('Pack name:', self), 1, 0)
            pack_name = TextField(None, self)
            pack_name.setObjectName('files_pack_name')
            grid.addWidget(pack_name, 1, 1)

            v_box.addWidget(MusicAssigner(FileAssignRow, self))

        elif index == 1:
            self.setObjectName('youtube_tab')

            grid.addWidget(Label('Playlist URL:', self), 0, 0)

            source_url = TextField('', self)
            source_url.setObjectName('youtube_source_url')
            grid.addWidget(source_url, 0, 1)

            fetch_videos_button = FetchVideosButton(self)
            grid.addWidget(fetch_videos_button, 0, 2)

            grid.addWidget(Label('Pack name:', self), 1, 0)
            pack_name = TextField(None, self)
            pack_name.setObjectName('youtube_pack_name')
            grid.addWidget(pack_name, 1, 1)

            v_box.addWidget(MusicAssigner(VideoAssignRow, self))

        elif index == 2:
            self.setObjectName('terraria_tab')

            grid.addWidget(Label('Source folder:', self), 0, 0)

            source_path = TextField(SYSTEM_PATHS[platform]['terraria'], self)
            source_path.setObjectName('terraria_source_path')
            grid.addWidget(source_path, 0, 1)

            browse_source_button = BrowseButton(self)
            browse_source_button.setObjectName('terraria_browse_button')
            grid.addWidget(browse_source_button, 0, 2)
            
            grid.addWidget(Label('Music pack:', self), 1, 0)
            music_packs = MusicPackSelector(self)
            source_path.text_changed_event()
            grid.addWidget(music_packs, 1, 1)


class Application(QApplication):
    def create_ui(self):
        DEFAULT_TARGET = os.path.join(os.getenv('AppData'), '.minecraft', 'resourcepacks')
        self.setWindowIcon(QIcon('app_icon.ico'))
        # Initialize window
        self.window = QMainWindow()
        self.window.setWindowTitle('Pixel Music Packer')
        self.window.setWindowIcon(QIcon('app_icon.ico'))
        self.window.setFixedSize(640, 500)

        # Create layout
        column = QWidget(self.window)
        self.window.setCentralWidget(column)
        v_box = QVBoxLayout(column)
        v_box.setContentsMargins(8, 8, 8, 8)
        column.setLayout(v_box)

        # Create tabs
        tabs = QTabWidget(column)
        tabs.setObjectName('tabs')
        tabs.setFixedHeight(283)
        tabs.addTab(AppTab(column, 0), 'Local files')
        tabs.addTab(AppTab(column, 1), 'YouTube')
        tabs.addTab(AppTab(column, 2), 'Terraria')
        v_box.addWidget(tabs)

        # Create target row
        row = QWidget(column)
        row.setFixedHeight(60)
        h_box = QHBoxLayout(row)
        row.setLayout(h_box)
        v_box.addWidget(row)
            
        h_box.addWidget(Label('Target folder:', row))
        target_path = TextField(SYSTEM_PATHS[platform]['minecraft'], row)
        target_path.setObjectName('target_path')
        h_box.addWidget(target_path)
        browse_target_button = BrowseButton(row)
        browse_target_button.setObjectName('target_browse_button')
        h_box.addWidget(browse_target_button)
        create_button = CreateButton(row)
        h_box.addWidget(create_button)
        
        # Create Log box
        v_box.addWidget(Label('Log output:', row))
        v_box.addWidget(LogBox(column))

        # Add stretch
        v_box.addStretch()

        # Show window
        self.window.show()

    def __init__(self, logger, musicPack):
        super().__init__([])

        global app_instance
        app_instance = self

        global Logger
        Logger = logger
        global MusicPack
        MusicPack = musicPack

        self.create_ui()
        Logger.log('Application window created')
        self.exec()

    def overwrite_pack(parent):
        message_box = QMessageBox(QMessageBox.Icon.Warning, 'Folder already exists', 'Do you want to overwrite the existing folder?', QMessageBox.StandardButton.No, parent)
        yes_button = message_box.addButton(QMessageBox.StandardButton.Yes)
        message_box.exec()
        return message_box.clickedButton() == yes_button
    
    def log(self, line):
        log_box = self.window.findChild(QTextEdit, 'log_box')
        if log_box is not None:
            log_box.append(line)
        return
    
    def instance():
        global app_instance
        return app_instance


def string_contains_characters(string, characters):
    for c in characters:
        if c in string:
            return True
        