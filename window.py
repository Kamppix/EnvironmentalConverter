import os, json
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QTabWidget, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QStyle, QTextEdit, QGridLayout, QComboBox, QFrame, QLineEdit, QMessageBox, QScrollArea, QSizePolicy
from PyQt6.QtGui import QIcon, QTextOption, QTextCursor
from PyQt6.QtCore import Qt
from sys import platform


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
        if self.objectName() == 'terraria_source_path':
            music_packs = self.parent().parent().findChild(MusicPackSelector, 'terraria_music_packs')
            pack_paths = None
            try:
                pack_paths = [f.path for f in os.scandir(self.text()) if f.is_dir()]
            except FileNotFoundError:
                pass
            music_packs.set_packs(pack_paths)
            

class MusicPackSelector(QComboBox):
    def __init__(self, parent):
        super().__init__(parent)
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
        self.clicked.connect(self.clicked_event)

    def clicked_event(self):
        index = self.parent().parent().findChild(QTabWidget, 'tabs').currentIndex()
        if index == 1:
            MusicPack.from_youtube(self.parent().parent().findChild(TextField, 'youtube_source_url').text(), self.parent().findChild(TextField, 'target_path').text())
        elif index == 2:
            selected_pack = self.parent().parent().findChild(MusicPackSelector, 'terraria_music_packs').current_folder()
            if selected_pack is not None:
                source = os.path.join(self.parent().parent().findChild(TextField, 'terraria_source_path').text(), selected_pack)
                with open(os.path.join(source, 'pack.json')) as pack_file:
                    title = json.load(pack_file)['Name']
                target = os.path.join(self.parent().findChild(TextField, 'target_path').text(), title)
                if not os.path.exists(target) or Application.overwrite_pack(self):
                    MusicPack.from_terraria(source, target)


class LogBox(QTextEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('log_box')
        self.setFixedHeight(128)
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


class FileSelector(QComboBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.addItem('--')
        self.files = []
    
    def set_files(self, paths):
        self.files.clear()
        for _ in range(self.count() - 1):
            self.removeItem(1)
        
        if paths is not None:
            items = []
            for path in paths:
                if os.path.exists(os.path.join(path, 'Content', 'Music', 'Music_1.ogg')) or os.path.exists(os.path.join(path, 'Content', 'Music', 'Music_1.mp3')) or os.path.exists(os.path.join(path, 'Content', 'Music', 'Music_1.wav')):
                    try:
                        with open(os.path.join(path, 'pack.json')) as pack_file:
                
                            items.append(json.load(pack_file)['Name'])
                            self.files.append(os.path.basename(os.path.normpath(path)))
                    except (FileNotFoundError, json.JSONDecodeError):
                        pass
            self.addItems(items)
    
    def current_folder(self):
        if len(self.files) > 1 and self.currentIndex() > 0:
            return self.files[self.currentIndex() - 1]


class FileAssignRow(QWidget):
    def __init__(self, title, parent):
        super().__init__(parent)
        self.setFixedSize(420, 40)
        row = QHBoxLayout(self)
        self.setLayout(row)

        label = QLabel(title + ':', self)
        label.setFixedWidth(90)
        row.addWidget(label)
        music_packs = FileSelector(self)
        row.addWidget(music_packs)


class FileAssigner(QScrollArea):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(120)
        child = QWidget(self)
        child.setMinimumHeight(100)
        v_box = QVBoxLayout(child)
        v_box.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        v_box.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinAndMaxSize)
        child.setLayout(v_box)

        v_box.addWidget(FileAssignRow('Overworld day', self))
        v_box.addWidget(FileAssignRow('Overworld night', self))
        v_box.addWidget(FileAssignRow('Underground', self))
        v_box.addWidget(FileAssignRow('Ender dragon', self))
        

class AppTab(QWidget):
    def __init__(self, parent: QMainWindow, index: int):
        super().__init__(parent)

        # Create source row
        v_box = QVBoxLayout(self)

        row = QWidget(self)
        v_box.addWidget(row)
        grid = QGridLayout(row)
        row.setLayout(grid)

        if index == 0:
            grid.addWidget(Label('Source folder:', self), 0, 0)

            source_path = TextField(os.getcwd(), self)
            source_path.setObjectName('files_source_path')
            grid.addWidget(source_path, 0, 1)

            browse_source_button = BrowseButton(self)
            browse_source_button.setObjectName('files_browse_button')
            grid.addWidget(browse_source_button, 0, 2)

            v_box.addWidget(FileAssigner(self))

        elif index == 1:
            grid.addWidget(Label('Playlist URL:', self), 0, 0)

            source_url = TextField('', self)
            source_url.setObjectName('youtube_source_url')
            grid.addWidget(source_url, 0, 1)

        elif index == 2:
            grid.addWidget(Label('Source folder:', self), 0, 0)

            source_path = TextField(SYSTEM_PATHS[platform]['terraria'], self)
            source_path.setObjectName('terraria_source_path')
            grid.addWidget(source_path, 0, 1)

            browse_source_button = BrowseButton(self)
            browse_source_button.setObjectName('terraria_browse_button')
            grid.addWidget(browse_source_button, 0, 2)
            
            grid.addWidget(Label('Music pack:', self), 1, 0)
            music_packs = MusicPackSelector(self)
            music_packs.setObjectName('terraria_music_packs')
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
        tabs.setFixedHeight(240)
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
        