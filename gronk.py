#!/usr/bin/env python3
"""
gronk --- view your notes as a static html site
"""

import argparse
import os
from pathlib import Path
import shutil
import sys
import subprocess
import copy
import time
import magic
import regex as re
import pprint

import frontmatter
import jinja2
import requests

GRONK_COMMIT = "dev"

PANDOC_SERVER_URL = os.getenv("PANDOC_SERVER_URL", r"http://localhost:3030/")
PANDOC_TIMEOUT = int(os.getenv("PANDOC_TIMEOUT", "120"))
GRONK_CSS_DIR = Path(os.getenv("GRONK_CSS_DIR", "/opt/gronk/css"))
GRONK_JS_DIR = Path(os.getenv("GRONK_JS_DIR", "/opt/gronk/js"))
GRONK_TEMPLATES_DIR = Path(
    os.getenv("GRONK_TEMPLATES_DIR", "/opt/gronk/templates/"))

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath=GRONK_TEMPLATES_DIR),
    autoescape=jinja2.select_autoescape)

JINJA_TEMPLATE_TEXTARTICLE = JINJA_ENV.get_template("article-text.html")
JINJA_TEMPLATE_HOME_INDEX = JINJA_ENV.get_template("home.html")
JINJA_TEMPLATE_INDEX = JINJA_ENV.get_template("index.html")
JINJA_TEMPLATE_ARTICLE = JINJA_ENV.get_template("article.html")
JINJA_TEMPLATE_PERMALINK = JINJA_ENV.get_template("permalink.html")

LICENSE = None
FILEMAP = None


class FileMap:
    """
    this class is used to read file properties, inherit properties,
    and have a centralised place to access them
    """

    def __init__(self, input_dir, output_dir):
        self._map = {}
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

    @staticmethod
    def _path_to_key(path):
        return str(path)

    @staticmethod
    def is_plaintext(filename):
        return re.match(r'^text/', magic.from_file(str(filename),
                                                   mime=True)) is not None

    def add(self, filepath):
        filepath = Path(filepath)
        if filepath.is_dir():
            properties = self._get_directory_properties(filepath)
        else:
            properties = self._get_file_properties(filepath)

        properties['src_path'] = filepath
        properties['dst_path'] = self._get_output_filepath(filepath)

        self._map[self._path_to_key(filepath)] = properties

    def get(self, filepath, default=None, raw=False):
        """
        get the properties of a file at a filepath
        raw=True to not inherit properties
        """
        # TODO maybe store properties of a file once it's in built and mark it
        # as built? might save time but also cba
        if self._path_to_key(filepath) not in self._map.keys():
            self.add(filepath)

        properties = copy.deepcopy(
            self._map.get(self._path_to_key(filepath), default))

        if raw:
            return properties

        parent = filepath
        while True:
            parent = parent.parent
            if parent == Path('.'):
                break

            parent_properties = self.get(parent, raw=True)
            # TODO inherit any property that isn't defined, append any lists
            # that exist
            properties['tags'] = properties.get(
                'tags', []) + parent_properties.get('tags', [])

            if parent == self.input_dir:
                break

        return properties

    def _get_directory_properties(self,
                                  filepath: Path,
                                  include_index_entries=True):
        post = {
            'title': filepath.name,
            'content_after_search': False,
            'automatic_index': True,
            'search_bar': True,
            'tags': [],
        }

        if 'readme.md' in [f.name for f in filepath.iterdir()]:
            with open(filepath.joinpath('readme.md'),
                      encoding='utf-8') as file_pointer:
                for key, val in frontmatter.load(
                        file_pointer).to_dict().items():
                    post[key] = val

        if 'content' in post.keys():
            post['content'] = render_markdown(post['content'])

        post['is_dir'] = True

        if include_index_entries:
            post['index_entries'] = self._get_index_entries(filepath)

        return post

    def _get_index_entries(self, filepath):
        entries = []

        for path in filepath.iterdir():
            if '.git' in path.parts:
                continue

            if path.is_dir():
                entry = self._get_directory_properties(
                    path, include_index_entries=False)
            else:
                entry = self._get_file_properties(path)

            entry['path'] = self._get_output_filepath(path)['web']
            entries.append(entry)

        entries.sort(key=lambda entry: str(entry.get('title', '')).lower())
        entries.sort(key=lambda entry: entry['is_dir'], reverse=True)

        return entries

    def _get_file_properties(self, filepath):
        post = {'title': filepath.name}

        if filepath.suffix == '.md':
            with open(filepath, encoding='utf-8') as file_pointer:
                post = frontmatter.load(file_pointer).to_dict()

        # don't store file contents in memory
        if 'content' in post.keys():
            del post['content']
        post['is_dir'] = False

        return post

    def _get_output_filepath(self, input_filepath):

        def webpath(filepath):
            return Path('/notes').joinpath(
                filepath.relative_to(self.output_dir))

        r = {}
        r['raw'] = self.output_dir.joinpath(
            input_filepath.relative_to(self.input_dir))
        r['web'] = webpath(r['raw'])

        if input_filepath.is_dir():
            return r

        if input_filepath.suffix == '.md':
            r['html'] = self.output_dir.joinpath(
                input_filepath.relative_to(
                    self.input_dir)).with_suffix('.html')
            r['web'] = webpath(r['html'])

        elif self.is_plaintext(input_filepath):
            r['html'] = self.output_dir.joinpath(
                input_filepath.relative_to(
                    self.input_dir)).with_suffix(input_filepath.suffix +
                                                 '.html')
            r['raw'] = self.output_dir.joinpath(
                input_filepath.relative_to(self.input_dir))
            r['web'] = webpath(r['html'])

        return r

    def to_list(self):
        return [val for _, val in self._map.items()]

    def to_search_data(self):
        """
        returns list of every file in map
        """
        r = []
        for _, val in self._map.items():
            r.append({
                'title': val.get('title', ''),
                'tags': val.get('tags', []),
                'path': str(val['dst_path']['web']),
                'is_dir': val['is_dir']
            })

        return r

    def get_uuid_map(self):
        d = {}
        for _, val in self._map.items():
            if 'uuid' not in val.keys():
                continue
            d[val['uuid']] = str(val['dst_path']['web'])

        return d


