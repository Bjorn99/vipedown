# VipeDown

A fast, efficient video downloader for Linux systems built with PyQt6. VipeDown emphasizes functionality over aesthetics, providing a reliable way to download videos and audio from various platforms.

## Features

### Download Management
- Queue system for multiple downloads
- Progress tracking with real-time speed and ETA
- Format selection (video/audio)
- Quality options from 360p to 2160p
- Playlist handling with selective download options

### Interface Elements
- URL input with paste functionality
- Format and quality selection dropdowns
- Progress indicators showing:
  - Download speed in MB/s or KB/s
  - Estimated time remaining
  - File size and completion percentage
  - Current download phase
- Queue management panel
- System tray integration with notifications

## Installation

VipeDown can be installed and used in two ways: as a system package or in development mode.

### System Installation (Arch Linux)

1. Install system dependencies:
```bash
sudo pacman -S base-devel git python python-pip ffmpeg
```

2. Clone and build:
```bash
git clone https://github.com/Bjorn99/vipedown.git
cd vipedown
make clean
make package
sudo pacman -U vipedown-0.1.0-1-any.pkg.tar.zst
```

3. Run:
```bash
vipedown
```

### Development Installation

1. Install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -

# Fish shell
set -U fish_user_paths $HOME/.local/bin $fish_user_paths

# Bash/Zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc  # or ~/.zshrc
source ~/.bashrc  # or ~/.zshrc
```

2. Clone and set up:
```bash
git clone https://github.com/Bjorn99/vipedown.git
cd vipedown
poetry install
```

3. Run in development mode:
```bash
poetry run vipedown
```

## Development vs Production Usage

### Development Mode
Use Poetry when developing:
```bash
# Activate development environment
poetry shell

# Run application
poetry run vipedown

# Add dependencies
poetry add package-name

# Update dependencies
poetry update
```

### Production Mode
Use system installation for regular use:
```bash
# Install system-wide
sudo pacman -U vipedown-*.pkg.tar.zst

# Run application
vipedown
```

## Environment Management

### Poetry Environments
- Poetry creates isolated virtual environments for each project
- Environments are stored in `~/.cache/pypoetry/virtualenvs/`
- Useful commands:
  ```bash
  # List environments
  poetry env list
  
  # Remove environments
  poetry env remove --all
  
  # Create new environment
  poetry env use python3.13
  ```

### Switching Between Modes
When switching from development to system installation:
1. Exit Poetry shell if active
2. Remove Poetry environments:
   ```bash
   poetry env remove --all
   rm -rf $HOME/.cache/pypoetry/virtualenvs/vipedown-*
   ```
3. Rebuild and install system package

## Usage Guide

### Basic Download
1. Launch VipeDown
2. Paste video URL
3. Select format (video/audio)
4. Choose quality
5. Click "Add to Queue"
6. Start the queue

### Playlist Downloads
1. Enter playlist URL
2. Enable "Download as Playlist"
3. Choose range (start/end) or specific videos
4. Select format and quality
5. Add to queue

### Queue Management
- Add multiple items to queue
- Remove items (right-click)
- Cancel ongoing downloads
- Monitor progress in real-time

## Troubleshooting

### Installation Issues
1. Poetry environment conflicts:
   ```bash
   poetry env remove --all
   rm -rf $HOME/.cache/pypoetry/virtualenvs/vipedown-*
   ```

2. Package conflicts:
   ```bash
   make clean
   make package
   ```

### Running Issues
1. Check dependencies:
   ```bash
   python --version  # Should be 3.10 or higher
   ffmpeg -version
   ```

2. Verify installation:
   ```bash
   which vipedown
   ```

## Contributing

1. Fork repository
2. Create feature branch
3. Set up development environment:
   ```bash
   poetry install
   poetry shell
   ```
4. Make changes and test
5. Submit pull request

## License
MIT License