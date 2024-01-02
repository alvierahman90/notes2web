#!/usr/bin/env python3
"""
notes2web --- view your notes as a static html site
"""


import argparse
import os
from pathlib import Path
import shutil
import sys
import pprint

import json

import frontmatter
import git
import jinja2
import requests

from fileproperties import FileMap


N2W_COMMIT = ""

PANDOC_SERVER_URL = os.getenv("PANDOC_SERVER_URL", r"http://localhost:3030/")
PANDOC_TIMEOUT = int(os.getenv("PANDOC_TIMEOUT", "120"))
CSS_DIR = Path(os.getenv("CSS_DIR", "/opt/notes2web/css"))
JS_DIR = Path(os.getenv("JS_DIR", "/opt/notes2web/js"))
TEMPLATES_DIR = Path(os.getenv("TEMPLATES_DIR", "/opt/notes2web/templates"))


JINJA_ENV = jinja2.Environment(
        loader=jinja2.PackageLoader("notes2web", str(TEMPLATES_DIR)),
        autoescape=jinja2.select_autoescape
        )

JINJA_TEMPLATES = {}
JINJA_TEMPLATE_TEXTARTICLE = JINJA_ENV.get_template("textarticle.html")
JINJA_TEMPLATE_HOME_INDEX = JINJA_ENV.get_template("home_index.html")
JINJA_TEMPLATE_DIRECTORY_INDEX = JINJA_ENV.get_template("index.html")
JINJA_TEMPLATE_ARTICLE = JINJA_ENV.get_template("article.html")


LICENSE = None
GIT_REPO = None
FILEMAP = None


def update_required(src_filepath, output_filepath):
    """
    check if file requires an update,
    return boolean
    """
    return not output_filepath.exists() or src_filepath.stat().st_mtime > output_filepath.stat().st_mtimeme()



def get_args():
    """ Get command line arguments """

    parser = argparse.ArgumentParser()
    parser.add_argument('notes', type=Path)
    parser.add_argument('-o', '--output-dir', type=Path, default='web')
    parser.add_argument('-F', '--force', action="store_true",
                help="Generate new output html even if source file was modified before output html")
    return parser.parse_args()


def render_markdown_file(input_filepath):
    """
    render markdown file to file
    write markdown file to args.output_dir in html,
    return list of tuple of output filepath, frontmatter post
    """
    print(f"render_markdown_file({input_filepath})")
    with open(input_filepath, encoding='utf-8') as file_pointer:
        content = frontmatter.load(file_pointer).content

    properties = FILEMAP.get(input_filepath)

    # TODO pandoc no longer handles template due to metadata passing issues, use jinja to fill in the metadata
    html = render_markdown(content)

    with open(properties['dst_path']['html'], 'w+', encoding='utf-8') as file_pointer:
        file_pointer.write(html)


def render_plaintext_file(input_filepath):
    """
    render plaintext file to file
    copy plaintext file into a html preview, copy raw to output dir
    return list of tuple of output filepath, empty dict
    """

    with open(input_filepath, encoding='utf-8') as file_pointer:
        raw_content = file_pointer.read()

    properties = FILEMAP.get(input_filepath)

    html = JINJA_TEMPLATE_TEXTARTICLE.render(license = LICENSE, **properties)

    with open(properties['dst_path']['raw'], "w+", encoding='utf-8') as file_pointer:
        file_pointer.write(raw_content)

    with open(properties['dst_path']['html'], "w+", encoding='utf-8') as file_pointer:
        file_pointer.write(html)


def render_generic_file(input_filepath):
    """
    render generic file to file
    copy generic file into to output_dir
    return list of tuple of output filepath, empty dict
    """
    properties = FILEMAP.get(input_filepath)
    output_filepath = properties['dst_path']['raw']
    shutil.copyfile(input_filepath, output_filepath)


