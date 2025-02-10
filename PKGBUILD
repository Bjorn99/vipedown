# Maintainer: Bjorn99 <67769176+Bjorn99@users.noreply.github.com>
pkgname=vipedown
pkgver=0.1.1
pkgrel=1
pkgdesc="Fast and efficient video downloader for Linux"
arch=('any')
url="https://github.com/Bjorn99/vipedown"
license=('MIT')
depends=(
    'python>=3.10'
    'python-pyqt6'
    'ffmpeg'
    'yt-dlp'
    'python-pip'
)
makedepends=(
    'python-build'
    'python-installer'
    'python-wheel'
    'python-poetry'
)
provides=('vipedown')
options=(!strip)
source=("$pkgname-$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
    cd "$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$pkgname-$pkgver"
    
    python -m installer --destdir="$pkgdir" dist/*.whl
    
    # Create bin directory and install executable
    install -Dm755 -d "$pkgdir/usr/bin"
    echo '#!/bin/sh' > "$pkgdir/usr/bin/vipedown"
    echo 'exec python -m vipedown "$@"' >> "$pkgdir/usr/bin/vipedown"
    chmod 755 "$pkgdir/usr/bin/vipedown"
    
    # Install desktop file
    install -Dm644 "resources/vipedown.desktop" "$pkgdir/usr/share/applications/vipedown.desktop"
    
    # Install icon
    install -Dm644 "resources/vipedown.png" "$pkgdir/usr/share/icons/hicolor/256x256/apps/vipedown.png"
    
    # Install license
    install -Dm644 "LICENSE" "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
