from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QProgressBar,
    QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from ..core.queue_manager import QueueManager, QueueItem, DownloadStatus

class QueueListItem(QWidget):
    def __init__(self, item: QueueItem):
        super().__init__()
        self.item = item
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        title_layout = QHBoxLayout()
        self.title_label = QLabel(item.title or item.url)
        self.status_label = QLabel(item.status.value)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(int(item.progress))
        
        info_layout = QHBoxLayout()
        format_label = QLabel(f"Format: {item.format_type}")
        quality_label = QLabel(f"Quality: {item.quality}")
        info_layout.addWidget(format_label)
        info_layout.addWidget(quality_label)
        if item.playlist:
            playlist_label = QLabel("Playlist")
            info_layout.addWidget(playlist_label)
        info_layout.addStretch()

        layout.addLayout(title_layout)
        layout.addWidget(self.progress_bar)
        layout.addLayout(info_layout)
        
        if item.error:
            error_label = QLabel(f"Error: {item.error}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)

    def update_progress(self, progress: float):
        self.progress_bar.setValue(int(progress))

    def update_status(self, status: DownloadStatus):
        self.status_label.setText(status.value)

class QueueWidget(QWidget):
    start_queue = pyqtSignal()
    pause_queue = pyqtSignal()
    remove_item = pyqtSignal(int)
    clear_queue = pyqtSignal()

    def __init__(self, queue_manager: QueueManager):
        super().__init__()
        self.queue_manager = queue_manager
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Control buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Queue")
        self.pause_button = QPushButton("Pause")
        self.clear_button = QPushButton("Clear")
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_list.customContextMenuRequested.connect(self._show_context_menu)

        # Status bar
        self.status_bar = QLabel()
        self._update_status_bar()

        layout.addLayout(button_layout)
        layout.addWidget(self.queue_list)
        layout.addWidget(self.status_bar)

        self._refresh_queue()

    def _connect_signals(self):
        self.start_button.clicked.connect(self.start_queue.emit)
        self.pause_button.clicked.connect(self.pause_queue.emit)
        self.clear_button.clicked.connect(self._confirm_clear)
        
        self.queue_manager.queue_updated.connect(self._refresh_queue)
        self.queue_manager.status_changed.connect(self._update_item_status)

    def _refresh_queue(self):
        self.queue_list.clear()
        for item in self.queue_manager.get_queue():
            list_item = QListWidgetItem()
            list_item.setSizeHint(QWidget().sizeHint())  # Will be updated when widget is set
            self.queue_list.addItem(list_item)
            
            item_widget = QueueListItem(item)
            self.queue_list.setItemWidget(list_item, item_widget)

        self._update_status_bar()
        self._update_buttons()

    def _update_status_bar(self):
        status = self.queue_manager.get_queue_status()
        status_text = f"Total: {len(self.queue_manager.get_queue())} | "
        status_text += f"Pending: {status[DownloadStatus.PENDING]} | "
        status_text += f"Downloading: {status[DownloadStatus.DOWNLOADING]} | "
        status_text += f"Completed: {status[DownloadStatus.COMPLETED]} | "
        status_text += f"Failed: {status[DownloadStatus.FAILED]}"
        self.status_bar.setText(status_text)

    def _update_buttons(self):
        queue_active = self.queue_manager.is_active()
        queue_paused = self.queue_manager.is_paused()
        has_items = bool(self.queue_manager.get_queue())

        self.start_button.setEnabled(has_items and not queue_active)
        self.pause_button.setEnabled(queue_active and not queue_paused)
        self.clear_button.setEnabled(has_items and not queue_active)

    def _show_context_menu(self, position):
        menu = QMenu()
        remove_action = menu.addAction("Remove")
        move_up_action = menu.addAction("Move Up")
        move_down_action = menu.addAction("Move Down")

        item = self.queue_list.itemAt(position)
        if item:
            index = self.queue_list.row(item)
            action = menu.exec(self.queue_list.mapToGlobal(position))
            
            if action == remove_action:
                self.remove_item.emit(index)
            elif action == move_up_action and index > 0:
                self.queue_manager.move_item(index, index - 1)
            elif action == move_down_action and index < self.queue_list.count() - 1:
                self.queue_manager.move_item(index, index + 1)

    def _confirm_clear(self):
        reply = QMessageBox.question(
            self,
            "Clear Queue",
            "Are you sure you want to clear the queue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_queue.emit()

    def update_item_progress(self, url: str, progress: float):
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            widget = self.queue_list.itemWidget(item)
            if widget.item.url == url:
                widget.update_progress(progress)
                break

    def _update_item_status(self, url: str, status: DownloadStatus):
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            widget = self.queue_list.itemWidget(item)
            if widget.item.url == url:
                widget.update_status(status)
                break
        self._update_status_bar()
        self._update_buttons()