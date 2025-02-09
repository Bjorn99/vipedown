# vipedown

A modern, feature-rich graphical user interface for yt-dlp, built with PyQt6. This application provides an intuitive way to download videos and audio from various platforms with advanced configuration options.

## Features

### Core Functionality
- Download videos and audio from YouTube and other supported platforms
- Support for both single videos and playlists
- Clean, modern interface with theme support (Light, Dark, and Nord themes)
- System tray integration with download notifications
- Progress tracking with detailed information

### Video Features
- Multiple quality options:
  - Maximum Quality (8K/4K)
  - Ultra HD (2160p)
  - Quad HD (1440p)
  - Full HD (1080p)
  - HD (720p)
  - SD (480p)
  - Low (360p)
- Codec preferences (AV1, VP9)
- Thumbnail embedding
- Chapter markers support
- Subtitle download and conversion

### Audio Features
- Multiple format options:
  - FLAC (Lossless)
  - WAV (Lossless)
  - OPUS (High Quality)
  - M4A (AAC)
  - MP3 (multiple bitrates: 320k, 256k, 192k, 128k)
- Audio normalization
- Chapter-based splitting
- Metadata embedding
- Thumbnail embedding

### Advanced Features
- Concurrent download support
- Download speed limiting
- Proxy support
- Debug logging
- Custom output templates
- Playlist range selection
- Extensive configuration options

## Installation

### Prerequisites for Arch Linux
1. Install Python and base development tools:
```bash
sudo pacman -S python python-pip git base-devel
```

2. Install FFmpeg (required for media processing):
```bash
sudo pacman -S ffmpeg
```

3. Install Poetry (Python dependency manager):
```bash
# Install poetry using the official installer
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to your PATH (for fish shell)
set -U fish_user_paths $fish_user_paths $HOME/.local/bin

# For bash/zsh, add this to your ~/.bashrc or ~/.zshrc:
# export PATH="$HOME/.local/bin:$PATH"
```

### Installing the Application

1. Clone the repository:
```bash
git clone https://github.com/Bjorn99/ytdl-gui.git
cd ytdl-gui
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Run the application:
```bash
poetry run ytdl-gui
```

### Optional: Creating a Desktop Entry
Create a desktop entry for easy access:

1. Create a new `.desktop` file:
```bash
sudo nano /usr/share/applications/ytdl-gui.desktop
```

2. Add the following content (adjust paths as needed):
```ini
[Desktop Entry]
Name=YT-DLP GUI
Comment=Modern YouTube Downloader
Exec=/path/to/poetry/bin/poetry run ytdl-gui
Icon=video-display
Terminal=false
Type=Application
Categories=AudioVideo;Network;
```

## Usage

### Basic Usage
1. Launch the application
2. Paste a video URL into the URL field
3. Select desired format (video/audio) and quality
4. Choose download location (optional)
5. Click "Start Download"

### Advanced Configuration
The settings dialog (⚙️) provides access to advanced options:

#### General Settings
- Default save location
- Update preferences
- Interface options
- Notification settings

#### Video Settings
- Default quality presets
- Codec preferences
- Video processing options
- Thumbnail and metadata options

#### Audio Settings
- Default format and quality
- Audio processing options
- Normalization settings
- Chapter splitting options

#### Advanced Settings
- Concurrent download limits
- Network settings
- Proxy configuration
- Debug options

## Troubleshooting

### Common Issues

1. **Download fails with format error**
   - Try a different quality setting
   - Check if the video is available in the selected quality
   - Verify your internet connection

2. **Audio conversion fails**
   - Ensure FFmpeg is properly installed
   - Check write permissions in the output directory
   - Verify the selected audio format is supported

3. **Application won't start**
   - Verify all dependencies are installed
   - Check Python version compatibility
   - Ensure Poetry environment is properly configured

### Debug Logging

To enable debug logging:
1. Open Settings (⚙️)
2. Go to Advanced tab
3. Enable "Write debug log"
4. Select log location
5. Restart the application

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for the core downloading functionality
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the GUI framework
- All contributors and users of the application
