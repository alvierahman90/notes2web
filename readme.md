# notes2web

View your notes as a static html site.

## Install

0. Install [Pandoc](https://pandoc.org/index.html)
1. Run `make install` as root

## Usage

```
notes2web NOTES_DIRECTORY_1 [NOTES_DIRECTORY_2 [...]]
```

The command will generate and place html files in your notes directory.
It will then generate a list of all note files and put it in `index.html` in the
root directory.

Then you just have to point a webserver at your notes directory.

## Uninstall

```
# make uninstall
```
