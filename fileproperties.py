from pathlib import Path
import frontmatter
import copy
import magic
import regex as re


class FileMap:
    """
    this class is used to read file properties, inherit properties, and have a centralised place to access them
    """
    def __init__(self, input_dir, output_dir):
        self._map = {}
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

    @staticmethod
    def _path_to_key(path):
        return str(Path(path))

    def get(self, filepath, default=None, raw=False):
        """
        get the properties of a file at a filepath
        raw=True to not inherit properties
        """
        #print(f"FileMap.get({filepath=}, {default=}, {raw=})")
        # TODO maybe store properties of a file once it's in built and mark it as built? might save time but also cba
        if self._path_to_key(filepath) not in self._map.keys():
            self.add(filepath)

        properties = copy.deepcopy(self._map.get(self._path_to_key(filepath), default))
        #print(f"FileMap.get({filepath=}, {default=}, {raw=}): {properties=}")

        if raw:
            return properties

        parent = filepath
        while True:
            parent = parent.parent
            if parent == Path('.'):
                break

            parent_properties = self.get(parent, raw=True)
            # TODO inherit any property that isn't defined, append any lists that exist
            properties['tags'] = properties.get('tags', []) + parent_properties.get('tags', [])

            if parent == self.input_dir:
                break

        return properties

    def add(self, filepath):
        filepath = Path(filepath)
        #print(f"FileMap.add({filepath=}")
        if filepath.is_dir():
            properties = self._get_directory_properties(filepath)
        else:
            properties = self._get_file_properties(filepath)

        properties['src_path'] = filepath
        properties['dst_path'] = self._get_output_filepath(filepath)

        self._map[self._path_to_key(filepath)] = properties


    def _get_directory_properties(self, filepath: Path, include_index_entries=True):
        """
        return dict of directory properties to be used in pandoc template
        """

        post = {
                'title': filepath.name,
                'content_after_search': False,
                'automatic_index': True,
                'search_bar': True,
                'tags': [],
                }

        if 'index.md' in filepath.iterdir():
            with open(filepath.joinpath('index.md'), encoding='utf-8') as file_pointer:
                for key, val in frontmatter.load(file_pointer).to_dict():
                    post[key] = val

        post['is_dir'] = True

        if include_index_entries:
            post['index_entries'] = self._get_index_entries(filepath)

        return post


    def _get_index_entries(self, filepath):
        """
        return sorted list of index entries. alphabetically sorted, folders first
        """
        entries = []

        for path in filepath.iterdir():
            print(f'{path=}')
            if path.is_dir():
                entry = self._get_directory_properties(path, include_index_entries=False)
            else:
                entry = self._get_file_properties(path)

            entry['path'] = self._get_output_filepath(path)['web']
            entries.append(entry)
            #print(f"FileMap._get_index_entries({filepath=}): {entry=}")


        entries.sort(key=lambda entry: str(entry['title']).lower())
        entries.sort(key=lambda entry: entry['is_dir'], reverse=True)

        return entries

    def _get_file_properties(self, filepath):
        #print(f"FileMap._get_file_properties({filepath=}")
        post = { 'title': filepath.name }

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
            return Path('/notes').joinpath(filepath.relative_to(self.output_dir))


        r = {}
        r['raw'] = self.output_dir.joinpath(input_filepath.relative_to(self.input_dir))
        r['web'] = webpath(r['raw'])

        if input_filepath.is_dir():
            return r

        if input_filepath.suffix == '.md':
            r['html'] = self.output_dir.joinpath(
                            input_filepath.relative_to(self.input_dir)
                        ).with_suffix('.html')
            r['web'] = webpath(r['html'])

        elif self.is_plaintext(input_filepath):
            r['html'] = self.output_dir.joinpath(
                            input_filepath.relative_to(self.input_dir)
                        ).with_suffix(input_filepath.suffix + '.html')
            r['raw'] = self.output_dir.joinpath(input_filepath.relative_to(self.input_dir))
            r['web'] = webpath(r['html'])

        #print(f"{r=}")

        return r


    def to_list(self):
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


    @staticmethod
    def is_plaintext(filename):
        """
        check if file is a plaintext format, such as html, css, etc,
        return boolean
        """
        return re.match(r'^text/', magic.from_file(str(filename), mime=True)) is not None
