import sys
import time
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

from PyQt6.QtCore import QThread, pyqtSignal, QSettings
import yt_dlp

@dataclass
class DownloadConfig:
    """Configuration for video/audio downloads"""
    url: str
    save_path: Path
    format_type: str  # 'video' or 'audio'
    quality: str
    playlist: bool = False
    start_index: int = 1
    end_index: Optional[int] = None
    subtitle_langs: List[str] = None
    convert_subs_format: str = None
    thumbnail: bool = False
    metadata: bool = True

class EnhancedDownloadWorker(QThread):
    progress_signal = pyqtSignal(dict)
    download_complete = pyqtSignal(bool, str)
    playlist_info_signal = pyqtSignal(dict)

    def __init__(self, config: DownloadConfig, settings: QSettings):
        super().__init__()
        self.config = config
        self.settings = settings
        self.is_cancelled = False
        self._current_download = None

    def run(self):
        try:
            # Create organized output directory structure
            base_path = self.config.save_path
            if self.config.format_type == 'video':
                base_path = base_path / 'Videos'
            else:
                base_path = base_path / 'Audio'
            
            output_template = str(base_path / '%(title)s/%(title)s-%(id)s.%(ext)s')
            
            # Initialize postprocessors list
            postprocessors = []
            
            # Configure advanced yt-dlp options
            ydl_opts = {
                'outtmpl': output_template,
                'progress_hooks': [self.progress_hook],
                'restrictfilenames': True,
                'ignoreerrors': self.settings.value('ignore_errors', True, type=bool),
                'extract_flat': True if self.config.playlist else False,
                'playliststart': self.config.start_index,
                'playlistend': self.config.end_index,
                'writethumbnail': self.config.thumbnail,
                'writeinfojson': self.config.metadata,
                'retries': self.settings.value('retry_attempts', 3, type=int),
                'verbose': self.settings.value('verbose_output', False, type=bool),
                'quiet': not self.settings.value('verbose_output', False, type=bool),
                'postprocessors': postprocessors  # Initialize empty list here
            }

            # Configure proxy if enabled
            if self.settings.value('use_proxy', False, type=bool):
                proxy_url = self.settings.value('proxy_url', '')
                if proxy_url:
                    ydl_opts['proxy'] = proxy_url

            # Configure rate limiting
            speed_limit = self.settings.value('limit_speed', 0, type=int)
            if speed_limit > 0:
                ydl_opts['ratelimit'] = speed_limit * 1024  # Convert to bytes/s

            # Configure format selection
            if self.config.format_type == 'video':
                ydl_opts['format'] = self._get_video_format()
                
                # Handle thumbnails and metadata
                if self.settings.value('embed_thumbnail', True, type=bool):
                    postprocessors.append({
                        'key': 'EmbedThumbnail',
                        'already_have_thumbnail': False
                    })
                
                if self.settings.value('embed_chapters', True, type=bool):
                    postprocessors.append({
                        'key': 'FFmpegMetadata',
                        'add_chapters': True
                    })
            else:
                ydl_opts['format'] = 'bestaudio/best'
                # Add audio postprocessors
                audio_pp = self._get_audio_postprocessors()
                postprocessors.extend(audio_pp)

            # Add subtitle handling
            if self.config.subtitle_langs:
                ydl_opts.update({
                    'writesubtitles': True,
                    'subtitleslangs': self.config.subtitle_langs,
                })
                if self.config.convert_subs_format:
                    postprocessors.append({
                        'key': 'FFmpegSubtitlesConvertor',
                        'format': self.config.convert_subs_format
                    })

            # Create output directory
            base_path.mkdir(parents=True, exist_ok=True)

            # Configure debug logging
            if self.settings.value('write_debug_log', False, type=bool):
                debug_location = Path(self.settings.value('debug_location', ''))
                if debug_location.exists():
                    ydl_opts['logger'] = self._setup_logger(debug_location)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract playlist information if needed
                if self.config.playlist:
                    info = ydl.extract_info(self.config.url, download=False)
                    if info.get('_type') == 'playlist':
                        self.playlist_info_signal.emit({
                            'title': info.get('title', 'Unknown Playlist'),
                            'total_entries': info.get('playlist_count', 0)
                        })

                # Perform download
                self._current_download = ydl
                ydl.download([self.config.url])

            self.download_complete.emit(True, "Download completed successfully!")
            
        except Exception as e:
            self.download_complete.emit(False, f"Download error: {str(e)}")
            
    def get_selected_quality(self) -> str:
        """Get selected quality setting"""
        quality_text = self.quality_combo.currentText()
        if self.video_radio.isChecked():
            quality_map = {
                'Maximum Quality (8K/4K)': 'bestvideo+bestaudio/best',
                'Ultra HD (2160p)': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
                'Quad HD (1440p)': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
                'Full HD (1080p)': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                'HD (720p)': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                'SD (480p)': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
                'Low (360p)': 'bestvideo[height<=360]+bestaudio/best[height<=360]'
            }
            return quality_map.get(quality_text, 'bestvideo+bestaudio/best')
        else:
            return quality_text.split('(')[0].strip().lower()  # Get format name (FLAC, WAV, etc.)

    def _get_video_format(self) -> str:
        """Get video format string based on quality settings"""
        quality = self.config.quality
        quality_map = {
            'Maximum Quality (8K/4K)': self._get_max_quality_format(),
            'Ultra HD (2160p)': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
            'Quad HD (1440p)': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
            'Full HD (1080p)': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            'HD (720p)': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'SD (480p)': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            'Low (360p)': 'bestvideo[height<=360]+bestaudio/best[height<=360]'
        }

        format_str = quality_map.get(quality, quality_map['Full HD (1080p)'])

        # Add codec preferences
        if self.settings.value('prefer_av1', False, type=bool):
            format_str = format_str.replace('bestvideo', 'bestvideo[vcodec^=av01]')
        elif self.settings.value('prefer_vp9', False, type=bool):
            format_str = format_str.replace('bestvideo', 'bestvideo[vcodec^=vp9]')

        return format_str

    def _get_max_quality_format(self) -> str:
        """Generate format string for maximum quality"""
        # For selecting the best quality available regardless of codec
        base_format = 'bestvideo+bestaudio/best'
        
        # Add codec preferences if set
        if self.settings.value('prefer_av1', False, type=bool):
            return f'bestvideo[vcodec^=av01]+bestaudio/bestvideo+bestaudio/best'
        elif self.settings.value('prefer_vp9', False, type=bool):
            return f'bestvideo[vcodec^=vp9]+bestaudio/bestvideo+bestaudio/best'
            
        return base_format

    def _get_audio_postprocessors(self) -> list:
        """Configure audio post-processing"""
        pp_list = []
        
        # Audio format conversion
        format_text = self.config.quality.lower()
        
        # Base audio extraction postprocessor
        audio_pp = {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format_text.split()[0],  # Get the format (flac, wav, opus, etc.)
        }
        
        # Add quality settings for lossy formats
        if 'mp3' in format_text:
            # Extract bitrate from format string (e.g., "320" from "MP3 (320kbps)")
            bitrate = ''.join(filter(str.isdigit, format_text))
            audio_pp['preferredquality'] = bitrate
        elif 'opus' in format_text or 'm4a' in format_text:
            audio_pp['preferredquality'] = '192'
            
        pp_list.append(audio_pp)

        # Add metadata if enabled
        if self.settings.value('add_metadata', True, type=bool):
            pp_list.append({'key': 'FFmpegMetadata'})
        
        # Add thumbnail embedding if enabled
        if self.settings.value('extract_thumbnail', True, type=bool):
            pp_list.append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False
            })
        
        # Add audio normalization if enabled
        if self.settings.value('normalize_audio', False, type=bool):
            pp_list.append({'key': 'FFmpegNormalize'})

        return pp_list

    def _setup_logger(self, debug_location: Path):
        """Setup debug logging"""
        import logging
        logger = logging.getLogger('yt-dlp')
        logger.setLevel(logging.DEBUG)
        
        fh = logging.FileHandler(
            debug_location / f'ytdl_debug_{int(time.time())}.log'
        )
        fh.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger

    def progress_hook(self, d: dict):
        """Enhanced progress tracking"""
        if self.is_cancelled:
            raise Exception("Download cancelled by user")
            
        if d['status'] == 'downloading':
            progress = {
                'status': 'downloading',
                'filename': d.get('filename', ''),
                'percent': d.get('_percent_str', 'N/A'),
                'speed': f"{d.get('speed', 0)/1024/1024:.1f} MB/s" if d.get('speed') else "N/A",
                'eta': d.get('_eta_str', 'N/A'),
                'total_bytes': d.get('total_bytes', 0),
                'downloaded_bytes': d.get('downloaded_bytes', 0),
                'video_format': d.get('format_note', ''),
                'video_codec': d.get('vcodec', 'N/A'),
                'audio_codec': d.get('acodec', 'N/A')
            }
            self.progress_signal.emit(progress)
        elif d['status'] == 'finished':
            progress = {
                'status': 'processing',
                'filename': d.get('filename', '')
            }
            self.progress_signal.emit(progress)

    def cancel(self):
        """Cancel ongoing download"""
        self.is_cancelled = True
        if self._current_download:
            self._current_download.stop_download()