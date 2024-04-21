import argparse
from pathlib import Path
from typing import Final

##########################################################
VERSION_NUMBER: Final["tuple[int, int, int]"] = (0, 3, 0)

VERSION_STR: Final[str] = ".".join(str(x) for x in VERSION_NUMBER)
##########################################################


def get_args(args: "list[str]") -> "tuple[argparse.Namespace, argparse.ArgumentParser]":
    parser = argparse.ArgumentParser(
        description="Test script for the RW214 Braille-Afrikaans Translator project",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION_STR}",
    )

    parser.add_argument(
        "-c",
        "--no-color",
        help="Disable color output",
        action="store_false",
        dest="color",
        default=True,
    )

    parser.add_argument(
        "-p",
        "--no-pretty-print",
        help="Disable pretty print for tabular data",
        action="store_false",
        dest="pretty_print",
        default=True,
    )

    parser.add_argument(
        "--debug",
        help="Enable debug output",
        action="store_true",
        default=False,
    )
    subparsers = parser.add_subparsers(help="Action", dest="action")

    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("proj", type=str, help="project directory")
    test_parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        help="Timeout for each testcase in seconds",
        default=10,
    )

    test_parser.add_argument(
        "-e",
        "--error",
        help="Show error messages output by the compiler/program",
        action="store_true",
        default=False,
    )

    output_group = test_parser.add_argument_group(
        "Output options", "Options for enabling output and setting output format"
    )
    output_group.add_argument(
        "-d",
        "--details",
        help="Show details of testcases",
        action="store_true",
        default=False,
    )
    output_group.add_argument(
        "--show-passing",
        help="Show passing testcases in detail views",
        action="store_true",
        default=False,
    )

    subparsers.add_parser("validate", help="Validate testcases")

    create_parser = subparsers.add_parser("create", help="Create a new testcase")
    create_parser.add_argument("-n", "--name", type=str, help="Name of the testcase")
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

    return parser.parse_args(args), parser


class ArgsWrapper:
    def __init__(self, args: argparse.Namespace):
        self.args: argparse.Namespace = args
        self.action: str = args.action
        self.color: bool = args.color
        self.pretty_print: bool = args.pretty_print
        self.debug: bool = args.debug

    def get_args(self) -> argparse.Namespace:
        return self.args

    def pprint(self):
        width = max(map(len, vars(self.args).keys()))
        for k, v in vars(self.args).items():
            print(f"{k:>{width}}: {v}")


class TestArgs(ArgsWrapper):
    def __init__(self, args: argparse.Namespace):
        super().__init__(args)
        self.proj: Path = Path(args.proj)
        self.timeout: int = args.timeout
        self.details: bool = args.details
        self.show_passing: bool = args.show_passing
        self.error_output: bool = args.error


class ValidateArgs(ArgsWrapper): ...


class CreateArgs(ArgsWrapper):
    def __init__(self, args: argparse.Namespace):
        super().__init__(args)
        self.name: str = args.name
        self.info: str = args.info
        self.level: str = args.level
        self.tags: list[str] = args.tags