def update_required(src_filepath, output_filepath):
    """
    check if file requires an update,
    return boolean
    """
    return not output_filepath.exists() or src_filepath.stat(
    ).st_mtime > output_filepath.stat().st_mtimeme()


def get_args():
    """ Get command line arguments """

    parser = argparse.ArgumentParser()
    parser.add_argument('notes', type=Path)
    parser.add_argument('-o', '--output-dir', type=Path, default='web')
    parser.add_argument(
        '-F',
        '--force',
        action="store_true",
        help=
        "Generate new output html even if source file was modified before output html"
    )
    return parser.parse_args()


def render_markdown_file(input_filepath):
    """
    render markdown file to file
    write markdown file to args.output_dir in html,
    return list of tuple of output filepath, frontmatter post
    """
    with open(input_filepath, encoding='utf-8') as file_pointer:
        content = frontmatter.load(file_pointer).content

    properties = FILEMAP.get(input_filepath)

    html = render_markdown(content)
    html = JINJA_TEMPLATE_ARTICLE.render(
        license=LICENSE,
        content=html,
        lecture_slides=properties.get("lecture_slides"),
        lecture_notes=properties.get("lecture_notes"),
        uuid=properties.get("uuid"),
        tags=properties.get("tags"),
        author=properties.get("author"),
        title=properties.get("title"))

    properties['dst_path']['html'].write_text(html)


def render_plaintext_file(input_filepath):
    """
    render plaintext file to file
    copy plaintext file into a html preview, copy raw to output dir
    return list of tuple of output filepath, empty dict
    """

    raw_content = input_filepath.read_text()
    properties = FILEMAP.get(input_filepath)
    html = JINJA_TEMPLATE_TEXTARTICLE.render(license=LICENSE, **properties)
    properties['dst_path']['raw'].write_text(raw_content)
    properties['dst_path']['html'].write_text(html)


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

    headers = {'Accept': 'application/json'}

    response = requests.post(PANDOC_SERVER_URL,
                             headers=headers,
                             json=post_body,
                             timeout=PANDOC_TIMEOUT)

    response = response.json()

    # TODO look at response['messages'] and log them maybe?
    # https://github.com/jgm/pandoc/blob/main/doc/pandoc-server.md#response

    return response['output']


def process_home_index(args, notes_git_head_sha1=None):
    """
    create home index.html in output_dir
    """

    post = {'title': 'gronk', 'content': ''}
    custom_content_file = args.notes.joinpath('readme.md')
    if custom_content_file.is_file():
        fmpost = frontmatter.loads(custom_content_file.read_text()).to_dict()
        for key, val in fmpost.items():
            post[key] = val

    post['content'] = render_markdown(post['content'])

    html = JINJA_TEMPLATE_HOME_INDEX.render(
        gronk_commit=GRONK_COMMIT,
        search_data=FILEMAP.to_search_data(),
        notes_git_head_sha1=notes_git_head_sha1,
        post=post)

    args.output_dir.joinpath('index.html').write_text(html)


def generate_permalink_page(output_dir):
    """
    create the directory and index.html for redirecting permalinks
    """

    dir = output_dir.joinpath('permalink')
    dir.mkdir(exist_ok=True)
    dir.joinpath('index.html').write_text(
        JINJA_TEMPLATE_PERMALINK.render(gronk_commit=GRONK_COMMIT,
                                        data=FILEMAP.get_uuid_map()))


