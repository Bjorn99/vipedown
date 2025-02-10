.PHONY: build clean package install uninstall prepare

VERSION := $(shell grep "^version" pyproject.toml | cut -d'"' -f2)
DIST_NAME := vipedown-$(VERSION)

prepare:
	cd .. && tar -czf VipeDown/$(DIST_NAME).tar.gz \
		--transform 's,^VipeDown,$(DIST_NAME),' \
		VipeDown/vipedown \
		VipeDown/pyproject.toml \
		VipeDown/README.md \
		VipeDown/LICENSE \
		VipeDown/resources

build: prepare
	makepkg -f

clean:
	rm -rf dist/
	rm -rf *.tar.gz
	rm -rf pkg/
	rm -rf src/
	rm -f *.pkg.tar.zst

package: clean build

install: package
	sudo pacman -U vipedown-$(VERSION)-1-any.pkg.tar.zst

uninstall:
	sudo pacman -R vipedown

update-srcinfo:
	makepkg --printsrcinfo > .SRCINFO