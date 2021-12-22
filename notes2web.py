#!/usr/bin/env python3


from bs4 import BeautifulSoup as bs
import subprocess
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
            if pathlib.Path(name).suffix == '.md':
                markdown.append(name)
            elif re.match(r'^text/', magic.from_file(name, mime=True)):
                plaintext.append(name)
                other.append(name)
            else:
                other.append(name)

    return markdown, plaintext, other


def git_filehistory(working_dir, filename):
    print(f"{pathlib.Path(filename).relative_to(working_dir)=}")
    git_response = subprocess.run(
            [
                'git',
                f"--git-dir={working_dir.joinpath('.git')}",
                "log",
                "-p",
                "--",
                pathlib.Path(filename).relative_to(working_dir)
            ],
            stdout=subprocess.PIPE
    )

    filehistory = [f"File history not available: git log returned code {git_response.returncode}."
    "\nIf this is not a git repository, this is not a problem."]

    if git_response.returncode == 0:
        filehistory = git_response.stdout.decode('utf-8')
        temp = re.split(
                r'(commit [a-f0-9]{40})',
                filehistory,
                flags=re.IGNORECASE
        )

        for t in temp:
            if t == '':
                temp.remove(t)
        filehistory = []
        for i in range(0, len(temp)-1, 2):
            filehistory.append(f"{temp[i]}{temp[i+1]}")

    if filehistory == "":
        filehistory = ["This file has no history (it may not be part of the git repository)."]

    filehistory = [ x.replace("<", "&lt;").replace(">", "&gt;") for x in filehistory]

    filehistory = "<pre>\n" + "</pre><pre>\n".join(filehistory) + "</pre>"

    return filehistory


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
    parser.add_argument('--tocsearchjs', type=pathlib.Path, default=pathlib.Path('/opt/notes2web/toc_search.js'))
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

    if args.output_dir.is_file():
        print(f"Output directory ({args.output_dir}) cannot be a file.")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    notes_license = "This note has no copyright license.",
    print(f"{notes_license=}")
    license_path = args.notes.joinpath("LICENSE")
    if license_path.exists():
        with open(license_path) as fp:
            notes_license = fp.read()

    markdown_files, plaintext_files, other_files = get_files(args.notes)

    all_entries=[]
    dirs_with_index_article = []
    tag_dict = {}

    print(f"{markdown_files=}")
    for filename in markdown_files:
        print(f"{filename=}")

        # calculate output filename
        output_filename = args.output_dir.joinpath('notes').joinpath(
            pathlib.Path(filename).relative_to(args.notes)
        ).with_suffix('.html')
        if os.path.basename(filename) in args.index_article_names:
            output_filename = output_filename.parent.joinpath('index.html')
            dirs_with_index_article.append(str(output_filename.parent))
        print(f"{output_filename=}")

        # extract tags from frontmatter, save to tag_dict
        fm = frontmatter.load(filename)
        if isinstance(fm.get('tags'), list):
            for tag in fm.get('tags'):
                t = {
                    'path': str(pathlib.Path(output_filename).relative_to(args.output_dir)),
                    'title': fm.get('title') or pathlib.Path(filename).name
                }
                if tag in tag_dict.keys():
                    tag_dict[tag].append(t)
                else:
                    tag_dict[tag] = [t]

        # find headers in markdown
        with open(filename) as fp:
            lines = fp.read().split('\n')
        header_lines = []
        for line in lines:
            if re.match('^#{1,6} \S', line):
                header_lines.append(" ".join(line.split(" ")[1:]))

        all_entries.append({
            'path': str(pathlib.Path(*pathlib.Path(output_filename).parts[1:])),
            'title': fm.get('title') or pathlib.Path(filename).name,
            'tags': fm.get('tags'),
            'headers': header_lines
        })

        # update file if required
        if update_required(filename, output_filename) or args.force:
            filehistory = git_filehistory(args.notes, filename)
            html = pypandoc.convert_file(filename, 'html', extra_args=[
                f'--template={args.template}',
                '-V', f'filehistory={filehistory}',
                '-V', f'licenseFull={notes_license}',
                '--mathjax',
                '--toc'
            ])
            pathlib.Path(output_filename).parent.mkdir(parents=True, exist_ok=True)

            with open(output_filename, 'w+') as fp:
                fp.write(html)

    print(f"{plaintext_files=}")
    for filename in plaintext_files:
        filehistory = git_filehistory(args.notes, filename)
        title = os.path.basename(filename)
        output_filename = str(
            args.output_dir.joinpath('notes').joinpath(
                pathlib.Path(filename).relative_to(args.notes)
            )
        ) + '.html'
        print(f"{output_filename=}")

        pathlib.Path(output_filename).parent.mkdir(parents=True, exist_ok=True)
        html = re.sub(r'\$title\$', title, TEXT_ARTICLE_TEMPLATE_HEAD)
        html = re.sub(r'\$h1title\$', title, html)
        html = re.sub(r'\$raw\$', os.path.basename(filename), html)
        html = re.sub(r'\$licenseFull\$', notes_license, html)
        html = html.replace('$filehistory$', filehistory)
        with open(filename) as fp:
            html += fp.read().replace("<", "&lt;").replace(">", "&gt;")
        html += TEXT_ARTICLE_TEMPLATE_FOOT

        with open(output_filename, 'w+') as fp:
            fp.write(html)
        all_entries.append({
            'path': str(pathlib.Path(*pathlib.Path(output_filename).parts[1:])),
            'title': title,
            'tags': [],
            'headers': []
        })

    print(f"{other_files=}")
    for filename in other_files:
        output_filename = str(
            args.output_dir.joinpath('notes').joinpath(
                pathlib.Path(filename).relative_to(args.notes)
            )
        )
        pathlib.Path(output_filename).parent.mkdir(parents=True, exist_ok=True)
        all_entries.append({
            'path': str(pathlib.Path(*pathlib.Path(output_filename).parts[1:])),
            'title': str(pathlib.Path(*pathlib.Path(output_filename).parts[1:])),
            'tags': [],
            'headers': []
        })
        shutil.copyfile(filename, output_filename)

    tagdir = args.output_dir.joinpath('.tags')
    tagdir.mkdir(parents=True, exist_ok=True)

    for tag in tag_dict.keys():
        html = re.sub(r'\$title\$', f'{tag}', INDEX_TEMPLATE_HEAD)
        html = re.sub(r'\$h1title\$', f'tag: {tag}', html)
        html = re.sub(r'\$extra_content\$', '', html)

        for entry in tag_dict[tag]:
            html += f"<div class=\"article\"><a href=\"/{entry['path']}\">{entry['title']}</a></div>"
        html += INDEX_TEMPLATE_FOOT

        with open(tagdir.joinpath(f'{tag}.html'), 'w+') as fp:
            fp.write(html)



    dirs_to_index = [args.output_dir.name] + get_dirs(args.output_dir)
    print(f"{dirs_to_index=}")
    print(f"{dirs_with_index_article=}")

    for d in dirs_to_index:
        print(f"{d in dirs_with_index_article=} {d=}")
        if d in dirs_with_index_article:
            continue

        directory = pathlib.Path(d)
        paths = os.listdir(directory)
        #print(f"{paths=}")

        indexentries = []
        
        for p in paths:
            path = pathlib.Path(p)
            #print(f"{path=}")
            if p in [ 'index.html', '.git' ]:
                continue

            fullpath = directory.joinpath(path)
            if path.suffix == '.html':
                with open(fullpath) as fp:
                    soup = bs(fp.read(), 'html.parser')

                try:
                    title = soup.find('title').get_text() or pathlib.Path(path).name
                except AttributeError:
                    title = pathlib.Path(path).stem
            elif fullpath.is_dir():
                title = path
            else:
                # don't add plaintext files to index, since they have a html wrapper
                continue

            if str(title).strip() == '':
                title = path

            indexentries.append({
                'title': str(title),
                'path': str(path),
                'isdirectory': fullpath.is_dir()
                })

        indexentries.sort(key=lambda entry: str(entry['title']).lower())
        indexentries.sort(key=lambda entry: entry['isdirectory'], reverse=True)
        
        html = re.sub(r'\$title\$', str(directory), INDEX_TEMPLATE_HEAD)
        html = re.sub(r'\$h1title\$', str(directory), html)
        html = re.sub(r'\$extra_content\$',
                EXTRA_INDEX_CONTENT if directory == args.notes else '',
                html
                )

        for entry in indexentries:
            html += (
                    '<li class="article">'
                        f'<a href="{entry["path"]}">'
                            f'{entry["title"]}{"/" if entry["isdirectory"] else ""}'
                        '</a>'
                    '</li>'
            )
        html += INDEX_TEMPLATE_FOOT

        with open(directory.joinpath('index.html'), 'w+') as fp:
            fp.write(html)

    shutil.copyfile(args.stylesheet, args.output_dir.joinpath('styles.css'))
    shutil.copyfile(args.fuse, args.output_dir.joinpath('fuse.js'))
    shutil.copyfile(args.searchjs, args.output_dir.joinpath('search.js'))
    shutil.copyfile(args.tocsearchjs, args.output_dir.joinpath('toc_search.js'))
    with open(args.output_dir.joinpath('index.html'), 'w+') as fp:
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
