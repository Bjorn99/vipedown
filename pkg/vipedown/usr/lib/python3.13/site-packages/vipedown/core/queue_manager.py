from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
import json
from loguru import logger

class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class QueueItem:
    url: str
    format_type: str
    quality: str
    playlist: bool
    playlist_items: str
    audio_only: bool
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0
    error: str = ""
    title: str = ""
    id: Optional[str] = None

class QueueManager(QObject):
    queue_updated = pyqtSignal()
    status_changed = pyqtSignal(str, DownloadStatus)
    
    def __init__(self):
        super().__init__()
        self._queue: List[QueueItem] = []
        self._current_index: int = -1
        self._active: bool = False
        self._paused: bool = False
        self._queue_file = Path.home() / ".config" / "vipedown" / "queue.json"
        self.clear_queue()

    def add_item(self, item: QueueItem) -> None:
        self._queue.append(item)
        self._save_queue()
        self.queue_updated.emit()

    def remove_item(self, index: int) -> None:
        if 0 <= index < len(self._queue):
            if index == self._current_index and self._active:
                return
            del self._queue[index]
            if index < self._current_index:
                self._current_index -= 1
            self._save_queue()
            self.queue_updated.emit()

    def clear_queue(self) -> None:
        if not self._active:
            self._queue.clear()
            self._current_index = -1
            self._save_queue()
            self.queue_updated.emit()

    def move_item(self, from_index: int, to_index: int) -> None:
        if (0 <= from_index < len(self._queue) and 
            0 <= to_index < len(self._queue) and 
            from_index != self._current_index):
            item = self._queue.pop(from_index)
            self._queue.insert(to_index, item)
            self._save_queue()
            self.queue_updated.emit()

    def get_next_item(self) -> Optional[QueueItem]:
        if self._paused or not self._queue:
            return None
            
        next_index = self._current_index + 1
        if next_index < len(self._queue):
            self._current_index = next_index
            item = self._queue[next_index]
            item.status = DownloadStatus.DOWNLOADING
            self.status_changed.emit(item.url, DownloadStatus.DOWNLOADING)
            self._save_queue()
            self.queue_updated.emit()
            return item
        return None

    def update_progress(self, url: str, progress: float) -> None:
        for item in self._queue:
            if item.url == url:
                item.progress = progress
                self.queue_updated.emit()
                break

    def update_status(self, url: str, status: DownloadStatus, error: str = "") -> None:
        for item in self._queue:
            if item.url == url:
                item.status = status
                item.error = error
                self.status_changed.emit(url, status)
                self._save_queue()
                self.queue_updated.emit()
                break

    def pause_queue(self) -> None:
        self._paused = True
        self.queue_updated.emit()

    def resume_queue(self) -> None:
        self._paused = False
        self.queue_updated.emit()

    def is_paused(self) -> bool:
        return self._paused

    def is_active(self) -> bool:
        return self._active

    def set_active(self, active: bool) -> None:
        self._active = active
        if not active:
            self._current_index = -1
        self.queue_updated.emit()

    def get_queue(self) -> List[QueueItem]:
        return self._queue.copy()

    def get_queue_status(self) -> Dict[str, int]:
        status_count = {status: 0 for status in DownloadStatus}
        for item in self._queue:
            status_count[item.status] += 1
        return status_count

    def _save_queue(self) -> None:
        try:
            self._queue_file.parent.mkdir(parents=True, exist_ok=True)
            queue_data = [
                {
                    'url': item.url,
                    'format_type': item.format_type,
                    'quality': item.quality,
                    'playlist': item.playlist,
                    'playlist_items': item.playlist_items,
                    'audio_only': item.audio_only,
                    'status': item.status.value,
                    'progress': item.progress,
                    'error': item.error,
                    'title': item.title,
                    'id': item.id
                }
                for item in self._queue
            ]
            self._queue_file.write_text(json.dumps(queue_data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save queue: {e}")

    def _load_queue(self) -> None:
        try:
            if self._queue_file.exists():
                queue_data = json.loads(self._queue_file.read_text())
                self._queue = [
                    QueueItem(
                        url=item['url'],
                        format_type=item['format_type'],
                        quality=item['quality'],
                        playlist=item['playlist'],
                        playlist_items=item['playlist_items'],
                        audio_only=item['audio_only'],
                        status=DownloadStatus(item['status']),
                        progress=item['progress'],
                        error=item['error'],
                        title=item['title'],
                        id=item['id']
                    )
                    for item in queue_data
                ]
        except Exception as e:
            logger.error(f"Failed to load queue: {e}")
            self._queue = []