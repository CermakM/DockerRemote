"""Docker Remote Manager - Manage remote docker repository"""

import sys

# Import custom classes
from docker_remote.core.analyser import DockerAnalyser


class ExceptionHandler:
    """Custom exception handling class allowing to turn off traceback"""

    def __init__(self, debug=True):
        """Initialize exception handler
        :param debug: use traceback, bool
        """
        self.debug = debug
        self.debug_hook = sys.excepthook

    def __call__(self, exc_type, exc, exc_tb):
        if self.debug:
            self.debug_hook(exc_type, exc, exc_tb)
        else:
            print("{name}: {exc}".format(name=exc_type.__name__, exc=exc),
                  file=sys.stderr)


class DockerManager:
    """Docker manager class"""

    def __init__(self, repository, namespace="library", search=False, url=None,
                 username=None, password=None, verbose=True,
                 debug=False):

        self.namespace = namespace
        self.repository_name = repository

        self.username = username
        self.password = password
        self.verbose = verbose

        # Initialize exception handler
        sys.excepthook = ExceptionHandler(debug=debug)

        # Initialize analyser
        self.analyser = DockerAnalyser(repository=repository,
                                       namespace=namespace,
                                       search=search,
                                       url=url,
                                       debug=debug)

        self.token = None
        if self.username:
            self.login(username, password)

    def login(self, username, password):
        self.username = username
        self.password = password

        self.analyser.set_credentials(username, password)
        self.token = self.analyser.request_token()

    def search(self, query, page_lim=None) -> iter:
        repo_list, num_results = self.analyser.query(query)
        # TODO handle printing multiple pages

        print("Number of results: {}\n".format(num_results))

        est_num_pages = num_results // len(repo_list)

        num_pages = min(est_num_pages, page_lim) if page_lim else est_num_pages

        max_key_len = max(len(res[0]) for res in repo_list)
        for page_i in range(num_pages):
            yield "Page %d\n------" % (page_i + 1)
            for i in range(len(repo_list)):
                repo = repo_list[i]
                result = "{repo:<{keylen}} : {description}\n".format(
                    keylen=max_key_len,
                    repo=repo[0],
                    description=repo[1]
                )

                yield result

            repo_list, _ = self.analyser.query(query, page=2)

    def search_by_user(self, user, query):
        # TODO
        pass

    def print_nof_search_results(self, query):
        _, num_results = self.analyser.query(query)

        if self.verbose:
            print("Number of results: {}\n".format(num_results))
        else:
            print(num_results)

    def print_repo_size(self, full):
        print(self.analyser.get_repo_size(full=full))

    def print_namespace(self):
        if self.namespace == 'library':
            print("Docker Hub remote repository: "
                  "{s.repository_name}\n".format(s=self))
        else:
            print("Docker Hub remote repository: "
                  "{s.namespace}/{s.repository_name}\n".format(s=self))

    def print_description(self, short=True, full=False):
        description = self.analyser.get_description()
        # TODO markdown conversion
        if short and full:
            print('\n'.join(description), '\n')
        elif short:
            print(description[0])
        else:
            print(description[1])

    def print_tag_info(self, tag_name: str, *args: str):
        """Prints all tag attributes or only attributes specified by *args
        :param tag_name: tag id (name), str
        :param args: [optional] Key values passed in to tag dictionary, str
        """
        tag = self.analyser.get_tag(tag_name)
        if self.verbose:
            print('Description of tag {}'.format(tag))

        tag_cpy = tag.copy()
        if not args:
            # Print all attributes if no arg is specified
            max_key_len = max(len(key) for key in tag_cpy.keys()) + 1
            # Print primary attributes
            primary_keys = ['namespace', 'repository_name', 'name', 'size_mb']
            for key in primary_keys:
                print("  {:<{keylen}s}:  {}".format(key, tag_cpy.pop(key),
                      keylen=max_key_len))
            # Print rest of the attributes
            for k, v in tag_cpy.items():
                print("  {:<{keylen}s}:  {}".format(k, v, keylen=max_key_len))
        else:
            # Print only specific attributes
            max_key_len = max(len(key) for key in args) + 1
            for arg in args:
                print("  {key:<{keylen}s}:  {value}".format(key=arg,
                                                            keylen=max_key_len,
                                                            value=tag[arg]))

        print('\n')

    def get_tag_count(self) -> int:
        """Returns number of tags from remote repository"""
        return self.analyser.get_nof_tags()

    def print_tag_count(self):
        """Prints number of tags from remote repository"""
        print(self.analyser.get_nof_tags())

    def print_tags(self, count: int = None, fmt='plain', delim=' '):
        """Prints list of tags from remote repository

        """
        tags = self.analyser.get_tags()
        if count is None:
            count = len(tags)

        if fmt == 'plain':
            print(delim.join([tag['name'] for tag in tags]))

        else:
            key_maxlen = max(len(tag.__str__()) for tag in tags)
            format_str = "{:<5}{:^{maxlen}} | {:^11}| {:^.10}"
            header_str = format_str.format(
                "NUM", "TAG", "SIZE", "UPDATED AT", maxlen=key_maxlen)

            print(header_str)
            print("{:-<{len}}".format("", len=len(header_str)))
            for index, tag in enumerate(tags[:count]):
                print(format_str.format(str(index + 1) + '.',
                                        tag.__str__(),
                                        tag['size_mb'],
                                        tag['last_updated'],
                                        maxlen=key_maxlen))

            print('\n')

    def remove_tag(self, tag_name: str, confirmation=None):
        """
        Remove tag from remote repository by specifying tag name
        Note: This method requires authorization token (login needed)
        :param tag_name: tag id (name), str
        :param confirmation: True for confirmed, False for not (default None)
        :return:
        """

        if not self._confirm_tags([tag_name], confirmation):
            self._abort(1)

        self.analyser.remove_tag(tag_name)

        if self.verbose:
            print("Tag: {name} was successfully removed".format(name=tag_name))

    def remove_tags(self, n: int, confirmation=None, reverse=False):
        """Remove `n` oldest tags from remote repository
        Note: This method requires authorization token (login needed)
        :param n: number of tags to be removed (-1 for all), int
        :param confirmation: True for confirmed, False for not (default None)
        :param reverse: Remove tags in reversed order (default False - oldest first)
        :returns: error code, int
        """
        tags = self.analyser.get_tags()
        if n == 0:
            print("There are no tags to be removed")
            exit(0)

        if n < 0:
            n = len(tags)

        tags = sorted(tags, key=lambda t: t['last_updated'], reverse=reverse)
        max_index = min(n, len(tags))

        tag_names = [t['name'] for t in tags[:max_index]]

        if not self._confirm_tags(tag_names, confirmation):
            self._abort(1)

        for tag in tag_names:
            self.remove_tag(tag)

    def _confirm_tags(self, tag_names: list, confirmation) -> bool:
        msg = "The following tags will be deleted:\n"
        if self.namespace == 'library':
            namespace = ''
        else:
            namespace = self.namespace + '/'
        for tag in tag_names:
            msg += "\t{namespace}{repo}:{tag}\n".format(namespace=namespace,
                                                        repo=self.repository_name,
                                                        tag=tag)
        msg += "Is this okay? [y/N]: "
        if confirmation is None:
            confirmation = self._confirm()

        msg += ['N\n', 'y\n'][confirmation]

        print(msg)
        return confirmation

    def _confirm(self) -> bool:
        """Ask user for confirmation, choice [y/N]"""
        confirmation = map(str.lower, input())
        try:
            confirmation = next(confirmation)
        except StopIteration:
            return False

        if confirmation in ['n', 'y']:
            return [False, True][confirmation == 'y']
        else:
            return self._confirm()

    # TODO consider if the exit is safe - turn to method eventually
    @staticmethod
    def _abort(err_code):
        """
        Aborts the program and safely exits
        :param err_code: error code to be returned
        :return: err_code
        """
        print("Operation aborted", file=sys.stderr)

        exit(err_code)
