# notes2web

View your notes as a static html site.

![](./screenshot.png)

## Install

0. Install [Pandoc](https://pandoc.org/index.html) and [yq](https://github.com/mikefarah/yq)

   On arch:
   ```
   # pacman -S pandoc yq
   ```

1. Run `make install` as root

## Usage

```
$ notes2web NOTES_DIRECTORY_1 [NOTES_DIRECTORY_2 [...]]
```

The command will generate and place html files in your notes directory.
It will then generate a list of all note files and put it in `index.html` in the
root directory.

Then you just have to point a webserver at your notes directory.

## Config

`notes2web` looks for a config file called `.notes2web.conf` in your current directory and your home
directory.
Default config values:

```bash
name=""
article_template="/opt/notes2web/templates/article.html"
listitem_template="/opt/notes2web/templates/listitem.html"
index_template="/opt/notes2web/templates/index.html"
stylesheet="/opt/notes2web/styles.css"
```

If the name is not set, the title is set to 'notes'.

## Uninstall

```
# make uninstall
```
