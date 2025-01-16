import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox, 
    QTextEdit, QMessageBox, QCheckBox, QButtonGroup, QRadioButton,
    QStackedWidget, QStyle, QProgressBar, QSystemTrayIcon, QMenu,
    QSpinBox, QGroupBox, QScrollArea
)

from .settings_dialog import SettingsDialog
from .download_worker import EnhancedDownloadWorker, DownloadConfig

from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSettings, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QAction, QPixmap

import yt_dlp
from validators import url as validate_url
from slugify import slugify


@dataclass
class ModernThemeManager:
    THEMES = {
        'light': {
            'window': QColor("#FFFFFF"),
            'text': QColor("#2C3E50"),
            'accent': QColor("#3498DB"),
            'button': QColor("#ECF0F1"),
            'button_hover': QColor("#BDC3C7"),
            'progress': QColor("#2ECC71"),
            'error': QColor("#E74C3C")
        },
        'dark': {
            'window': QColor("#2C3E50"),
            'text': QColor("#ECF0F1"),
            'accent': QColor("#3498DB"),
            'button': QColor("#34495E"),
            'button_hover': QColor("#2980B9"),
            'progress': QColor("#27AE60"),
            'error': QColor("#C0392B")
        },
        'nord': {
            'window': QColor("#2E3440"),
            'text': QColor("#ECEFF4"),
            'accent': QColor("#88C0D0"),
            'button': QColor("#3B4252"),
            'button_hover': QColor("#4C566A"),
            'progress': QColor("#A3BE8C"),
            'error': QColor("#BF616A")
        }
    }

    def __init__(self):
        self.settings = QSettings('YTDLPGui', 'ThemeSettings')
        self._current_theme = self.settings.value('theme', 'light')

    def get_palette(self, theme_name: str = None) -> QPalette:
        theme_name = theme_name or self._current_theme
        theme = self.THEMES[theme_name]
        palette = QPalette()

        # Set colors for various UI elements
        palette.setColor(QPalette.ColorRole.Window, theme['window'])
        palette.setColor(QPalette.ColorRole.WindowText, theme['text'])
        palette.setColor(QPalette.ColorRole.Base, theme['window'].darker(110))
        palette.setColor(QPalette.ColorRole.AlternateBase, theme['window'].darker(120))
        palette.setColor(QPalette.ColorRole.Text, theme['text'])
        palette.setColor(QPalette.ColorRole.Button, theme['button'])
        palette.setColor(QPalette.ColorRole.ButtonText, theme['text'])
        palette.setColor(QPalette.ColorRole.Highlight, theme['accent'])
        palette.setColor(QPalette.ColorRole.HighlightedText, theme['text'])

        return palette

    def cycle_theme(self, app: QApplication) -> str:
        """Cycle through available themes"""
        themes = list(self.THEMES.keys())
        current_idx = themes.index(self._current_theme)
        new_theme = themes[(current_idx + 1) % len(themes)]
        
        self.settings.setValue('theme', new_theme)
        self._current_theme = new_theme
        app.setPalette(self.get_palette(new_theme))
        
        return new_theme

