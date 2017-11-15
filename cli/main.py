"""Command line interface for Docker Remote Manager"""

import argparse

from manager import DockerManager


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

    # Add arguments
    parser.add_argument(
        '-u', '--login', action='store',
        help="Login credentials to Docker Hub in format 'username:password'"
    )

    parser.add_argument(
        '-s', '--silent', action='store_true',
        help="Silent all unnecessary output"
    )

    # Initialize subparsers
    subparsers = parser.add_subparsers(dest='command',
                                       description="Docker Manager sub commands")

    # Sub parser for list-description sub command
    parser_description = subparsers.add_parser('description',
                                               help="Manage Docker Hub "
                                                    "repository description")

    parser_description.add_argument(
        '-l', '--list', action='store_true', default=True,
        help="List description in Docker hub repository"
    )

    group_descr_len = parser_description.add_mutually_exclusive_group()
    group_descr_len.add_argument(
        '--short', action='store_true', default=True,
        help="List only short description (default)"
    )

    group_descr_len.add_argument(
        '--long', action='store_true',
        help="List only long description"
    )

    group_descr_len.add_argument(
        '--full', action='store_true',
        help="list both short and long description"
    )

    # Sub parser for tags sub command
    parser_tags = subparsers.add_parser('tags', help="Manage tags "
                                                     "in Docker Hub repository")

    parser_tags.add_argument(
        '-l', '--list', action='store_true', default=True,
        help="List tags in Docker hub repository"
    )

    parser_tags.add_argument(
        '--remove', action='store_true',
        help="Remove tags from Docker Hub repository\n"
             "Note: Login credentials are necessary "
             "for this action to succeed"
    )

    group_lst_tag_count = parser_tags.add_mutually_exclusive_group()
    group_lst_tag_count.add_argument(
        '-n', '--count', action='store', type=int,
        help="List information about specific number of tags (from the newest)"
    )

    group_lst_tag_count.add_argument(
        '-t', '--tag', action='store', type=str,
        help="List information about the tag specified by id (name)"
    )

    group_lst_tag_count.add_argument(
        '-a', '-all', action='store_true',
        help="List all tags in Docker Hub repository (default)"
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
    namespace, repository = "", ""
    repository_split = args.repository.split('/')
    if len(repository_split) == 2:
        namespace, repository = repository_split
    else:
        repository, = repository_split

    if args.login is not None:
        username, password = args.login.split(':')
    else:
        username, password = None, None

    verbose = not args.silent

    hub = DockerManager(repository=repository, namespace=namespace,
                        username=username, password=password,
                        verbose=verbose, debug=True)  # FIXME - turn off debug

    if not args.silent:
        hub.print_namespace()

    # Choose from list actions
    if args.command == 'description':
        if args.list:
            args.short = not args.long
            if args.full:
                args.long = args.short

            hub.print_description(short=args.short, full=args.long)

    elif args.command == 'tags':
        if args.list:
            if args.tag:
                hub.print_tag_info(args.tag)
            else:
                hub.print_tags(args.count)


if __name__ == '__main__':
    main()
