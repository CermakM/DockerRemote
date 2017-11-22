"""Docker Remote Repository - remote docker repository handler"""


# TODO subclass dict and add attribute getter and setter
class Tag(dict):
    """Docker tag object"""
    def __init__(self, dct: dict, namespace: str, repo: str):
        """
        Convenient class to access tag dictionary via attributes
        :param dct: dictionary holding tag attributes, dict
        :param namespace: repository namespace, str
        :param repo: remote repository name, str
        """
        super(Tag, self).__init__(dct)
        self['namespace'] = namespace
        self['repository_name'] = repo
        self['size_mb'] = str(dct['full_size'] // 1e6) + ' MB'
        "size in MB, str"

    def __str__(self):
        if self['namespace'] == 'library':
            return "{s[repository_name]}:{s[name]}".format(s=self)

        return "{s[namespace]}/{s[repository_name]}:{s[name]}".format(s=self)


class DockerRepository(dict):
    """Docker repository object"""

    def __init__(self, *args, **kwargs):
        self.tags = {}
        "Dictionary of Tag objects, key = tag.name"

        super(DockerRepository, self).__init__(*args, **kwargs)

    def add_info(self, data: dict):
        """Accepts data in json format and parse it to receive repository info
        :param data: dictionary representing json object, dict
        """
        if type(data) is not dict:
            raise TypeError("'data' is not of type 'dict': Type '%s'" % type(data))

        self.update(data)

    def add_tags(self, data: dict):
        """Accepts data in json format and parse it to receive repository info
        :param data: dictionary representing json object, dict
        """
        if type(data) is not dict:
            raise TypeError("'data' is not of type 'dict': Type '%s'" % type(data))

        try:
            dct_list = data['results']
        except KeyError as exc:
            # TODO logging
            raise exc

        for tag_dct in dct_list:
            tag = Tag(tag_dct, self['namespace'], self['name'])
            self.tags[tag['name']] = tag
