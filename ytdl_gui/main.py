import sys
import os
from pathlib import Path
from typing import Optional, List, Dict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, 
    QTextEdit, QMessageBox, QCheckBox, QButtonGroup, QRadioButton,
    QStackedWidget, QStyle
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSettings
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette

from validators import url as validate_url
from slugify import slugify

import yt_dlp

class ThemeManager:
    """Manages application themes"""
    def __init__(self):
        self.settings = QSettings('YTDLPGui', 'ThemeSettings')
        self._current_theme = self.settings.value('theme', 'light')

    def get_palette(self, theme: str = None) -> QPalette:
        """Generate color palette based on theme"""
        theme = theme or self._current_theme
        palette = QPalette()

        if theme == 'dark':
            # Dark theme colors
            palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        else:
            # Light theme (default system palette)
            palette = QApplication.style().standardPalette()

        return palette

    def toggle_theme(self, app: QApplication) -> str:
        """Toggle between light and dark themes"""
        current_theme = self.settings.value('theme', 'light')
        new_theme = 'dark' if current_theme == 'light' else 'light'
        
        # Save theme preference
        self.settings.setValue('theme', new_theme)
        
        # Apply new palette
        app.setPalette(self.get_palette(new_theme))
        
        return new_theme

class VideoDownloadWorker(QThread):
    """Background worker for downloading videos"""
    progress_signal = pyqtSignal(str)
    download_complete = pyqtSignal(bool)

    def __init__(self, url: str, save_path: str, format_options: Dict):
        super().__init__()
        self.url = url
        self.save_path = Path(save_path)
        self.format_options = format_options
        self.is_cancelled = False

    def run(self):
        """Perform the download in a separate thread"""
        try:
            # Sanitize filename template
            output_template = str(self.save_path / '%(title)s-%(id)s.%(ext)s')
            
            # Configure ydl options based on format selection
            ydl_opts = {
                'outtmpl': output_template,
                'progress_hooks': [self.progress_hook],
                'quiet': True,
                'no_warnings': True,
                'restrictfilenames': True
            }

            # Customize format based on user selection
            format_key = self.format_options.get('type', 'video')
            quality = self.format_options.get('quality', 'best')

            # Build format string dynamically
            if format_key == 'video':
                # Map quality to format
                quality_map = {
                    'low': 'worstvideo[height<=360]+worstaudio/worst',
                    'medium': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                    'high': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                    'best': 'bestvideo+bestaudio/best'
                }
                ydl_opts['format'] = quality_map.get(quality, quality_map['best'])
            
            elif format_key == 'audio':
                # Audio extraction options
                audio_formats = {
                    'mp3': {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'},
                    'wav': {'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'},
                    'm4a': {'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a'}
                }
                
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    **audio_formats.get(quality, audio_formats['mp3'])
                }]

            # Verify save path exists and is writable
            if not self.save_path.exists():
                self.save_path.mkdir(parents=True, exist_ok=True)
            
            if not os.access(str(self.save_path), os.W_OK):
                raise PermissionError(f"No write permission for directory: {self.save_path}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            self.download_complete.emit(True)
        except Exception as e:
            self.progress_signal.emit(f"Download error: {str(e)}")
            self.download_complete.emit(False)

    def progress_hook(self, d: dict):
        """Update progress during download"""
        if self.is_cancelled:
            raise Exception("Download cancelled by user")
            
        if d['status'] == 'downloading':
            p = d.get('_percent_str', 'N/A')
            speed = d.get('speed', 0)
            if speed:
                speed_str = f"{speed/1024/1024:.1f} MB/s"
            else:
                speed_str = "N/A"
            self.progress_signal.emit(f"Downloading: {p} (Speed: {speed_str})")
        elif d['status'] == 'finished':
            self.progress_signal.emit("Processing download...")

class YTDLPFrontend(QMainWindow):
    def __init__(self):
        super().__init__()
        self.download_worker: Optional[VideoDownloadWorker] = None
        self.theme_manager = ThemeManager()
        self.init_ui()
        
        # Apply initial theme
        app = QApplication.instance()
        app.setPalette(self.theme_manager.get_palette())

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("YT-DLP Downloader")
        self.setGeometry(100, 100, 700, 600)

        # Main container
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Theme Toggle Button
        self.theme_button = QPushButton("🌓 Toggle Theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        main_layout.addWidget(self.theme_button)

        # URL Input
        url_layout = QHBoxLayout()
        url_label = QLabel("YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video URL...")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)

        # Download Type and Quality
        type_quality_layout = QHBoxLayout()

        # Type Selection
        type_group = QButtonGroup(self)
        self.video_radio = QRadioButton("Video")
        self.audio_radio = QRadioButton("Audio")
        type_group.addButton(self.video_radio)
        type_group.addButton(self.audio_radio)
        self.video_radio.setChecked(True)

        # Quality Selection
        self.quality_combo = QComboBox()
        self.update_quality_options()
        
        # Connect type radio buttons to update quality options
        self.video_radio.toggled.connect(self.update_quality_options)
        
        type_quality_layout.addWidget(QLabel("Type:"))
        type_quality_layout.addWidget(self.video_radio)
        type_quality_layout.addWidget(self.audio_radio)
        type_quality_layout.addWidget(QLabel("Quality:"))
        type_quality_layout.addWidget(self.quality_combo)
        main_layout.addLayout(type_quality_layout)

        # Download Path
        path_layout = QHBoxLayout()
        path_label = QLabel("Save Path:")
        self.path_input = QLineEdit()
        self.path_input.setText(str(Path.home() / "Downloads"))
        self.path_input.setReadOnly(True)
        path_button = QPushButton("Browse")
        path_button.clicked.connect(self.select_download_path)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(path_button)
        main_layout.addLayout(path_layout)

        # Download Button
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.start_download)
        main_layout.addWidget(self.download_button)

        # Progress Log
        self.progress_log = QTextEdit()
        self.progress_log.setReadOnly(True)
        main_layout.addWidget(self.progress_log)

    def update_quality_options(self):
        """Update quality options based on selected type"""
        self.quality_combo.clear()
        if self.video_radio.isChecked():
            self.quality_combo.addItems([
                'Best Quality', 
                'High (1080p)', 
                'Medium (720p)', 
                'Low (360p)'
            ])
        else:
            self.quality_combo.addItems([
                'MP3', 
                'WAV', 
                'M4A'
            ])

    def toggle_theme(self):
        """Toggle application theme"""
        app = QApplication.instance()
        theme = self.theme_manager.toggle_theme(app)
        self.progress_log.append(f"Switched to {theme} theme")

    def select_download_path(self):
        """Open file dialog to select download directory"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Download Directory",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        if path:
            self.path_input.setText(path)

    def start_download(self):
        """Initiate the download process"""
        url = self.url_input.text().strip()
        save_path = self.path_input.text().strip()

        # Validate URL
        if not url or not validate_url(url):
            QMessageBox.warning(self, "Input Error", "Please enter a valid URL.")
            return

        # Validate save path
        if not save_path or not Path(save_path).exists():
            QMessageBox.warning(self, "Input Error", "Please select a valid download path.")
            return

        # Prepare download options
        format_options = {
            'type': 'video' if self.video_radio.isChecked() else 'audio',
            'quality': self.get_selected_quality()
        }

        # Disable download button during download
        self.download_button.setEnabled(False)
        self.progress_log.clear()

        # Start download worker
        self.download_worker = VideoDownloadWorker(url, save_path, format_options)
        self.download_worker.progress_signal.connect(self.update_progress)
        self.download_worker.download_complete.connect(self.download_finished)
        self.download_worker.start()

    def get_selected_quality(self) -> str:
        """Map UI quality selection to yt-dlp format"""
        quality_text = self.quality_combo.currentText()
        if self.video_radio.isChecked():
            quality_map = {
                'Best Quality': 'best',
                'High (1080p)': 'high',
                'Medium (720p)': 'medium', 
                'Low (360p)': 'low'
            }
            return quality_map.get(quality_text, 'best')
        else:
            return quality_text.lower()

    def update_progress(self, message: str):
        """Update progress log"""
        self.progress_log.append(message)

    def download_finished(self, success: bool):
        """Handle download completion"""
        self.download_button.setEnabled(True)
        if success:
            QMessageBox.information(self, "Success", "Download completed successfully!")
        else:
            QMessageBox.warning(self, "Error", "Download failed. Check the log for details.")

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    frontend = YTDLPFrontend()
    frontend.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()