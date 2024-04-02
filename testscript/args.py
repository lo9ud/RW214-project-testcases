import argparse
from pathlib import Path
from typing import Final

##########################################################
VERSION_NUMBER: Final[tuple[int, int, int]] = (0, 3, 0)

VERSION_STR: Final[str] = ".".join(str(x) for x in VERSION_NUMBER)
##########################################################


def get_args(args: list[str]) -> tuple[argparse.Namespace, argparse.ArgumentParser]:
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
        "-t",
        "--timeout",
        type=int,
        help="Timeout for each testcase in seconds",
        default=10,
    )
    test_parser.add_argument(
        "-c",
        "--color",
        action=argparse.BooleanOptionalAction,
        help="Enable color in output",
        default=True,
    )

    output_group = test_parser.add_argument_group(
        "Output options", "Options for enabling output and setting output format"
    )
    output_group.add_argument(
        "--output-style",
        help="Set output style",
        choices=["table", "json", "report", "minimal"],
        default="table",
    )
    output_group.add_argument(
        "--breakdown",
        help="Show a breakdown of testcases",
        action="store_true",
        default=True,
    )
    output_group.add_argument(
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

    validate_parser = subparsers.add_parser("validate", help="Validate testcases")
    validate_parser.add_argument(
        "-c",
        "--color",
        action=argparse.BooleanOptionalAction,
        help="Enable color in output",
        default=True,
    )
    validate_parser.add_argument(
        "-p",
        "--pretty-print",
        action=argparse.BooleanOptionalAction,
        help="Pretty print the output",
    )

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
    create_parser.add_argument(
        "-c",
        "--color",
        action=argparse.BooleanOptionalAction,
        help="Enable color in output",
        default=True,
    )
    create_parser.add_argument(
        "-p",
        "--pretty-print",
        action=argparse.BooleanOptionalAction,
        help="Pretty print the output",
    )

    return parser.parse_args(args), parser


class ArgsWrapper:
    def __init__(self, args: argparse.Namespace):
        self.args: argparse.Namespace = args
        self.action: str = args.action
        self.color: bool = args.color
        self.pretty_print: bool = args.pretty_print

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
        self.output_style: str = args.output_style
        self.breakdown: bool = args.breakdown
        self.details: bool = args.details
        self.show_passing: bool = args.show_passing


class ValidateArgs(ArgsWrapper): ...


class CreateArgs(ArgsWrapper):
    def __init__(self, args: argparse.Namespace):
        super().__init__(args)
        self.name: str = args.name
        self.info: str = args.info
        self.level: str = args.level
        self.tags: list[str] = args.tags
