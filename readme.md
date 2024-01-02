# gronk

View your notes as a static html site. Browse a live sample of it [here](https://notes.alv.cx).

![](./screenshot.png)

Tested with [pandoc v2.19.2](https://github.com/jgm/pandoc/releases/tag/2.19.2).


## Why?

- View notes as a website, on any device
- Write notes with Pandoc markdown
- Easily share notes
- Lightweight HTML generated
- Minimal JavaScript


## Install

0. Install [Pandoc](https://pandoc.org/index.html) and [Pip](https://github.com/pypa/pip), python3-dev, and a C compiler
1. Run `make install` as root

## Other Things to Know

- gronk indexes [ATX-style headings](https://pandoc.org/MANUAL.html#atx-style-headings) for
  searching
- gronk looks for the plaintext file `LICENSE` in the root directory of your notes


## Custom Directory Index

To add custom content to a directory index, put it in a file called `index.md` under the directory.

You can set the following frontmatter variables to customise the directory index of a directory:

| variable               | default value     | description                                                                                |
|------------------------|-------------------|--------------------------------------------------------------------------------------------|
| `tags`                 | `[]`              | list of tags, used by search and inherited by any notes and subdirectories                 |
| `uuid`                 | none              | unique id to reference directory, used for permalinking                                    |
| `content_after_search` | `false`           | show custom content in `index.md` after search bar and directory index                     |
| `automatic_index`      | `true`            | show the automatically generated directory index. required for search bar to function.     |
| `search_bar`           | `true`            | show search bar to search directory items. requires `automatic_index` (enabled by default) |


## Notes Metadata

gronk reads the following YAML [frontmatter](https://jekyllrb.com/docs/front-matter/) variables for metadata:

| variable         | description                                                                           |
|------------------|---------------------------------------------------------------------------------------|
| `author`         | The person(s) who wrote the article                                                   |
| `tags`           | A YAML list of tags which the article relates to - this is used for browsing and also |
| `title`          | The title of the article                                                              |
| `uuid`           | A unique identifier used for permalinks.                                              |
| `lecture_slides` | a list of paths pointing to lecture slides used while taking notes                    |
| `lecture_notes`  | a list of paths pointing to other notes used while taking notes                       |

## Permalinks

Permalinks are currently rather basic and requires JavaScript to be enabled on the local computer.
In order to identify documents between file changes, a unique identifier is used to identify a file.

This unique identifier can be generated using the `uuidgen` command in the `uuid-runtime` package or
`str(uuid.uuid())` in the `uuid` python package.

The included `n2w_add_uuid.py` will add a UUID to a markdown file which does not have a UUID in it
already.
Combine it with `find` to UUIDify all your markdown files (but make a backup first).

## Custom Styling

To completely replace the existing styling, set the environment variable `GRONK_CSS_DIR` to another directory with
a file called `styles.css`.

To add additional styling, the default styling will attempt to import `styles.css` from the root of the notes
directory.

To add additional content to the homepage, create a file called `index.md` at the top level of your notes directory.
To set the HTML `title` tag, set `title` in the frontmatter of `index.md`:

```markdown
---
title: "alv's notes"
---

# alv's notes

these notes are probably wrong
```

## CLI Usage

```
$ gronk.py notes_directory
```

Output of `gronk.py --help`:

TODO add cli output

The command will generate a website in the `output-dir` directory (`./web` by default).
It will then generate a list of all note files and put it in `index.html`.

Then you just have to point a webserver at `output-dir`.

## Uninstall

```
# make uninstall
```

## Acknowledgements

Default synatx highlighting is based off [Pygments](https://pygments.org/)' default theme and
made using Pandoc v2.7.2.
I found the theme [here](https://github.com/tajmone/pandoc-goodies/blob/master/skylighting/css/built-in-styles/pygments.css).

Pretty sure the link colours are taken from [thebestmotherfucking.website](https://thebestmotherfucking.website/).
