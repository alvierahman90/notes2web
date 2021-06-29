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
$ notes2web.py NOTES_DIRECTORY_1
```

Output of `notes2web.py --help`:

```
usage: notes2web.py [-h] [-o OUTPUT_DIR] [-t TEMPLATE] [-H TEMPLATE_TEXT_HEAD]
                    [-f TEMPLATE_TEXT_FOOT] [-i TEMPLATE_INDEX_HEAD]
                    [-I TEMPLATE_INDEX_FOOT] [-s STYLESHEET]
                    [-e EXTRA_INDEX_CONTENT]
                    notes

positional arguments:
  notes

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
  -t TEMPLATE, --template TEMPLATE
  -H TEMPLATE_TEXT_HEAD, --template-text-head TEMPLATE_TEXT_HEAD
  -f TEMPLATE_TEXT_FOOT, --template-text-foot TEMPLATE_TEXT_FOOT
  -i TEMPLATE_INDEX_HEAD, --template-index-head TEMPLATE_INDEX_HEAD
  -I TEMPLATE_INDEX_FOOT, --template-index-foot TEMPLATE_INDEX_FOOT
  -s STYLESHEET, --stylesheet STYLESHEET
  -e EXTRA_INDEX_CONTENT, --extra-index-content EXTRA_INDEX_CONTENT
```

The command will generate a website in the `output-dir` directory (`./web` by default).
It will then generate a list of all note files and put it in `index.html`.

Then you just have to point a webserver at `output-dir`.

## Uninstall

```
# make uninstall
```
