#!/usr/bin/env python3

import editfrontmatter
import frontmatter
import pathlib
import sys
import uuid

def get_args():
    """ Get command line arguments """

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=pathlib.Path)
    parser.add_argument('-w', '--write', action='store_true',
            help='write to file instead of stdout')
    return parser.parse_args()


def main(args):
    """ Entry point for script """
        template_str= [
            "author: {{ author }}"
            "date: {{ date }}"
            "title: {{ title }}"
            "tags: {{ tags }}"
            "uuid: {{ uuid }}"
            ].join("\n")

    with open(args.filename) as fp:
        fm_pre = frontmatter.load(fp)

    processor = editfrontmatter.EditFrontMatter(file_path=args.filename, template_str=template_str)
    fm_data = fm_pre.metadata
    if 'uuid' not in fm_data.keys():
        fm_data['uuid'] = str(uuid.uuid4())

    processor.run(fm_data)

    if args.write:
        with open(args.filename, 'w') as fp:
            fp.write(processor.dumpFileData())
    else:
        print(processor.dumpFileData())
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(get_args()))
    except KeyboardInterrupt:
        sys.exit(0)