def render_file(input_filepath):
    """
    render any file by detecting type and applying appropriate type
    write input_filepath to correct file in args.output_dir in appropriate formats,
    return list of tuples of output filepath, frontmatter post
    """

    if input_filepath.suffix == '.md':
        return render_markdown_file(input_filepath)

    if FileMap.is_plaintext(input_filepath):
        return render_plaintext_file(input_filepath)

    return render_generic_file(input_filepath)


def render_markdown(content):
    """
    render markdown to html
    """

    post_body = {
            'text': content,
            'toc-depth': 6,
            'highlight-style': 'pygments',
            'html-math-method': 'mathml',
            'to': 'html',
            'files': {
                'data/data/abbreviations': '',
                },
            'standalone': False,
            }

    headers = {
            'Accept': 'application/json'
            }

    response = requests.post(
            PANDOC_SERVER_URL,
            headers=headers,
            json=post_body,
            timeout=PANDOC_TIMEOUT
            )

    response = response.json()


    # TODO look at response['messages'] and log them maybe?
    # https://github.com/jgm/pandoc/blob/main/doc/pandoc-server.md#response

    return response['output']



def process_home_index(output_dir, search_data, notes_git_head_sha1=None):
    """
    create home index.html in output_dir
    """
    html = JINJA_TEMPLATE_HOME_INDEX.render(
            n2w_commit = N2W_COMMIT,
            search_data=search_data,
            notes_git_head_sha1=notes_git_head_sha1,
            )
    with open(output_dir.joinpath('index.html'), 'w+', encoding='utf-8') as file_pointer:
        file_pointer.write(html)


def generate_variable_browser(output_dir, posts, variable_name) :
    """
    generate a directory that lets you groub by and browse by any given tag. e.g. tags, authors
    """
    groups = {}

    for key, post in posts.iter():
        group_val = post.get(variable_name, None)
        if group_val is None:
            continue

        if group_val not in groups.keys():
            groups[group_val] = []

        groups[group_val].append(post)

    for group_val, index_entries in groups.iter():
        post = {
                'index_entries': index_entries,
                'title': group_val,
                }

    # TODO finish writing function, write page to disk



def main(args):
    """ Entry point for script """

    global LICENSE
    global GIT_REPO
    global FILEMAP

    FILEMAP = FileMap(args.notes, args.output_dir.joinpath('notes'))

    if args.output_dir.is_file():
        print(f"Output directory ({args.output_dir}) cannot be a file.")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # attempt to get licensing information
    license_path = args.notes.joinpath("LICENSE")
    if license_path.exists():
        with open(license_path, encoding='utf-8') as file_pointer:
            LICENSE = file_pointer.read()

    # create git.Repo object if notes dir is a git repo
    # TODO git commit log integration
    if '.git' in args.notes.iterdir():
        GIT_REPO = git.Repo(args.notes)

    for root_str, subdirectories, files in os.walk(args.notes):
        root = Path(root_str)
        if '.git' in root.parts:
            continue

        root_properties = FILEMAP.get(root)
        root_properties['dst_path']['raw'].mkdir(parents=True, exist_ok=True)

        pprint.pprint(root_properties)
        print(JINJA_TEMPLATE_DIRECTORY_INDEX)
        html = JINJA_TEMPLATE_DIRECTORY_INDEX.render(**root_properties)
        with open(root_properties['dst_path']['raw'].joinpath('index.html'), 'w+', encoding='utf-8') as file_pointer:
            file_pointer.write(html)

        # render each file
        for file in files:
            render_file(root.joinpath(file))


    process_home_index(args.output_dir, search_data=FILEMAP.to_list())

    # copy styling and js scripts necessary for function
    shutil.copytree(CSS_DIR, args.output_dir.joinpath('css'), dirs_exist_ok=True)
    shutil.copytree(JS_DIR, args.output_dir.joinpath('js'), dirs_exist_ok=True)



    return 0


# TODO implement useful logging and debug printing
# TODO build tag/metadata pages

if __name__ == '__main__':
    try:
        sys.exit(main(get_args()))
    except KeyboardInterrupt:
        sys.exit(0)
