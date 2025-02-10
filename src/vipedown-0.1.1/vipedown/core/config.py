from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict
from PyQt6.QtCore import QSettings
import json

@dataclass
class AppConfig:
    download_path: Path = Path.home() / "Downloads" / "VipeDown"
    default_format: str = "video"
    default_quality: str = "1080p"
    max_concurrent: int = 3
    dark_mode: bool = True
    save_metadata: bool = True
    save_thumbnail: bool = True
    auto_add_to_queue: bool = False
    minimize_to_tray: bool = True
    notify_on_complete: bool = True

class ConfigManager:
    def __init__(self):
        self.settings = QSettings("VipeDown", "Settings")
        self.config = self._load_config()
        self._ensure_paths()

    def _load_config(self) -> AppConfig:
        if self.settings.contains("config"):
            config_dict = json.loads(self.settings.value("config"))
            config_dict["download_path"] = Path(config_dict["download_path"])
            return AppConfig(**config_dict)
        return AppConfig()

    def save(self):
        config_dict = asdict(self.config)
        config_dict["download_path"] = str(config_dict["download_path"])
        self.settings.setValue("config", json.dumps(config_dict))
        self.settings.sync()

    def _ensure_paths(self):
        paths = [
            self.config.download_path,
            self.config.download_path / "Video",
            self.config.download_path / "Audio",
            Path.home() / ".config" / "vipedown"
        ]
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)

    def get_download_formats(self) -> Dict[str, Any]:
        return {
            "video": {
                "2160p": "Ultra HD",
                "1440p": "Quad HD",
                "1080p": "Full HD",
                "720p": "HD",
                "480p": "SD",
                "360p": "Low",
                "best": "Best Available"
            },
            "audio": {
                "mp3": ["320k", "256k", "192k", "128k"],
                "m4a": ["High", "Medium", "Low"],
                "opus": ["High", "Medium", "Low"],
                "wav": ["Lossless"],
                "flac": ["Lossless"]
            }
        }

    def get_default_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive"
        }

    def get_log_path(self) -> Path:
        log_path = Path.home() / ".local" / "share" / "vipedown" / "logs"
        log_path.mkdir(parents=True, exist_ok=True)
        return log_path