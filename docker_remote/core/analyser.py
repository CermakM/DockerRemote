"""Docker Remote Analyser - Handle remote docker repository"""

import json
import logging
import urllib3

from docker_remote.core.repository import DockerRepository, Tag

DOCKER_BASE_URL = 'https://hub.docker.com/v2/'
DOCKER_LOGIN_URL = 'https://hub.docker.com/v2/users/login/'

LOG = logging.getLogger('docker-remote.analyser')


class DockerAnalyser:

    def __init__(self, repository, namespace="library", search=False, url="", token=None, debug=False):
        """Initialize Docker analyser to handle http requests"""
        # Disable warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.repository_name = repository
        self.namespace = namespace
        self.url = url
        self.token = token
        self.debug = debug
        self.login = ""

        # Initialize controls
        self.http = urllib3.PoolManager()
        # Used for tracking current status and logging
        self.response = None

        # Get repository
        if not search:
            self.repository = self._get_repository()  # Repository object

    def set_credentials(self, username: str, password: str):
        self.login = {'username': username, 'password': password}

    def request_token(self) -> str:
        """Performs login to the docker hub and requests user token
        Sets up authorization header on success
        Uses cookies
        :returns: Authorization token, str
        :raises: urllib3.exceptions.HTTPError, KeyError
        """
        self.response = self.http.request('POST', DOCKER_LOGIN_URL, fields=self.login)
        self._check_response()
        try:
            self.http.headers['cookie'] = self.response.getheader('set-cookie')
            self.token = json.loads(self.response.data.decode('utf-8'))['token']
        except KeyError as e:
            # TODO LOG
            raise e

        # Create authorization header
        self.http.headers['Authorization'] = "Bearer %s" % self.token

        return self.token

    def query(self, query, site='repositories', page=1) -> (int, list):
        """
        Queries Docker Hub repository for given search term
        :param query: search string
        :param site: site to browse (default 'repositories')
        :param page: page to be displayed (default 1)
        :return: count, list of repository names or None
        """
        search_url = DOCKER_BASE_URL + "search/" + site
        query = "{url}/?page={page}&query={query}".format(url=search_url,
                                                          page=page, query=query)

        LOG.debug("Performing search for query: %s", query)

        self.response = self.http.request('GET', query)
        self._check_response()

        json_response = json.loads(self.response.data.decode('utf-8'))
        count = json_response['count']
        results = json_response['results']

        repo_list = [None] * len(results)
        "List of tuples: (repo_name, short_description)"
        for i, res in enumerate(results):
            repo_list[i] = (res['repo_name'], res['short_description'])

        return repo_list, count

    @staticmethod
    def repo_to_url(repository, namespace, site='repositories'):

        return "{base}{site}/{namespace}/{repo}/".format(base=DOCKER_BASE_URL,
                                                         site=site,
                                                         namespace=namespace,
                                                         repo=repository)

    def _get_repository(self) -> DockerRepository:
        """
        :return: DockerRepository
        :raises: urllib3.exceptions.HTTPError
        """
        if not any((self.repository_name, self.url)):
            raise ValueError("Cannot get repository: "
                             "URL or repository name must be provided")

        if not self.url:
            self.url = self.repo_to_url(self.repository_name, self.namespace)
        # Get repository info
        self.response = self.http.request('GET', self.url)
        self._check_response()

        repository = DockerRepository(url=self.url)
        repository.add_info(data=json.loads(self.response.data.decode('utf-8'), encoding='UTF-8'))

        # Get repository tags and repeat for multiple pages
        data = None
        next_url = self.url + 'tags/'

        while next_url:
            self.response = self.http.request('GET', next_url)
            self._check_response()

            data = json.loads(self.response.data.decode('utf-8'), encoding='UTF-8')
            repository.add_tags(data=data)

            next_url = data['next']

        repository.count = data.get('count', 0)

        return repository

    def get_repo_size(self, full=False) -> int or str:

        return self.repository.size if full else self.repository.size_mb

    def get_tag(self, tag_name: str) -> Tag:

        return self.repository.tags[tag_name]

    def get_tags(self) -> list:

        return list(self.repository.tags.values())

    def get_tag_names(self) -> list:

        return list(self.repository.tags.keys())

    def get_nof_tags(self) -> int:

        return len(self.repository)

    def get_description(self) -> tuple:

        return self.repository['description'], self.repository['full_description']

    def get_permissions(self) -> dict:
        return self.repository['permissions']

    def remove_tag(self, tag: str):
        """
        :param tag: tag id (name), str
        :raises: urllib3.exceptions.HTTPError
        """
        self.response = self.http.request('DELETE', self.url + 'tags/%s' % tag)
        self._check_response()

        self.repository.pop(tag, None)

    def _check_response(self, status=300):
        """Check status code and raises exception based on status argument
        :param status: status code that is tolerated
        :raises: urllib3.exceptions.HTTPError
        """
        if self.response.status >= status:
            self._raise_from_response()

    def _raise_from_response(self):
        """
        :raises: urllib3.exceptions.HTTPError
        """
        msg = "Error %d occurred: " % self.response.status
        msg += "%s, " % self.response.reason
        msg += self.response.data.decode('utf-8')
        # TODO LOG
        raise urllib3.exceptions.HTTPError(msg)

    def _check_tag(self, tag_name: str):
        """
        :param tag_name:
        :raises:  KeyError
        """
        if tag_name not in self.repository.tags:
            # TODO LOG, add did you mean?
            msg = "Tag {namespace}/{repo}:{tag} does not exist".format(
                tag=tag_name,
                namespace=self.namespace,
                repo=self.repository_name
            )
            raise KeyError(msg)
