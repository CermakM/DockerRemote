"""Command line interface for Docker Remote Manager"""

import argparse
import os
import sys

import logging
import tempfile
import textwrap

import docker_remote
from docker_remote.manager import DockerManager
from docker_remote.cli import pager


LOG = logging.getLogger('docker-remote')
DEBUG = bool(os.environ.get('DEBUG')) or False


def _init_logger(debug=False):
    """
    Initialize logger
    :param debug: show debugging messages (default False)
    """
    fd, logfile = tempfile.mkstemp(prefix='docker-remote_', suffix='.log')

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)-12s - [%(levelname)-8s]: %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=logfile,
                        filemode='w')

    if debug:
        sys.stdout.write("logging file: %s\n" % logfile)

    LOG.setLevel(logging.DEBUG)

    # Set up file handler to handle even debug messages
    log_level = logging.DEBUG

    # Set up stream handler to handle higher log level unless debug
    if not debug:
        log_level = logging.INFO
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(log_level)

    LOG.addHandler(stream_handler)

    LOG.debug("logging initialized")


def _init_pager() -> pager.Pager:
    """
    Check for available pager to be used
    :return: Pager object
    """
    if not hasattr(sys.stdin, 'isatty'):
        return pager.PlainPager()
    if not hasattr(sys.stdout, 'isatty'):
        return pager.PlainPager()
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return pager.PlainPager()
    if os.environ.get('TERM') in ('dumb', 'emacs'):
        return pager.PlainPager()
    if hasattr(os, 'system') and os.system('less 2>/dev/null') == 0:
        return pager.PipePager('less')

    # `more` cmd throws error 256 if <file> is not provided
    import tempfile
    fd, filename = tempfile.mkstemp()
    os.close(fd)  # It is not necessary to have descriptor opened
    try:
        if hasattr(os, 'system') and os.system('more "%s" 2>/dev/null' % filename) == 0:
            return pager.PipePager('more')
        else:
            return pager.TTYPager()
    finally:
        os.unlink(filename)  # Close the file

    # TODO: check what happens on win32


