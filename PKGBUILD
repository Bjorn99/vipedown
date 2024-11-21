# Maintainer: Your Name <your-email@example.com>

pkgname=ytdl-gui
pkgver=0.1.0
pkgrel=1
pkgdesc="A modern graphical user interface for yt-dlp"
arch=('any')
url="https://github.com/Bjorn99/ytdl-gui"
license=('MIT')
depends=(
    'python'
    'python-pyqt6'
    'python-yt-dlp'
    'python-slugify'
    'python-validators'
)
makedepends=(
    'python-poetry'
    'python-build'
    'python-installer'
    'python-wheel'
)
source=("$pkgname-$pkgver.tar.gz::$url/archive/v$pkgver.tar.gz")
sha256sums=('bac8792ac97e0701c2314e17c041061e1eedc363101605ee80a8d242e11d96ef' '56ba47c97150fafa4dd65e46fb168a1bc74eda7ae9c6924bf5e9d725c6cec1d7' 'c2c59285c2746d19da2179ea5839e31b9be0afd5852acf2f6047c7f36c404ad7')  # Replace with actual checksum after first build

package() {
    cd "$srcdir/$pkgname-$pkgver"
    
    # Use poetry to build and install
    poetry build -f wheel
    python -m installer --destdir="$pkgdir" dist/*.whl

    # Install LICENSE
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"

    # Install desktop entry
    install -Dm644 ytdl-gui.desktop "$pkgdir/usr/share/applications/ytdl-gui.desktop"

    # Install icon
    install -Dm644 icon.png "$pkgdir/usr/share/pixmaps/ytdl-gui.png"
}