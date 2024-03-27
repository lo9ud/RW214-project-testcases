import argparse
from pathlib import Path
from typing import Final

##########################################################
VERSION_NUMBER: Final[tuple[int, int, int]] = (0, 1, 0)

VERSION_STR: Final[str] = ".".join(str(x) for x in VERSION_NUMBER)
##########################################################


def get_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test script",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION_STR}",
    )

    subparsers = parser.add_subparsers(help="Action", dest="action")

    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("proj", type=str, help="project directory")
    test_parser.add_argument(
        "-p",
        "--pretty-print",
        action=argparse.BooleanOptionalAction,
        help="Pretty print the output",
    )
    test_parser.add_argument(
        "-v", "--verbose", action="count", help="Increase output verbosity", default=0
    )

    validate_parser = subparsers.add_parser("validate", help="Validate testcases")
    validate_parser.add_argument(
        "-v", "--verbose", action="count", help="Increase output verbosity", default=0
    )

    create_parser = subparsers.add_parser("create", help="Create a new testcase")
    create_parser.add_argument("-n", "--name", type=str, help="Name of the testcase")
    create_parser.add_argument(
        "-d", "--direction", type=str, help="Direction of the testcase"
    )
    create_parser.add_argument(
        "-i", "--info", type=str, help="Description of the testcase"
    )
    create_parser.add_argument("-l", "--level", type=str, help="Level of the testcase")
    create_parser.add_argument(
        "-t",
        "--tags",
        type=lambda x: list(x.split(":")),
        help='Tags of the testcase in the format "tag1:tag2:tag3"',
    )

    return parser.parse_args(args)


class TestArgs:
    def __init__(self, args: argparse.Namespace):
        self.action: str = args.action
        self.proj: Path = Path(args.proj)
        self.verbose: int = args.verbose


class ValidateArgs:
    def __init__(self, args: argparse.Namespace):
        self.verbose: int = args.verbose


class CreateArgs:
    def __init__(self, args: argparse.Namespace):
        self.name: str = args.name
        self.direction: str = args.direction
        self.info: str = args.info
        self.level: str = args.level
        self.tags: list[str] = args.tags
