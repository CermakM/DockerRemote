import pbr.version

from docker_remote.cli import main
from docker_remote.core import analyser
from docker_remote.core import repository
from docker_remote.manager import manager

__version__ = pbr.version.VersionInfo('docker-remote').version_string()
