_list:
  @just --list

build: _deps _make

_make:
  cd src && python3 game-icons.py

_deps:
  if [ -e gameicons-font ]; then cd gameicons-font && git reset --hard HEAD && git pull; fi
  if [ ! -e gameicons-font ]; then git clone --depth 1 https://github.com/seiyria/gameicons-font.git; fi
  cd gameicons-font && sed -i.bak 's|startCodepoint: 0xF000|startCodepoint: 0xa000|g' download-and-format-icons.js
  cd gameicons-font && npm upgrade && npm install
  cd gameicons-font && npm run build:font
  cp gameicons-font/dist/game-icons.css ./src
  cp gameicons-font/dist/game-icons.ttf .
