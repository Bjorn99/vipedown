import sys
from pathlib import Path
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QSpinBox, QComboBox, QCheckBox,
    QPushButton, QFileDialog, QGroupBox, QMessageBox
)
from PyQt6.QtCore import QSettings, Qt

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings('YTDLPGui', 'AppSettings')
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize settings dialog UI"""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)

        # Create tab widget
        tab_widget = QTabWidget()
        
        # Add tabs
        tab_widget.addTab(self.create_general_tab(), "General")
        tab_widget.addTab(self.create_video_tab(), "Video")
        tab_widget.addTab(self.create_audio_tab(), "Audio")
        tab_widget.addTab(self.create_advanced_tab(), "Advanced")
        
        layout.addWidget(tab_widget)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        reset_button = QPushButton("Reset to Defaults")

        save_button.clicked.connect(self.save_and_close)
        cancel_button.clicked.connect(self.reject)
        reset_button.clicked.connect(self.reset_settings)

        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def create_general_tab(self) -> QWidget:
        """Creating general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Default save location
        path_group = QGroupBox("Default Save Location")
        path_layout = QHBoxLayout()
        self.default_path = QLineEdit()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_path)
        path_layout.addWidget(self.default_path)
        path_layout.addWidget(browse_button)
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # Update checking
        update_group = QGroupBox("Updates")
        update_layout = QVBoxLayout()
        self.check_updates = QCheckBox("Check for updates on startup")
        self.auto_update = QCheckBox("Automatically install updates")
        update_layout.addWidget(self.check_updates)
        update_layout.addWidget(self.auto_update)
        update_group.setLayout(update_layout)
        layout.addWidget(update_group)

        # Interface options
        interface_group = QGroupBox("Interface")
        interface_layout = QVBoxLayout()
        self.minimize_to_tray = QCheckBox("Minimize to system tray")
        self.show_notifications = QCheckBox("Show desktop notifications")
        self.confirm_exit = QCheckBox("Confirm before exit")
        interface_layout.addWidget(self.minimize_to_tray)
        interface_layout.addWidget(self.show_notifications)
        interface_layout.addWidget(self.confirm_exit)
        interface_group.setLayout(interface_layout)
        layout.addWidget(interface_group)

        layout.addStretch()
        return tab

    def create_video_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Video quality presets
        quality_group = QGroupBox("Default Video Quality")
        quality_layout = QVBoxLayout()
        
        self.video_quality = QComboBox()
        self.video_quality.addItems([
            'Maximum Quality (8K/4K)',
            'Ultra HD (2160p)',
            'Quad HD (1440p)',
            'Full HD (1080p)',
            'HD (720p)',
            'SD (480p)',
            'Low (360p)'
        ])
        
        self.prefer_av1 = QCheckBox("Prefer AV1 codec when available")
        self.prefer_vp9 = QCheckBox("Prefer VP9 codec when available")
        self.max_video_height = QSpinBox()
        self.max_video_height.setRange(360, 8192)
        self.max_video_height.setSingleStep(360)
        self.max_video_height.setSuffix("p")
        
        quality_layout.addWidget(QLabel("Default Quality:"))
        quality_layout.addWidget(self.video_quality)
        quality_layout.addWidget(self.prefer_av1)
        quality_layout.addWidget(self.prefer_vp9)
        quality_layout.addWidget(QLabel("Maximum Video Height:"))
        quality_layout.addWidget(self.max_video_height)
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)

        # Video processing
        processing_group = QGroupBox("Video Processing")
        processing_layout = QVBoxLayout()
        
        self.embed_thumbnail = QCheckBox("Embed thumbnail in video file")
        self.embed_metadata = QCheckBox("Embed metadata")
        self.embed_chapters = QCheckBox("Embed chapters")
        self.remove_source = QCheckBox("Remove source files after processing")
        
        processing_layout.addWidget(self.embed_thumbnail)
        processing_layout.addWidget(self.embed_metadata)
        processing_layout.addWidget(self.embed_chapters)
        processing_layout.addWidget(self.remove_source)
        processing_group.setLayout(processing_layout)
        layout.addWidget(processing_group)

        layout.addStretch()
        return tab

    def create_audio_tab(self) -> QWidget:
        """Create audio settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Audio format settings
        format_group = QGroupBox("Audio Format")
        format_layout = QVBoxLayout()
        
        self.audio_format = QComboBox()
        self.audio_format.addItems([
            'FLAC (Lossless)',
            'WAV (Lossless)',
            'OPUS (High Quality)',
            'M4A (AAC)',
            'MP3 (320kbps)',
            'MP3 (256kbps)',
            'MP3 (192kbps)',
            'MP3 (128kbps)'
        ])
        
        self.audio_quality = QSpinBox()
        self.audio_quality.setRange(0, 10)
        self.audio_quality.setValue(5)
        self.audio_quality.setPrefix("Quality: ")
        
        format_layout.addWidget(QLabel("Default Format:"))
        format_layout.addWidget(self.audio_format)
        format_layout.addWidget(QLabel("Audio Quality (0-10, higher is better):"))
        format_layout.addWidget(self.audio_quality)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # Audio processing
        processing_group = QGroupBox("Audio Processing")
        processing_layout = QVBoxLayout()
        
        self.normalize_audio = QCheckBox("Normalize audio volume")
        self.split_by_chapters = QCheckBox("Split by chapters")
        self.extract_thumbnail = QCheckBox("Extract thumbnail")
        self.add_metadata = QCheckBox("Add metadata")
        
        processing_layout.addWidget(self.normalize_audio)
        processing_layout.addWidget(self.split_by_chapters)
        processing_layout.addWidget(self.extract_thumbnail)
        processing_layout.addWidget(self.add_metadata)
        processing_group.setLayout(processing_layout)
        layout.addWidget(processing_group)

        layout.addStretch()
        return tab

    def create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Download settings
        download_group = QGroupBox("Download Settings")
        download_layout = QVBoxLayout()
        
        self.max_concurrent = QSpinBox()
        self.max_concurrent.setRange(1, 10)
        self.max_concurrent.setValue(3)
        
        self.limit_speed = QSpinBox()
        self.limit_speed.setRange(0, 100000)
        self.limit_speed.setSingleStep(1000)
        self.limit_speed.setSuffix(" KB/s")
        
        self.retry_attempts = QSpinBox()
        self.retry_attempts.setRange(0, 10)
        self.retry_attempts.setValue(3)
        
        download_layout.addWidget(QLabel("Maximum Concurrent Downloads:"))
        download_layout.addWidget(self.max_concurrent)
        download_layout.addWidget(QLabel("Download Speed Limit (0 for unlimited):"))
        download_layout.addWidget(self.limit_speed)
        download_layout.addWidget(QLabel("Retry Attempts:"))
        download_layout.addWidget(self.retry_attempts)
        download_group.setLayout(download_layout)
        layout.addWidget(download_group)

        # Proxy settings
        proxy_group = QGroupBox("Proxy Settings")
        proxy_layout = QVBoxLayout()
        
        self.use_proxy = QCheckBox("Use Proxy")
        self.proxy_url = QLineEdit()
        self.proxy_url.setPlaceholderText("socks5://user:pass@hostname:port")
        
        proxy_layout.addWidget(self.use_proxy)
        proxy_layout.addWidget(QLabel("Proxy URL:"))
        proxy_layout.addWidget(self.proxy_url)
        proxy_group.setLayout(proxy_layout)
        layout.addWidget(proxy_group)

        # Debug options
        debug_group = QGroupBox("Debug Options")
        debug_layout = QVBoxLayout()
        
        self.verbose_output = QCheckBox("Enable verbose output")
        self.write_debug_log = QCheckBox("Write debug log")
        self.debug_location = QLineEdit()
        browse_debug = QPushButton("Browse")
        browse_debug.clicked.connect(self.browse_debug_path)
        
        debug_layout.addWidget(self.verbose_output)
        debug_layout.addWidget(self.write_debug_log)
        debug_layout.addWidget(QLabel("Debug Log Location:"))
        debug_hlayout = QHBoxLayout()
        debug_hlayout.addWidget(self.debug_location)
        debug_hlayout.addWidget(browse_debug)
        debug_layout.addLayout(debug_hlayout)
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)

        layout.addStretch()
        return tab

    def browse_path(self):
        """Browse for default save path"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Default Save Location",
            self.default_path.text()
        )
        if path:
            self.default_path.setText(path)

    def browse_debug_path(self):
        """Browse for debug log path"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Debug Log Location",
            self.debug_location.text()
        )
        if path:
            self.debug_location.setText(path)

    def load_settings(self):
        """Load saved settings"""
        # General settings
        self.default_path.setText(
            self.settings.value('save_path', str(Path.home() / "Downloads"))
        )
        self.check_updates.setChecked(
            self.settings.value('check_updates', True, type=bool)
        )
        self.auto_update.setChecked(
            self.settings.value('auto_update', False, type=bool)
        )
        self.minimize_to_tray.setChecked(
            self.settings.value('minimize_to_tray', True, type=bool)
        )
        self.show_notifications.setChecked(
            self.settings.value('show_notifications', True, type=bool)
        )
        self.confirm_exit.setChecked(
            self.settings.value('confirm_exit', True, type=bool)
        )

        # Video settings
        self.video_quality.setCurrentText(
            self.settings.value('video_quality', 'Full HD (1080p)')
        )
        self.prefer_av1.setChecked(
            self.settings.value('prefer_av1', False, type=bool)
        )
        self.prefer_vp9.setChecked(
            self.settings.value('prefer_vp9', True, type=bool)
        )
        self.max_video_height.setValue(
            self.settings.value('max_video_height', 1080, type=int)
        )
        self.embed_thumbnail.setChecked(
            self.settings.value('embed_thumbnail', True, type=bool)
        )
        self.embed_metadata.setChecked(
            self.settings.value('embed_metadata', True, type=bool)
        )
        self.embed_chapters.setChecked(
            self.settings.value('embed_chapters', True, type=bool)
        )
        self.remove_source.setChecked(
            self.settings.value('remove_source', False, type=bool)
        )

        # Audio settings
        self.audio_format.setCurrentText(
            self.settings.value('audio_format', 'MP3 (320kbps)')
        )
        self.audio_quality.setValue(
            self.settings.value('audio_quality', 5, type=int)
        )
        self.normalize_audio.setChecked(
            self.settings.value('normalize_audio', False, type=bool)
        )
        self.split_by_chapters.setChecked(
            self.settings.value('split_by_chapters', False, type=bool)
        )
        self.extract_thumbnail.setChecked(
            self.settings.value('extract_thumbnail', True, type=bool)
        )
        self.add_metadata.setChecked(
            self.settings.value('add_metadata', True, type=bool)
        )

        # Advanced settings
        self.max_concurrent.setValue(
            self.settings.value('max_concurrent', 3, type=int)
        )
        self.limit_speed.setValue(
            self.settings.value('limit_speed', 0, type=int)
        )
        self.retry_attempts.setValue(
            self.settings.value('retry_attempts', 3, type=int)
        )
        self.use_proxy.setChecked(
            self.settings.value('use_proxy', False, type=bool)
        )
        self.proxy_url.setText(
            self.settings.value('proxy_url', '')
        )
        self.verbose_output.setChecked(
            self.settings.value('verbose_output', False, type=bool)
        )
        self.write_debug_log.setChecked(
            self.settings.value('write_debug_log', False, type=bool)
        )
        self.debug_location.setText(
            self.settings.value('debug_location', str(Path.home() / "Downloads" / "logs"))
        )

    def save_settings(self):
        """Save all settings"""
        # General settings
        self.settings.setValue('save_path', self.default_path.text())
        self.settings.setValue('check_updates', self.check_updates.isChecked())
        self.settings.setValue('auto_update', self.auto_update.isChecked())
        self.settings.setValue('minimize_to_tray', self.minimize_to_tray.isChecked())
        self.settings.setValue('show_notifications', self.show_notifications.isChecked())
        self.settings.setValue('confirm_exit', self.confirm_exit.isChecked())

        # Video settings
        self.settings.setValue('video_quality', self.video_quality.currentText())
        self.settings.setValue('prefer_av1', self.prefer_av1.isChecked())
        self.settings.setValue('prefer_vp9', self.prefer_vp9.isChecked())
        self.settings.setValue('max_video_height', self.max_video_height.value())
        self.settings.setValue('embed_thumbnail', self.embed_thumbnail.isChecked())
        self.settings.setValue('embed_metadata', self.embed_metadata.isChecked())
        self.settings.setValue('embed_chapters', self.embed_chapters.isChecked())
        self.settings.setValue('remove_source', self.remove_source.isChecked())

        # Audio settings
        self.settings.setValue('audio_format', self.audio_format.currentText())
        self.settings.setValue('audio_quality', self.audio_quality.value())
        self.settings.setValue('normalize_audio', self.normalize_audio.isChecked())
        self.settings.setValue('split_by_chapters', self.split_by_chapters.isChecked())
        self.settings.setValue('extract_thumbnail', self.extract_thumbnail.isChecked())
        self.settings.setValue('add_metadata', self.add_metadata.isChecked())

        # Advanced settings
        self.settings.setValue('max_concurrent', self.max_concurrent.value())
        self.settings.setValue('limit_speed', self.limit_speed.value())
        self.settings.setValue('retry_attempts', self.retry_attempts.value())
        self.settings.setValue('use_proxy', self.use_proxy.isChecked())
        self.settings.setValue('proxy_url', self.proxy_url.text())
        self.settings.setValue('verbose_output', self.verbose_output.isChecked())
        self.settings.setValue('write_debug_log', self.write_debug_log.isChecked())
        self.settings.setValue('debug_location', self.debug_location.text())

    def reset_settings(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.clear()
            self.load_settings()

    def save_and_close(self):
        """Save settings and close dialog"""
        self.save_settings()
        self.accept()