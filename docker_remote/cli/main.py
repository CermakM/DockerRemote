"""Command line interface for Docker Remote Manager"""

import argparse
import sys
import textwrap

import docker_remote
from docker_remote.manager import DockerManager


def _init_logger():
    # TODO
    pass


def main():
    # Bring logging stuff up

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
    parser_search = subparsers.add_parser('search',
                                          help="Search Docker Hub repository")
    parser_search.add_argument(
        '-c', '--count', action='store_true',
        help="Output only number of results"
    )

    parser_search.add_argument(
        '-n', '--number', action='store',
        help="Limit number of pages of search results."
             "By default only first page is printed."  # TODO
    )

    # Sub parser for description sub command
    parser_description = subparsers.add_parser('description',
                                               help="Manage Docker Hub "
                                                    "repository description")

    # Add --list option only for explicit usages - being able to show intention
    parser_description.add_argument(
        '-l', '--list', action='store_true', default=True,
        help="List description in Docker hub repository"
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
    parser_tags = subparsers.add_parser('tags',
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

    # TODO lots of other stuff

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
            print("[WARNING]: namespace not provided, "
                  "searching for official repositories",
                  file=sys.stderr)

    if args.login is not None:
        username, password = args.login.split(':')
    else:
        username, password = None, None

    # Necessary to avoid creating repository
    is_search = args.command == 'search'

    hub = DockerManager(repository=repository, namespace=namespace,
                        search=is_search,
                        username=username, password=password,
                        verbose=args.verbose, debug=True)  # FIXME - turn off debug

    if args.verbose and not is_search:
        hub.print_namespace()

    if is_search:
        print("Searching Docker Hub repository for: %s\n" % args.repository)

# Handle search

    if args.command == 'search':
        hub.search(args.repository, args.number)

# Handle repository

    elif args.command == 'repository':
        if args.size or args.full_size:
            hub.print_repo_size(full=args.full_size)


# Handle description

    elif args.command == 'description':
        args.short = not args.long
        if args.full:
            args.long = args.short

        hub.print_description(short=args.short, full=args.long)

# Handle tags

    elif args.command == 'tags':

        args.format = 'plain' if not args.pretty else 'pretty'

        if args.pop_back or args.pop_front:
            reverse = True if args.pop_front else False

            if not any([args.tag, args.number, args.keep, args.all]):
                parser.error("argument missing, choose from "
                             "[--tag, --number, --keep, --all])")
            if args.tag:
                hub.remove_tag(args.tag)
            else:
                if args.keep:
                    n = hub.get_tag_count() - args.keep
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