def generate_tag_browser(output_dir):
    """
    generate a directory that lets you groub by and browse by any given tag. e.g. tags, authors
    """
    tags = {}

    for post in FILEMAP.to_list():
        post['path'] = post['dst_path']['web']

        if 'tags' not in post.keys():
            continue

        for tag in post['tags']:
            if tag not in tags.keys():
                tags[tag] = []

            tags[tag].append(post)

    for tag, index_entries in tags.items():
        output_file = output_dir.joinpath(tag, 'index.html')
        output_file.parent.mkdir(exist_ok=True, parents=True)
        output_file.write_text(
            JINJA_TEMPLATE_INDEX.render(
                gronk_commit=GRONK_COMMIT,
                automatic_index=True,
                search_bar=True,
                title=tag,
                index_entries=[{
                    'title': entry.get('title', ''),
                    'is_dir': entry.get('is_dir', False),
                    'path': str(entry.get('path', Path(''))),
                } for entry in index_entries],
            ))

    output_file = output_dir.joinpath('index.html')
    output_file.parent.mkdir(exist_ok=True, parents=True)
    output_file.write_text(
        JINJA_TEMPLATE_INDEX.render(automatic_index=True,
                                    gronk_commit=GRONK_COMMIT,
                                    search_bar=True,
                                    title='tags',
                                    index_entries=[{
                                        'path': tag,
                                        'title': tag,
                                        'is_dir': False,
                                    } for tag in tags.keys()]))


def main(args):
    """ Entry point for script """

    start_time = time.time()

    global LICENSE
    global FILEMAP

    FILEMAP = FileMap(args.notes, args.output_dir.joinpath('notes'))

    # TODO have some sort of 'site rebuild in progress - come back in a minute
    # or two!' or auto checking/refreshing page for when site is being built

    if args.output_dir.is_file():
        print(f"Output directory ({args.output_dir}) cannot be a file.")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # attempt to get licensing information
    license_path = args.notes.joinpath("LICENSE")
    if license_path.exists():
        LICENSE = license_path.read_text()

    # TODO git commit log integration

    for root_str, _, files in os.walk(args.notes):
        root = Path(root_str)
        if '.git' in root.parts:
            continue

        root_properties = FILEMAP.get(root)
        root_properties['dst_path']['raw'].mkdir(parents=True, exist_ok=True)

        #pprint.pprint(root_properties)
        html = JINJA_TEMPLATE_INDEX.render(
            gronk_commit=GRONK_COMMIT,
            title=root_properties.get('title', ''),
            content=root_properties.get('content', ''),
            content_after_search=root_properties['content_after_search'],
            automatic_index=root_properties['automatic_index'],
            search_bar=root_properties['search_bar'],
            index_entries=[{
                'title': entry.get('title', ''),
                'is_dir': entry.get('is_dir', False),
                'path': str(entry.get('path', Path(''))),
            } for entry in root_properties.get('index_entries', '')],
        )
        root_properties['dst_path']['raw'].joinpath('index.html').write_text(
            html)

        # render each file
        for file in files:
            # don't render readme.md as index as it is used for directory
            if file == "readme.md":
                continue
            render_file(root.joinpath(file))

    process_home_index(args)

    # copy styling and js scripts necessary for function
    shutil.copytree(GRONK_CSS_DIR,
                    args.output_dir.joinpath('css'),
                    dirs_exist_ok=True)
    shutil.copytree(GRONK_JS_DIR,
                    args.output_dir.joinpath('js'),
                    dirs_exist_ok=True)

    generate_tag_browser(args.output_dir.joinpath('tags'))
    generate_permalink_page(args.output_dir)

    elapsed_time = time.time() - start_time
    print(f"generated notes {elapsed_time=}")

    return 0


def start_pandoc_server():
    """
    attempt to get the version of pandoc server in a loop until it is
    successful and return version as string
    """
    start_time = time.time()
    process = subprocess.Popen(["/usr/bin/pandoc-server"],
                               stdout=subprocess.PIPE)
    version = None

    while True:
        try:
            resp = requests.get(f"{PANDOC_SERVER_URL}/version")
            version = resp.content.decode('utf-8')
            break
        except requests.ConnectionError:
            time.sleep(0.1)
            rc = process.poll()
            if rc is not None:
                print(f"PANDOC SERVER FAILED TO START: {rc=}")
                print(process.stdout.read().decode("utf-8"))
                raise Exception("Pandoc server failed to start")

    elapsed_time = time.time() - start_time
    print(f"pandoc-server started {version=} {elapsed_time=}")
    return process


# TODO implement useful logging and debug printing

if __name__ == '__main__':
    pandoc_process = start_pandoc_server()

    try:
        sys.exit(main(get_args()))
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        pandoc_process.kill()
