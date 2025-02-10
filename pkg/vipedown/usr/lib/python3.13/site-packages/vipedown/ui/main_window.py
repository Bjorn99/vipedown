from pathlib import Path
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLineEdit, QComboBox, QLabel,
    QProgressBar, QSystemTrayIcon, QMenu, QFileDialog,
    QMessageBox, QGroupBox, QCheckBox, QSpinBox, QSplitter,
    QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction
import sys
from loguru import logger

from ..core.downloader import VipeDownloader, DownloadConfig
from ..core.config import ConfigManager
from ..core.queue_manager import QueueManager, QueueItem, DownloadStatus
from .queue_widget import QueueWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.downloader = VipeDownloader()
        self.config = ConfigManager()
        self.queue_manager = QueueManager()
        self._shutdown_requested = False
        self._setup_ui()
        self._setup_connections()
        self._setup_tray()

    def _setup_ui(self):
        self.setWindowTitle("VipeDown")
        self.setMinimumSize(QSize(1000, 600))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Download options widget
        download_widget = QWidget()
        download_layout = QVBoxLayout(download_widget)
        
        download_layout.addWidget(self._create_url_group())
        download_layout.addWidget(self._create_format_group())
        download_layout.addWidget(self._create_playlist_group())
        download_layout.addWidget(self._create_progress_group())
        download_layout.addLayout(self._create_button_layout())
        
        # Queue widget
        self.queue_widget = QueueWidget(self.queue_manager)
        
        splitter.addWidget(download_widget)
        splitter.addWidget(self.queue_widget)
        
        main_layout.addWidget(splitter)
        
        # Set initial splitter sizes (40% top, 60% bottom)
        splitter.setSizes([400, 600])
        
        self._update_quality_options("Video")

    def _create_url_group(self) -> QGroupBox:
        group = QGroupBox("Video URL")
        layout = QHBoxLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter video or playlist URL")
        
        self.paste_button = QPushButton("Paste")
        self.paste_button.setFixedWidth(70)

        layout.addWidget(self.url_input)
        layout.addWidget(self.paste_button)
        group.setLayout(layout)
        return group

    def _create_format_group(self) -> QGroupBox:
        group = QGroupBox("Format Options")
        layout = QVBoxLayout()

        format_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Video", "Audio"])
        self.quality_combo = QComboBox()

        format_layout.addWidget(QLabel("Format:"))
        format_layout.addWidget(self.format_combo)
        format_layout.addWidget(QLabel("Quality:"))
        format_layout.addWidget(self.quality_combo)
        format_layout.addStretch()

        layout.addLayout(format_layout)
        group.setLayout(layout)
        return group

    def _create_playlist_group(self) -> QGroupBox:
        group = QGroupBox("Playlist Options")
        layout = QVBoxLayout()

        self.playlist_check = QCheckBox("Download as Playlist")
        
        range_layout = QHBoxLayout()
        self.playlist_start = QSpinBox()
        self.playlist_start.setMinimum(1)
        self.playlist_start.setMaximum(9999)
        self.playlist_end = QSpinBox()
        self.playlist_end.setMinimum(1)
        self.playlist_end.setMaximum(9999)
        
        range_layout.addWidget(QLabel("Start:"))
        range_layout.addWidget(self.playlist_start)
        range_layout.addWidget(QLabel("End:"))
        range_layout.addWidget(self.playlist_end)
        range_layout.addStretch()

        self.playlist_items = QLineEdit()
        self.playlist_items.setPlaceholderText("Enter items (e.g., 1,3-5,7) or leave empty for all")
        
        self.create_playlist_folder = QCheckBox("Create Playlist Folder")
        self.create_playlist_folder.setChecked(True)
        
        layout.addWidget(self.playlist_check)
        layout.addLayout(range_layout)
        layout.addWidget(QLabel("Specific Items (optional):"))
        layout.addWidget(self.playlist_items)
        layout.addWidget(self.create_playlist_folder)
        
        group.setLayout(layout)
        self._toggle_playlist_options(False)
        return group

    def _create_progress_group(self) -> QGroupBox:
        group = QGroupBox("Progress")
        layout = QVBoxLayout()

        # Main progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v MB / %m MB")
        
        # Status labels
        status_layout = QHBoxLayout()
        self.phase_label = QLabel("Ready")
        self.speed_label = QLabel("")
        self.eta_label = QLabel("")
        status_layout.addWidget(self.phase_label)
        status_layout.addStretch()
        status_layout.addWidget(self.speed_label)
        status_layout.addWidget(self.eta_label)
        
        # Current file label
        self.file_label = QLabel("")
        self.file_label.setWordWrap(True)
        
        layout.addWidget(self.progress_bar)
        layout.addLayout(status_layout)
        layout.addWidget(self.file_label)
        
        group.setLayout(layout)
        return group

    def _create_button_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        
        # Left side - Exit button
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.safe_quit)
        
        # Right side - Download controls
        self.download_button = QPushButton("Add to Queue")
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        
        layout.addWidget(self.exit_button)
        layout.addStretch()
        layout.addWidget(self.download_button)
        layout.addWidget(self.cancel_button)
        
        return layout

    def _setup_connections(self):
        self.paste_button.clicked.connect(self._paste_url)
        self.format_combo.currentTextChanged.connect(self._update_quality_options)
        self.playlist_check.toggled.connect(self._toggle_playlist_options)

        self.queue_widget.start_queue.connect(self._start_queue_download)
        self.queue_widget.pause_queue.connect(self._pause_queue)
        self.queue_widget.remove_item.connect(self.queue_manager.remove_item)
        self.queue_widget.clear_queue.connect(self.queue_manager.clear_queue)

        self.download_button.setText("Add to Queue")
        self.download_button.clicked.connect(self._add_to_queue)
        self.cancel_button.clicked.connect(self._cancel_download)
        
        self.downloader.progress.connect(self._update_progress)
        self.downloader.completed.connect(self._download_finished)
        self.downloader.error.connect(self._show_error)
        self.downloader.playlist_progress.connect(self._update_playlist_progress)

    def _add_to_queue(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL")
            return

        queue_item = QueueItem(
            url=url,
            format_type=self.format_combo.currentText().lower(),
            quality=self._get_selected_quality(),
            playlist=self.playlist_check.isChecked(),
            playlist_items=self.playlist_items.text().strip() if hasattr(self, 'playlist_items') else "",
            audio_only=self.format_combo.currentText().lower() == "audio"
        )
        
        self.queue_manager.add_item(queue_item)
        self.url_input.clear()
        self.phase_label.setText("Added to queue")

    def _start_queue_download(self):
        if not self.queue_manager.is_active():
            self.queue_manager.set_active(True)
            self._process_next_in_queue()

    def _process_next_in_queue(self):
        if not self.queue_manager.is_active():
            return

        next_item = self.queue_manager.get_next_item()
        if next_item:
            config = DownloadConfig(
                url=next_item.url,
                output_path=self.config.config.download_path,
                format_type=next_item.format_type,
                quality=next_item.quality,
                audio_only=next_item.audio_only,
                playlist=next_item.playlist,
                playlist_items=next_item.playlist_items
            )
            self._reset_progress()
            self.phase_label.setText("Starting download...")  # Changed from status_label
            self.downloader.download(config)
        else:
            self.queue_manager.set_active(False)
            self.phase_label.setText("Queue completed")

    def _pause_queue(self):
        if self.queue_manager.is_active():
            self.queue_manager.pause_queue()
            self.downloader.cancel()
            self.phase_label.setText("Queue paused")

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ArrowDown))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.safe_quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        if self.config.config.minimize_to_tray:
            self.tray_icon.show()

    def _update_quality_options(self, format_type: str):
        self.quality_combo.clear()
        formats = self.config.get_download_formats()
        
        if format_type.lower() == "video":
            for quality, label in formats["video"].items():
                self.quality_combo.addItem(f"{label} ({quality})")
        else:
            for format_name, qualities in formats["audio"].items():
                for quality in qualities:
                    self.quality_combo.addItem(f"{format_name} ({quality})")

    def _toggle_playlist_options(self, enabled: bool):
        self.playlist_start.setEnabled(enabled)
        self.playlist_end.setEnabled(enabled)
        self.playlist_items.setEnabled(enabled)
        self.create_playlist_folder.setEnabled(enabled)

    def _paste_url(self):
        clipboard = self.clipboard()
        self.url_input.setText(clipboard.text())

    def _start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a URL")
            return

        self._prepare_download_ui()
        
        try:
            config = self._create_download_config(url)
            self.downloader.download(config)
        except Exception as e:
            logger.exception("Failed to start download")
            self._show_error(str(e))
            self._reset_download_ui()

    def _create_download_config(self, url: str) -> DownloadConfig:
        return DownloadConfig(
            url=url,
            output_path=self.config.config.download_path,
            format_type=self.format_combo.currentText().lower(),
            quality=self._get_selected_quality(),
            audio_only=self.format_combo.currentText().lower() == "audio",
            playlist=self.playlist_check.isChecked(),
            playlist_start=self.playlist_start.value(),
            playlist_end=self.playlist_end.value(),
            playlist_items=self.playlist_items.text().strip(),
            create_playlist_folder=self.create_playlist_folder.isChecked()
        )

    def _prepare_download_ui(self):
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.playlist_progress.setValue(0)
        self.status_label.setText("Starting download...")
        
        if self.playlist_check.isChecked():
            self.playlist_progress.show()
            self.playlist_label.show()
        else:
            self.playlist_progress.hide()
            self.playlist_label.hide()

    def _reset_download_ui(self):
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.playlist_progress.hide()
        self.playlist_label.hide()

    def _get_selected_quality(self) -> str:
        quality_text = self.quality_combo.currentText()
        if "(" in quality_text and ")" in quality_text:
            return quality_text.split("(")[1].split(")")[0]
        return "best"

    def _update_progress(self, progress: dict):
        try:
            if progress["status"] == "downloading":
                # Update progress bar
                percent = progress.get("percent", 0)
                self.progress_bar.setValue(int(percent))
                
                # Update file size in progress bar format
                total_mb = progress.get("total_bytes", 0) / 1024 / 1024
                downloaded_mb = progress.get("downloaded_bytes", 0) / 1024 / 1024
                self.progress_bar.setFormat(
                    f"%p% - {downloaded_mb:.1f} MB / {total_mb:.1f} MB"
                )
                
                # Update speed
                speed = progress.get("speed", 0)
                if speed > 0:
                    if speed > 1024 * 1024:  # MB/s
                        speed_str = f"{speed/1024/1024:.1f} MB/s"
                    else:  # KB/s
                        speed_str = f"{speed/1024:.1f} KB/s"
                    self.speed_label.setText(f"Speed: {speed_str}")
                else:
                    self.speed_label.setText("")
                
                # Update ETA
                eta = progress.get("eta", 0)
                if eta > 0:
                    if eta > 60:
                        eta_str = f"{eta//60}m {eta%60}s"
                    else:
                        eta_str = f"{eta}s"
                    self.eta_label.setText(f"ETA: {eta_str}")
                else:
                    self.eta_label.setText("")
                
                # Update phase and filename
                phase = progress.get("phase", "Downloading")
                fragment_info = progress.get("fragment_info", "")
                if fragment_info:
                    phase = f"{phase} - {fragment_info}"
                self.phase_label.setText(phase)
                
                filename = Path(progress.get('filename', '')).name
                self.file_label.setText(filename)
                
            elif progress["status"] == "processing":
                self.progress_bar.setValue(100)
                self.phase_label.setText(progress.get("phase", "Processing"))
                self.speed_label.setText("")
                self.eta_label.setText("")
                filename = Path(progress.get('filename', '')).name
                self.file_label.setText(filename)
                
        except Exception as e:
            logger.error(f"Error updating progress: {e}")

    def _update_playlist_progress(self, progress: dict):
        current = progress.get('current', 0)
        total = progress.get('total', 0)
        title = progress.get('title', '')
        
        if total > 0:
            percent = (current / total) * 100
            self.playlist_progress.setValue(int(percent))
            self.playlist_label.setText(f"Playlist Progress: {current}/{total} - Current: {title}")

    def _download_finished(self, success: bool, message: str):
        current_item = self.queue_manager.get_queue()[self.queue_manager._current_index]
        
        if success:
            self.queue_manager.update_status(current_item.url, DownloadStatus.COMPLETED)
            if self.config.config.notify_on_complete:
                self.tray_icon.showMessage(
                    "Download Complete",
                    f"Download completed: {current_item.url}",
                    self.tray_icon.MessageIcon.Information
                )
        else:
            self.queue_manager.update_status(current_item.url, DownloadStatus.FAILED, message)
            self.phase_label.setText(f"Download failed: {message}")  # Changed from status_label
            self.tray_icon.showMessage(
                "Download Failed",
                f"Failed to download: {current_item.url}",
                self.tray_icon.MessageIcon.Critical
            )

        self._process_next_in_queue()

    def _reset_progress(self):
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p% - 0 MB / 0 MB")
        self.phase_label.setText("Ready")
        self.speed_label.setText("")
        self.eta_label.setText("")
        self.file_label.setText("")

    def _show_error(self, error: str):
        QMessageBox.critical(self, "Error", error)

    def _cancel_download(self):
        if self.queue_manager.is_active():
            current_item = self.queue_manager.get_queue()[self.queue_manager._current_index]
            self.queue_manager.update_status(current_item.url, DownloadStatus.FAILED, "Cancelled")
            self.downloader.cancel()
            self.queue_manager.set_active(False)
            self.phase_label.setText("Download cancelled")
            self._reset_progress()

    def safe_quit(self):
        try:
            self._shutdown_requested = True
            
            self.hide()
            
            if hasattr(self, 'downloader') and self.downloader is not None:
                self.downloader.cancel()
            
            # Clear the queue
            if hasattr(self, 'queue_manager') and self.queue_manager is not None:
                self.queue_manager.clear_queue()

            if hasattr(self, 'config') and self.config is not None:
                self.config.save()
            
            if hasattr(self, 'tray_icon') and self.tray_icon is not None:
                try:
                    self.tray_icon.hide()
                    self.tray_icon.setVisible(False)
                    self.tray_icon.deleteLater()
                except:
                    pass
                finally:
                    self.tray_icon = None
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            QApplication.quit()
            sys.exit(0)

    def closeEvent(self, event):
        if not self._shutdown_requested and self.config.config.minimize_to_tray:
            event.ignore()
            self.hide()
        else:
            self.safe_quit()

    def closeEvent(self, event):
        if not self._shutdown_requested and self.config.config.minimize_to_tray:
            event.ignore()
            self.hide()
        else:
            self.safe_quit()