from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal
import yt_dlp
from loguru import logger
import re

@dataclass
class PlaylistInfo:
    title: str
    uploader: str
    description: str
    entries: list
    entry_count: int
    webpage_url: str

    @classmethod
    def from_dict(cls, info_dict: Dict[str, Any]) -> 'PlaylistInfo':
        return cls(
            title=info_dict.get('title', 'Unknown Playlist'),
            uploader=info_dict.get('uploader', 'Unknown'),
            description=info_dict.get('description', ''),
            entries=info_dict.get('entries', []),
            entry_count=len(info_dict.get('entries', [])),
            webpage_url=info_dict.get('webpage_url', '')
        )

@dataclass
class DownloadConfig:
    url: str
    output_path: Path
    format_type: str = "video"
    quality: str = "best"
    subtitles: bool = False
    playlist: bool = False
    audio_only: bool = False
    audio_format: str = "mp3"
    audio_quality: str = "192"
    playlist_start: int = 1
    playlist_end: Optional[int] = None
    playlist_items: str = ""
    create_playlist_folder: bool = True

class VipeDownloader(QObject):
    progress = pyqtSignal(dict)
    completed = pyqtSignal(bool, str)
    error = pyqtSignal(str)
    info = pyqtSignal(dict)
    playlist_progress = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._ydl = None
        self._active = False
        self._current_item = 0
        self._total_items = 0

    def download(self, config: DownloadConfig):
        try:
            self._active = True
            ydl_opts = self._create_options(config)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self._ydl = ydl
                self._extract_and_download(config, ydl)
                
        except Exception as e:
            logger.exception("Download failed")
            self.error.emit(str(e))
            self.completed.emit(False, f"Download failed: {str(e)}")
        finally:
            self._cleanup()

    def _extract_and_download(self, config: DownloadConfig, ydl: yt_dlp.YoutubeDL):
        try:
            info = ydl.extract_info(config.url, download=False)
            if not info or not self._active:
                return

            if info.get('_type') == 'playlist':
                self._handle_playlist(config, ydl, info)
            else:
                self._handle_single_video(info)

            if self._active:
                ydl.download([config.url])
                self.completed.emit(True, "Download completed successfully")

        except yt_dlp.utils.DownloadError as e:
            self.error.emit(str(e))
            self.completed.emit(False, str(e))

    def _handle_playlist(self, config: DownloadConfig, ydl: yt_dlp.YoutubeDL, info: Dict[str, Any]):
        playlist_info = PlaylistInfo.from_dict(info)
        self._total_items = playlist_info.entry_count
        
        self.info.emit({
            'type': 'playlist',
            'title': playlist_info.title,
            'uploader': playlist_info.uploader,
            'total_entries': playlist_info.entry_count,
            'duration': sum(entry.get('duration', 0) for entry in playlist_info.entries if entry)
        })
        
        if config.create_playlist_folder:
            playlist_path = config.output_path / self._sanitize_filename(playlist_info.title)
            playlist_path.mkdir(parents=True, exist_ok=True)
            ydl_opts = ydl.params
            ydl_opts['outtmpl'] = str(playlist_path / '%(title)s.%(ext)s')
            self._ydl = yt_dlp.YoutubeDL(ydl_opts)

    def _handle_single_video(self, info: Dict[str, Any]):
        self.info.emit({
            'type': 'video',
            'title': info.get('title', ''),
            'duration': info.get('duration', 0),
            'uploader': info.get('uploader', '')
        })

    def _create_options(self, config: DownloadConfig) -> Dict[str, Any]:
        if config.playlist and config.create_playlist_folder:
            # Will be updated with playlist name after extraction
            output_template = str(config.output_path / '%(playlist_title)s' / '%(title)s.%(ext)s')
        else:
            output_template = str(config.output_path / '%(title)s.%(ext)s')
        
        ydl_opts = {
            'format': self._get_format_string(config),
            'outtmpl': output_template,
            'progress_hooks': [self._handle_progress],
            'merge_output_format': 'mp4',
            'writethumbnail': False,
            'writeinfojson': False,
            'retries': 5,
            'fragment_retries': 5,
            'ignoreerrors': True,
            'continuedl': True,
            'noprogress': True,
            'concurrent_fragment_downloads': 5,
            'http_chunk_size': 10485760
        }

        # Playlist specific options
        if config.playlist:
            if config.playlist_items:
                ydl_opts['playlist_items'] = config.playlist_items
            else:
                ydl_opts.update({
                    'playliststart': config.playlist_start,
                    'playlistend': config.playlist_end
                })

        if config.audio_only:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': config.audio_format,
                'preferredquality': config.audio_quality,
            }]

        return ydl_opts

    def _handle_progress(self, d: Dict[str, Any]):
        if not self._active:
            raise Exception("Download cancelled")
            
        if d['status'] == 'downloading':
            try:
                # Get total bytes accurately
                total_bytes = float(d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0))
                downloaded_bytes = float(d.get('downloaded_bytes', 0))
                
                # Calculate percentage
                if total_bytes > 0:
                    percent = (downloaded_bytes / total_bytes) * 100
                else:
                    percent = 0
                    
                # Get accurate speed
                speed = d.get('speed', 0)
                if isinstance(speed, str) or speed is None:
                    speed = 0
                    
                # Calculate estimated time
                eta = d.get('eta', 0)
                if eta is None:
                    eta = 0
                
                # Get download phase info
                fragment_info = ""
                if d.get('fragment_index') is not None:
                    fragment_info = f"Fragment: {d.get('fragment_index', 0)}/{d.get('fragment_count', 0)}"
                
                progress = {
                    'status': 'downloading',
                    'filename': d.get('filename', ''),
                    'percent': percent,
                    'speed': speed,
                    'eta': eta,
                    'total_bytes': total_bytes,
                    'downloaded_bytes': downloaded_bytes,
                    'fragment_info': fragment_info,
                    'phase': 'Downloading',
                }
                self.progress.emit(progress)
                
            except Exception as e:
                logger.error(f"Progress calculation error: {e}")
                
        elif d['status'] == 'finished':
            self.progress.emit({
                'status': 'processing',
                'filename': d.get('filename', ''),
                'percent': 100,
                'phase': 'Processing'
            })
        
        elif d['status'] == 'postprocessing':
            # Handle post-processing stages
            phase = d.get('postprocessor', 'Processing')
            self.progress.emit({
                'status': 'processing',
                'filename': d.get('filename', ''),
                'phase': f'Post-processing: {phase}'
            })

    def _create_progress_info(self, d: Dict[str, Any]) -> Dict[str, Any]:
        total_bytes = float(d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0))
        downloaded_bytes = float(d.get('downloaded_bytes', 0))
        
        if d.get('info_dict', {}).get('playlist_index'):
            self._current_item = d['info_dict']['playlist_index']
        
        return {
            'status': 'downloading',
            'filename': d.get('filename', ''),
            'percent': (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0,
            'speed': d.get('speed', 0),
            'eta': d.get('eta', 0),
            'total_bytes': total_bytes,
            'downloaded_bytes': downloaded_bytes,
            'playlist_index': self._current_item,
            'playlist_count': self._total_items
        }

    def _get_format_string(self, config: DownloadConfig) -> str:
        if config.audio_only:
            return 'bestaudio/best'
            
        quality_map = {
            'best': 'bestvideo+bestaudio/best',
            '2160p': 'bestvideo[height<=2160]+bestaudio/best',
            '1440p': 'bestvideo[height<=1440]+bestaudio/best',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best',
            '720p': 'bestvideo[height<=720]+bestaudio/best',
            '480p': 'bestvideo[height<=480]+bestaudio/best',
            '360p': 'bestvideo[height<=360]+bestaudio/best'
        }
        return quality_map.get(config.quality, 'bestvideo+bestaudio/best')

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '_', filename)

    def _cleanup(self):
        self._active = False
        self._ydl = None
        self._current_item = 0
        self._total_items = 0

    def cancel(self):
        self._active = False
        if self._ydl:
            try:
                self._ydl.stop_download()
            except:
                pass
            finally:
                self._ydl = None