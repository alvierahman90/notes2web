#!/usr/bin/env python3


from bs4 import BeautifulSoup as bs
import magic
import sys
import pathlib
import pypandoc
import shutil
import os
import re

TEXT_ARTICLE_TEMPLATE_FOOT = None
TEXT_ARTICLE_TEMPLATE_HEAD = None
INDEX_TEMPLATE_FOOT = None
INDEX_TEMPLATE_HEAD = None
EXTRA_INDEX_CONTENT = None

def get_files(folder):
    markdown = []
    plaintext = []
    other = []

    for root, folders, files in os.walk(folder):
        for filename in files:
            name = os.path.join(root, filename)
            if os.path.splitext(name)[1] == '.md':
                markdown.append(name)
            elif re.match(r'^text/', magic.from_file(name, mime=True)):
                plaintext.append(name)
                other.append(name)
            else:
                other.append(name)

    return markdown, plaintext, other

def get_dirs(folder):
    r = []

    for root, folders, files in os.walk(folder):
        [r.append(os.path.join(root, folder)) for folder in folders]

    return r


def get_args():
    """ Get command line arguments """

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('notes', type=pathlib.Path)
    parser.add_argument('-o', '--output-dir', type=pathlib.Path, default='web')
    parser.add_argument('-t', '--template', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/templates/article.html'))
    parser.add_argument('-H', '--template-text-head', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/templates/textarticlehead.html'))
    parser.add_argument('-f', '--template-text-foot', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/templates/textarticlefoot.html'))
    parser.add_argument('-i', '--template-index-head', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/templates/indexhead.html'))
    parser.add_argument('-I', '--template-index-foot', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/templates/indexfoot.html'))
    parser.add_argument('-s', '--stylesheet', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/styles.css'))
    parser.add_argument('-e', '--extra-index-content', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/templates/extra_index_content.html'))
    return parser.parse_args()


def main(args):
    """ Entry point for script """

    with open(args.template_text_foot) as fp:
        TEXT_ARTICLE_TEMPLATE_FOOT = fp.read()

    with open(args.template_text_head) as fp:
        TEXT_ARTICLE_TEMPLATE_HEAD = fp.read()

    with open(args.template_index_foot) as fp:
        INDEX_TEMPLATE_FOOT = fp.read()

    with open(args.template_index_head) as fp:
        INDEX_TEMPLATE_HEAD = fp.read()

    with open(args.extra_index_content) as fp:
        EXTRA_INDEX_CONTENT = fp.read()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir, exist_ok=True)

    if os.path.isfile(args.output_dir):
        print("Output directory ({output_dir}) cannot be a file.")


    markdown_files, plaintext_files, other_files = get_files(args.notes)

    print(f"{markdown_files=}")
    for filename in markdown_files:
        html = pypandoc.convert_file(filename, 'html', extra_args=[f'--template={args.template}'])
        output_filename = os.path.splitext(re.sub(f"^{args.notes.name}", args.output_dir.name, filename))[0] + '.html'
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)

        with open(output_filename, 'w+') as fp:
            fp.write(html)

    print(f"{plaintext_files=}")
    for filename in plaintext_files:
        output_filename = re.sub(f"^{args.notes.name}", args.output_dir.name, filename) + '.html'
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        title = os.path.basename(output_filename)
        html = re.sub(r'\$title\$', title, TEXT_ARTICLE_TEMPLATE_HEAD)
        html = re.sub(r'\$raw\$', os.path.basename(filename), html)
        with open(filename) as fp:
            html += fp.read()
        html += TEXT_ARTICLE_TEMPLATE_FOOT

        with open(output_filename, 'w+') as fp:
            fp.write(html)

    print(f"{other_files=}")
    for filename in other_files:
        output_filename = re.sub(f"^{args.notes.name}", args.output_dir.name, filename)
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        shutil.copyfile(filename, output_filename)


    dirs_to_index = [args.output_dir.name] + get_dirs(args.output_dir)
    print(f"{dirs_to_index=}")
    print(f"{os.path.commonpath(dirs_to_index)=}")

    for directory in dirs_to_index:
        paths = os.listdir(directory)
        print(f"{paths=}")

        indexentries = []
        
        for path in paths:
            if path == 'index.html':
                continue

            fullpath = os.path.join(directory, path)
            if os.path.splitext(path)[1] == '.html':
                with open(fullpath) as fp:
                    soup = bs(fp.read(), 'html.parser')

                try:
                    title = soup.find('title').get_text()
                except AttributeError:
                    title = path
            else:
                title = path

            if title.strip() == '':
                title = path

            indexentries.append({
                'title': title,
                'path': path,
                'isdirectory': os.path.isdir(fullpath)
                })

        indexentries.sort(key=lambda entry: entry['title'])
        indexentries.sort(key=lambda entry: entry['isdirectory'], reverse=True)
        
        html = re.sub(r'\$title\$', directory, INDEX_TEMPLATE_HEAD)
        html = re.sub(r'\$extra_content\$',
                EXTRA_INDEX_CONTENT if directory == os.path.commonpath(dirs_to_index) else '',
                html
                )

        for entry in indexentries:
            html += f"<div class=\"article\"><a href=\"{entry['path']}\">{entry['title']}{'/' if entry['isdirectory'] else ''}</a></div>"
        html += INDEX_TEMPLATE_FOOT

        with open(os.path.join(directory, 'index.html'), 'w+') as fp:
            fp.write(html)

    shutil.copyfile(args.stylesheet, os.path.join(args.output_dir.name, 'styles.css'))

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(get_args()))
    except KeyboardInterrupt:
        sys.exit(0)
