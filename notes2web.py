#!/usr/bin/env python3


from bs4 import BeautifulSoup as bs
import frontmatter
import magic
import sys
import pathlib
import pypandoc
import shutil
import os
import re
import json


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
            if '/.git' in root:
                continue
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


def update_required(src_filename, output_filename):
    return not os.path.exists(output_filename) or os.path.getmtime(src_filename) > os.path.getmtime(output_filename)


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
    parser.add_argument('--home_index', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/templates/home_index.html'))
    parser.add_argument('-e', '--extra-index-content', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/templates/extra_index_content.html'))
    parser.add_argument('-n', '--index-article-names', action='append', default=['index.md'])
    parser.add_argument('-F', '--force', action="store_true", help="Generate new output html even if source file was modified before output html")
    parser.add_argument('--fuse', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/fuse.js'))
    parser.add_argument('--searchjs', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/search.js'))
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
    all_entries=[]

    print(f"{args.index_article_names=}")

    dirs_with_index_article = []

    print(f"{markdown_files=}")
    tag_dict = {}
    for filename in markdown_files:
        print(f"{filename=}")
        print(f"{os.path.basename(filename)=}")

        if os.path.basename(filename) in args.index_article_names:
            output_filename = os.path.join(
                    os.path.dirname(re.sub(f"^{args.notes.name}", os.path.join(args.output_dir.name, 'notes', filename))),
                    'index.html'
                    )
            dirs_with_index_article.append(os.path.dirname(re.sub(f"^{args.notes.name}", os.path.join(args.output_dir.name, 'notes'), filename)))
        else:
            output_filename = os.path.splitext(re.sub(f"^{args.notes.name}", os.path.join(args.output_dir.name, 'notes'), filename))[0] + '.html'

        fm = frontmatter.load(filename)
        if isinstance(fm.get('tags'), list):
            for tag in fm.get('tags'):
                if tag in tag_dict.keys():
                    tag_dict[tag].append({
                        'path': str(pathlib.Path(*pathlib.Path(output_filename).parts[1:])),
                        'title': fm.get('title')
                        })
                else:
                    tag_dict[tag] = [ {
                        'path': str(pathlib.Path(*pathlib.Path(output_filename).parts[1:])),
                        'title': fm.get('title')
                        } ]
        print(f"{output_filename=}")
        all_entries.append({
            'path': str(pathlib.Path(*pathlib.Path(output_filename).parts[1:])),
            'title': fm.get('title'),
            'tags': fm.get('tags')
        })

        if update_required(filename, output_filename) or args.force:
            html = pypandoc.convert_file(filename, 'html', extra_args=[f'--template={args.template}'])
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)

            with open(output_filename, 'w+') as fp:
                fp.write(html)

    print(f"{plaintext_files=}")
    for filename in plaintext_files:
        title = os.path.basename(re.sub(f"^{args.notes.name}", args.output_dir.name, filename))
        output_filename = re.sub(f"^{args.notes.name}", os.path.join(args.output_dir.name, 'notes'), filename) + '.html'
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        html = re.sub(r'\$title\$', title, TEXT_ARTICLE_TEMPLATE_HEAD)
        html = re.sub(r'\$h1title\$', title, html)
        html = re.sub(r'\$raw\$', os.path.basename(filename), html)
        with open(filename) as fp:
            html += fp.read()
        html += TEXT_ARTICLE_TEMPLATE_FOOT

        with open(output_filename, 'w+') as fp:
            fp.write(html)
        all_entries.append({
            'path': str(pathlib.Path(*pathlib.Path(output_filename).parts[1:])),
            'title': title,
            'tags': []
        })

    print(f"{other_files=}")
    for filename in other_files:
        output_filename = re.sub(f"^{args.notes.name}", os.path.join(args.output_dir.name, 'notes'), filename)
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        all_entries.append({
            'path': str(pathlib.Path(*pathlib.Path(output_filename).parts[1:])),
            'title': str(pathlib.Path(*pathlib.Path(output_filename).parts[1:])),
            'tags': []
        })
        shutil.copyfile(filename, output_filename)

    tagdir = os.path.join(args.output_dir, '.tags')
    os.makedirs(tagdir, exist_ok=True)

    for tag in tag_dict.keys():
        html = re.sub(r'\$title\$', f'{tag}', INDEX_TEMPLATE_HEAD)
        html = re.sub(r'\$h1title\$', f'tag: {tag}', html)
        html = re.sub(r'\$extra_content\$', '', html)

        for entry in tag_dict[tag]:
            html += f"<div class=\"article\"><a href=\"/{entry['path']}\">{entry['title']}</a></div>"
        html += INDEX_TEMPLATE_FOOT

        with open(os.path.join(tagdir, f'{tag}.html'), 'w+') as fp:
            fp.write(html)



    dirs_to_index = [args.output_dir.name] + get_dirs(args.output_dir)
    print(f"{dirs_to_index=}")
    print(f"{os.path.commonpath(dirs_to_index)=}")

    for directory in dirs_to_index:
        if directory in dirs_with_index_article:
            continue
        paths = os.listdir(directory)
        print(f"{paths=}")

        indexentries = []
        
        for path in paths:
            print(f"{path=}")
            if path in [ 'index.html', '.git' ]:
                continue

            fullpath = os.path.join(directory, path)
            if os.path.splitext(path)[1] == '.html':
                with open(fullpath) as fp:
                    soup = bs(fp.read(), 'html.parser')

                try:
                    title = soup.find('title').get_text()
                except AttributeError:
                    title = path
            elif os.path.isdir(fullpath):
                title = path
            else:
                # don't add plaintext files to index, since they have a html wrapper
                continue

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
        html = re.sub(r'\$h1title\$', directory, html)
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
    shutil.copyfile(args.fuse, os.path.join(args.output_dir.name, 'fuse.js'))
    shutil.copyfile(args.searchjs, os.path.join(args.output_dir.name, 'search.js'))
    with open(os.path.join(args.output_dir.name, 'index.html'), 'w+') as fp:
        with open(args.home_index) as fp2:
            html = re.sub(r'\$title\$', args.output_dir.parts[0], fp2.read())
            html = re.sub(r'\$h1title\$', args.output_dir.parts[0], html)

        html = re.sub(r'\$data\$', json.dumps(all_entries), html)

        fp.write(html)
    print(tag_dict)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(get_args()))
    except KeyboardInterrupt:
        sys.exit(0)