def main():
    # Bring logging stuff up ASAP
    _init_logger(debug=DEBUG)

    # Aliases
    repository_alias = ['repository', 'repo', 'r']
    search_alias = ['search', 's']
    description_alias = ['description', 'des', 'd']
    tag_alias = ['tags', 't']

    # Initialize argument parser
    parser = argparse.ArgumentParser(
        description='Docker Remote Manager - Manage remote docker repository',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help="Verbose output"
    )

    parser.add_argument(
        '-V', '--version', action='version',
        version="%(prog)s {version}".format(version=docker_remote.__version__),
        help='Show current version and exit'
    )

    parser.add_argument(
        '-u', '--login', action='store',
        help="Login credentials to Docker Hub in format 'username:password'"
    )

    # Initialize subparsers
    subparsers = parser.add_subparsers(dest='command',
                                       description="Docker Manager sub commands")

    parser_repo = subparsers.add_parser('repository',
                                        aliases=repository_alias,
                                        help="Manage Docker Hub repository information")

    parser_repo.add_argument(
        '-s', '--size', action='store_true',
        help="Show total repository size in MBs and exit"
    )

    parser_repo.add_argument(
        '-S', '--full-size', action='store_true',
        help="Show full repository size and exit"
    )

    # Search parser for search sub command
    parser_search = subparsers.add_parser('search', aliases=search_alias,
                                          help="Search Docker Hub repository")
    parser_search.add_argument(
        '-c', '--count', action='store_true',
        help="Output only number of results"
    )

    parser_search.add_argument(
        '-n', '--number', action='store', type=int,
        help="Limit number of pages of search results."
             "By default only first page is printed."  # TODO
    )

    # Sub parser for description sub command
    parser_description = subparsers.add_parser('description',
                                               aliases=description_alias,
                                               help="Manage Docker Hub "
                                                    "repository description")

    # Add --list option only for explicit usages - being able to show intention
    parser_description.add_argument(
        '-l', '--list', action='store_true', default=True,
        help="List description in Docker hub repository"
    )

    parser_description.add_argument(
        '--set', action='store', type=str,
        help="Set Docker Hub repository description (default --short)"
    )

    group_descr_len = parser_description.add_mutually_exclusive_group()
    group_descr_len.add_argument(
        '--short', action='store_true', default=True,
        help="Select only short description (default)"
    )

    group_descr_len.add_argument(
        '--long', action='store_true',
        help="Select only long description"
    )

    group_descr_len.add_argument(
        '--full', action='store_true',
        help="Select both short and long description"
    )

    # Sub parser for tags sub command
    parser_tags = subparsers.add_parser('tags', aliases=tag_alias,
                                        formatter_class=argparse.RawTextHelpFormatter,
                                        help="Manage Docker Hub repository tags")

    # Add --list option only for explicit usages - being able to show intention
    parser_tags.add_argument(
        '-l', '--list', action='store_true', default=True,
        help="List tags in Docker hub repository"
    )

    parser_tags.add_argument(
        '-c', '--count', action='store_true',
        help="Show only number of results and exits"
    )

    parser_tags.add_argument(
        '-d', '--delim', action='store', default=' ',
        help="Delimiter to separate text plain output"
    )

    parser_tags.add_argument(
        '--pretty', action='store_true',
        help="Pretty the output format"
    )

    parser_tags.add_argument(
        '--pop-back', action='store_true',
        help=textwrap.dedent('''\
        Remove tags from Docker Hub repository (oldest first)
        Note: Login is necessary
        ''')
    )

    parser_tags.add_argument(
        '--pop-front', action='store_true',
        help=textwrap.dedent('''\
        Remove tags from Docker Hub repository (newest first)
        Note: Login is necessary
        ''')
    )

    parser_tags.add_argument(
        '--pop-all', action='store_true',
        help=textwrap.dedent('''\
        Remove all tags from Docker Hub repository
        Note: Login is necessary
        ''')
    )

    parser_tags.add_argument(
        '-y', '--assumeyes', action='store_true', dest='confirm',
        default=None,
        help="Automatically answer 'yes' to all questions"
    )

    parser_tags.add_argument(
        '--assumeno', action='store_false', dest='confirm',
        default=None,
        help="Automatically answer 'no' to all questions"
    )

    group_tag_num = parser_tags.add_mutually_exclusive_group()
    group_tag_num.add_argument(
        '-n', '--number', action='store', type=int,
        help=textwrap.dedent('''\
        Select specific number of tags.
        If combined with the `--list` argument, lists `n` newest tags.
        ''')
    )

    group_tag_num.add_argument(
        '-k', '--keep', action='store', type=int,
        help="Opposite of -n, specify number of tags to be kept"
    )

    group_tag_num.add_argument(
        '-t', '--tag', action='store', type=str,
        help="Select a tag specified by id (name)"
    )

    group_tag_num.add_argument(
        '-a', '--all', action='store_const', const=-1,
        help="Select all tags in Docker Hub repository (default)"
    )

    # Last argument should be repository - positional argument
    parser.add_argument(
        'repository', action='store', type=str,
        help="Namespace and repository specification in format 'namespace/repository'"
    )

    # Initialize
    # ----------

    _pager = _init_pager()

    # Parse arguments and initialize DockerManager
    # --------------------------------------------

    args = parser.parse_args()

    # Set up parsed arguments
    namespace, repository = "library", ""
    repository_split = args.repository.lower().split('/')
    if len(repository_split) == 2:
        namespace, repository = repository_split
    else:
        repository, = repository_split
        if args.verbose:
            LOG.info("namespace not provided, "
                     "searching for official repositories",
                     file=sys.stderr)

    if args.login is not None:
        username, password = args.login.split(':')
    else:
        username, password = None, None

    # Necessary to avoid creating repository
    is_search = args.command in search_alias

    hub = DockerManager(repository=repository, namespace=namespace,
                        search=is_search,
                        username=username, password=password,
                        verbose=args.verbose, debug=DEBUG)  # FIXME - turn off debug

    if args.verbose and not is_search:
        hub.print_namespace()

# Handle search

    if is_search:
        LOG.info("Searching Docker Hub repository for: %s\n" % args.repository)

        if args.count:
            hub.print_nof_search_results(query=args.repository)
        else:
            search = hub.search(query=args.repository, page_lim=args.number)
            _pager("\n".join(search))

# Handle repository

    elif args.command in repository_alias:
        if args.size or args.full_size:
            hub.print_repo_size(full=args.full_size)


# Handle description

    elif args.command in description_alias:
        args.short = not args.long
        if args.full:
            args.long = args.short

        hub.print_description(short=args.short, full=args.long)

# Handle tags

    elif args.command in tag_alias:

        args.format = 'plain' if not args.pretty else 'pretty'

        if args.pop_back or args.pop_front:
            reverse = True if args.pop_front else False

            if not any([args.tag, args.number, args.keep, args.all]):
                LOG.error("argument missing, choose from "
                          "[--tag, --number, --keep, --all])")
            if args.tag:
                hub.remove_tag(args.tag, confirmation=args.confirm)
            else:
                if args.keep:
                    repo_tag_count = hub.get_tag_count()
                    if args.keep > repo_tag_count:
                        LOG.info("There are no tags to be removed")
                        exit(0)
                    n = repo_tag_count - args.keep
                else:
                    n = args.number if args.number else args.all

                hub.remove_tags(n, confirmation=args.confirm,
                                reverse=reverse)
        if args.pop_all:

            hub.remove_tags(-1, confirmation=args.confirm)

        elif args.count:
            hub.print_tag_count()

        else:
            # args.list true by default
            if args.tag:
                hub.print_tag_info(args.tag)
            else:
                hub.print_tags(args.number, fmt=args.format, delim=args.delim)


if __name__ == '__main__':
    main()