class ModernYTDLPFrontend(QMainWindow):
    def __init__(self):
        super().__init__()
        self.download_worker = None
        self.theme_manager = ModernThemeManager()
        self.settings = QSettings('YTDLPGui', 'AppSettings')
        self.init_ui()
        self.setup_tray()
        
        # Apply saved theme
        app = QApplication.instance()
        app.setPalette(self.theme_manager.get_palette())

    def init_ui(self):
        """Initialize modern user interface"""
        self.setWindowTitle("Modern YT-DLP Downloader")
        self.setGeometry(100, 100, 800, 700)
        self.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown))

        # Main container with scroll area
        main_widget = QWidget()
        main_scroll = QScrollArea()
        main_scroll.setWidget(main_widget)
        main_scroll.setWidgetResizable(True)
        self.setCentralWidget(main_scroll)

        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Modern toolbar
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)

        # URL input with paste button
        url_group = QGroupBox("Video URL")
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video or playlist URL...")
        paste_button = QPushButton("📋")
        paste_button.clicked.connect(self.paste_url)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(paste_button)
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)

        # Download options
        options_group = QGroupBox("Download Options")
        options_layout = QVBoxLayout()
        
        # Format selection
        format_layout = QHBoxLayout()
        self.video_radio = QRadioButton("Video")
        self.audio_radio = QRadioButton("Audio")
        self.quality_combo = QComboBox()
        format_layout.addWidget(QLabel("Type:"))
        format_layout.addWidget(self.video_radio)
        format_layout.addWidget(self.audio_radio)
        format_layout.addWidget(QLabel("Quality:"))
        format_layout.addWidget(self.quality_combo)
        options_layout.addLayout(format_layout)
        
        # Playlist options
        playlist_layout = QHBoxLayout()
        self.playlist_check = QCheckBox("Download Playlist")
        self.start_index = QSpinBox()
        self.end_index = QSpinBox()
        self.start_index.setRange(1, 9999)
        self.end_index.setRange(1, 9999)
        self.start_index.setValue(1)
        playlist_layout.addWidget(self.playlist_check)
        playlist_layout.addWidget(QLabel("Start:"))
        playlist_layout.addWidget(self.start_index)
        playlist_layout.addWidget(QLabel("End:"))
        playlist_layout.addWidget(self.end_index)
        options_layout.addLayout(playlist_layout)

        # Additional options
        extra_layout = QHBoxLayout()
        self.thumbnail_check = QCheckBox("Download Thumbnail")
        self.metadata_check = QCheckBox("Save Metadata")
        self.subtitle_check = QCheckBox("Download Subtitles")
        self.subtitle_combo = QComboBox()
        self.subtitle_combo.addItems(['en', 'es', 'fr', 'de', 'it', 'pt', 'all'])
        self.subtitle_combo.setEnabled(False)
        extra_layout.addWidget(self.thumbnail_check)
        extra_layout.addWidget(self.metadata_check)
        extra_layout.addWidget(self.subtitle_check)
        extra_layout.addWidget(self.subtitle_combo)
        options_layout.addLayout(extra_layout)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # Save path selection
        path_group = QGroupBox("Save Location")
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setText(str(Path.home() / "Downloads"))
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.select_download_path)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)
        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        # Progress section
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m MB")
        
        self.status_label = QLabel("Ready")
        self.progress_log = QTextEdit()
        self.progress_log.setReadOnly(True)
        self.progress_log.setMaximumHeight(150)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_log)
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # Control buttons
        button_layout = QHBoxLayout()
        self.download_button = QPushButton("Start Download")
        self.download_button.clicked.connect(self.start_download)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        # Connect signals
        self.video_radio.toggled.connect(self.update_quality_options)
        self.subtitle_check.toggled.connect(self.subtitle_combo.setEnabled)
        self.playlist_check.toggled.connect(self.toggle_playlist_options)
        
        # Set initial state
        self.video_radio.setChecked(True)
        self.update_quality_options()
        self.load_settings()

    def create_toolbar(self) -> QWidget:
        """Creating a modern toolbar"""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        # Theme button
        self.theme_button = QPushButton("🎨 Theme")
        self.theme_button.clicked.connect(self.cycle_theme)
        
        # Settings button
        settings_button = QPushButton("⚙️ Settings")
        settings_button.clicked.connect(self.show_settings)
        
        # Help button
        help_button = QPushButton("❔ Help")
        help_button.clicked.connect(self.show_help)

        toolbar_layout.addWidget(self.theme_button)
        toolbar_layout.addWidget(settings_button)
        toolbar_layout.addWidget(help_button)
        toolbar_layout.addStretch()

        toolbar.setLayout(toolbar_layout)
        return toolbar

    def setup_tray(self):
        """Setup system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def load_settings(self):
        """Load saved application settings"""
        self.path_input.setText(self.settings.value('save_path', str(Path.home() / "Downloads")))
        self.metadata_check.setChecked(self.settings.value('save_metadata', True, type=bool))
        self.thumbnail_check.setChecked(self.settings.value('save_thumbnail', False, type=bool))

    def save_settings(self):
        """Save application settings"""
        self.settings.setValue('save_path', self.path_input.text())
        self.settings.setValue('save_metadata', self.metadata_check.isChecked())
        self.settings.setValue('save_thumbnail', self.thumbnail_check.isChecked())

    def toggle_playlist_options(self, enabled: bool):
        """Enable/disable playlist-specific options"""
        self.start_index.setEnabled(enabled)
        self.end_index.setEnabled(enabled)

    def update_quality_options(self):
        """Update quality options based on selected type"""
        self.quality_combo.clear()
        if self.video_radio.isChecked():
            self.quality_combo.addItems([
                'Maximum Quality (8K/4K)',
                'Ultra HD (2160p)',
                'Quad HD (1440p)',
                'Full HD (1080p)',
                'HD (720p)',
                'SD (480p)',
                'Low (360p)'
            ])
        else:
            self.quality_combo.addItems([
                'FLAC (Lossless)',
                'WAV (Lossless)',
                'OPUS (High Quality)',
                'M4A (AAC)',
                'MP3 (320kbps)',
                'MP3 (256kbps)',
                'MP3 (192kbps)',
                'MP3 (128kbps)'
            ])

    def cycle_theme(self):
        """Cycle through available themes"""
        app = QApplication.instance()
        new_theme = self.theme_manager.cycle_theme(app)
        self.status_label.setText(f"Theme changed to {new_theme}")

    def paste_url(self):
        """Paste URL from clipboard"""
        clipboard = QApplication.clipboard()
        self.url_input.setText(clipboard.text())

    def select_download_path(self):
        """Select download directory"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Download Directory",
            self.path_input.text(),
            QFileDialog.Option.ShowDirsOnly
        )
        if path:
            self.path_input.setText(path)
            self.save_settings()

    def show_settings(self):
        """Show settings dialog"""
        settings_dialog = SettingsDialog(self)
        if settings_dialog.exec():
            # Reload settings if dialog was accepted
            self.load_settings()

    def show_help(self):
        """Show help information"""
        help_text = """
        Modern YT-DLP Downloader Help

        1. Enter a video or playlist URL
        2. Select download type (video/audio) and quality
        3. Configure additional options if needed
        4. Choose save location
        5. Click 'Start Download'

        Supported platforms: YouTube, Vimeo, and many more.
        For more information, visit: https://github.com/yt-dlp/yt-dlp
        """
        QMessageBox.information(self, "Help", help_text)

    def start_download(self):
        """Start the download process"""
        url = self.url_input.text().strip()
        save_path = Path(self.path_input.text().strip())

        # Validate inputs
        if not url or not validate_url(url):
            QMessageBox.warning(self, "Input Error", "Please enter a valid URL")
            return

        # Create download configuration
        config = DownloadConfig(
            url=url,
            save_path=save_path,
            format_type='video' if self.video_radio.isChecked() else 'audio',
            quality=self.get_selected_quality(),
            playlist=self.playlist_check.isChecked(),
            start_index=self.start_index.value(),
            end_index=self.end_index.value() if self.playlist_check.isChecked() else None,
            subtitle_langs=[self.subtitle_combo.currentText()] if self.subtitle_check.isChecked() else None,
            thumbnail=self.thumbnail_check.isChecked(),
            metadata=self.metadata_check.isChecked()
        )

        # Update UI state
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_log.clear()
        self.status_label.setText("Starting download...")

        # Start download worker
        self.download_worker = EnhancedDownloadWorker(config, self.settings)
        self.download_worker.progress_signal.connect(self.update_progress)
        self.download_worker.download_complete.connect(self.download_finished)
        self.download_worker.playlist_info_signal.connect(self.show_playlist_info)
        self.download_worker.start()

        # Save settings
        self.save_settings()

    def get_selected_quality(self) -> str:
        """Get selected quality setting"""
        quality_text = self.quality_combo.currentText()
        if self.video_radio.isChecked():
            quality_map = {
                'Best Quality': 'best',
                'High (1080p)': 'high',
                'Medium (720p)': 'medium',
                'Low (480p)': 'low'
            }
            return quality_map.get(quality_text, 'best')
        else:
            return quality_text.split()[0]  # Get first word (MP3, WAV, etc.)

    def update_progress(self, progress: dict):
        """Updates download progress"""
        if progress['status'] == 'downloading':
            self.status_label.setText(f"Downloading: {progress['filename']}")
            self.progress_log.append(
                f"Speed: {progress['speed']} | ETA: {progress['eta']}"
            )
            
            if progress['total_bytes'] > 0:
                percent = (progress['downloaded_bytes'] / progress['total_bytes']) * 100
                self.progress_bar.setValue(int(percent))
                
        elif progress['status'] == 'processing':
            self.status_label.setText(f"Processing: {progress['filename']}")
            self.progress_log.append("Processing download...")

    def show_playlist_info(self, info: dict):
        """Displays playlist information"""
        self.progress_log.append(
            f"Playlist: {info['title']}\n"
            f"Total videos: {info['total_entries']}\n"
        )

    def cancel_download(self):
        """Cancels ongoing download"""
        if self.download_worker:
            self.download_worker.cancel()
            self.status_label.setText("Download cancelled")
            self.cancel_button.setEnabled(False)

    def download_finished(self, success: bool, message: str):
        """Handles download completion"""
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        
        if success:
            self.status_label.setText("Download completed successfully")
            self.tray_icon.showMessage(
                "Download Complete",
                "Your download has finished successfully",
                QSystemTrayIcon.MessageIcon.Information
            )
        else:
            self.status_label.setText("Download failed")
            self.progress_log.append(f"Error: {message}")
            self.tray_icon.showMessage(
                "Download Failed",
                message,
                QSystemTrayIcon.MessageIcon.Critical
            )

    def closeEvent(self, event):
        """Handles application close event"""
        self.save_settings()
        event.accept()

def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("Modern YT-DLP Downloader")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("YTDLPGui")
    
    # Creates and shows main window
    frontend = ModernYTDLPFrontend()
    frontend.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()