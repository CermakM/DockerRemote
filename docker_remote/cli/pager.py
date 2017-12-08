"""A collection of different types of pagers"""

import io
import logging
import sys

from abc import ABCMeta, abstractmethod


LOG = logging.getLogger('docker-remote.pager')


def _escape_stdout(text) -> str:
    """
    Escape non-encodable characters
    :param text: text stream
    :return: decoded text
    """
    encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'

    return text.encode(encoding, 'backslashreplace').decode(encoding)


class Pager:
    """This abstract base class serves as a convenient way to define return type `Pager`"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def __call__(self, *args, **kwargs):
        ...


class PlainPager(Pager):
    def __init__(self):
        """Initialize plain pager"""
        self.isatty = False
        super(PlainPager, self).__init__()

    def __call__(self, *args, **kwargs):
        """
        Write plain text to the output stream
        :param args: string-convertible items to be written to the output by pager
        :param kwargs: -
        """
        for arg in args:
            # Ensure string
            try:
                sys.stdout.write(_escape_stdout(arg))
            except (TypeError, AttributeError):
                LOG.debug("Cannot convert {arg} to string ... SKIPPED"
                          .format(arg=arg), file=sys.stderr)
                pass


class PipePager(Pager):
    def __init__(self, cmd):
        """Initialize pipe pager
        :param cmd: command to be used as a pipe
        """
        self.isatty = True
        self.cmd = cmd
        super(PipePager, self).__init__()

    def __call__(self, *args, **kwargs):
        """
        Write to the output stream using pipe pager
        :param args: string-convertible items to be written to the output by pager
        :param kwargs: -
        """
        import subprocess

        for arg in args:
            # Ensure string
            try:
                stream = _escape_stdout(arg)
            except (TypeError, AttributeError):
                LOG.debug("Cannot convert {arg} to string ... SKIPPED"
                          .format(arg=arg), file=sys.stderr)
                continue

            proc = subprocess.Popen(self.cmd, shell=True, stdin=subprocess.PIPE)
            try:
                with io.TextIOWrapper(proc.stdin) as pipe:
                    try:
                        pipe.write(stream + '\n')
                    except KeyboardInterrupt:
                        # Abandon rest of the results
                        # Note: pager is still in control of the terminal
                        pass
            except BrokenPipeError:
                pass  # Ignore broken pipe error
            while True:
                try:
                    proc.wait()
                    break
                except KeyboardInterrupt:
                    # Ignore ctrl-c to exit pager properly
                    pass


class TTYPager(Pager):
    def __init__(self):
        """Initialize tty pager"""
        self.isatty = True
        super(TTYPager, self).__init__()

    def __call__(self, *args, **kwargs):

        # TODO: atm just use plain pager

        PlainPager.__call__(*args, **kwargs)
