"""Docker Remote Manager - Manage remote docker repository"""

import sys

# Import custom classes
from remote import DockerAnalyser


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

    def search(self, query, count=None):
        num_results, repo_list = self.analyser.query(query)
        # TODO handle printing multiple pages
        print("Number of results: {}\n".format(num_results))

        count = min(len(repo_list), count) if count else len(repo_list)

        max_key_len = max(len(res[0]) for res in repo_list)

        for i in range(count):
            repo = repo_list[i]
            print("{repo:<{keylen}} : {description}\n".format(
                keylen=max_key_len,
                repo=repo[0],
                description=repo[1]
            ))

    def search_by_user(self, user, query):
        # TODO
        pass

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

    def print_tags(self, count: int = None):
        """Prints list of tags from remote repository
        """
        tags = self.analyser.get_tags()
        if count is None:
            count = len(tags)

        key_maxlen = max(len(tag.__str__()) for tag in tags)
        header_str = "{:<{maxlen}} | {:^10}| {:^.10}".format(
            "TAG", "SIZE", "UPDATED AT", maxlen=key_maxlen)

        print(header_str)
        print("{:-<{len}}".format("", len=len(header_str)))
        for tag in tags[:count]:
            print("{:<{maxlen}} | {:^10}| {:.10}"
                  .format(tag.__str__(), tag['size_mb'], tag['last_updated'], maxlen=key_maxlen))

        print('\n')

    def remove_tag(self, tag_name: str):
        """
        Remove tag from remote repository by specifying tag name
        Note: This method requires authorization token (login needed)
        :param tag_name: tag id (name), str
        :return:
        """
        self.analyser.remove_tag(tag_name)
        print("Tag: {name} was successfully removed".format(name=tag_name))

    def remove_tags(self, n: int):
        """Remove `n` latest tags from remote repository
        Note: This method requires authorization token (login needed)
        :param n: number of tags to be removed, int
        """
        tags = self.analyser.get_tag_names()
        tags = sorted(tags, key=lambda t: t.last_updated)
        max_index = min(n, len(tags))
        for tag in tags[:max_index]:
            self.remove_tag(tag.name)

    def remove_all_tags(self):
        """Remove all tags from remote repository
        Note: This method requires authorization token (login needed)
        """
        for tag in self.analyser.get_tag_names():
            self.analyser.remove_tag(tag.name)
