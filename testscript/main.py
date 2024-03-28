import argparse

from args import CreateArgs, TestArgs, ValidateArgs
from common import set_color_enabled
from create_case import create
from table_maker import set_tabulate_enabled
from test_prog import test
from validate_cases import validate


def main(args: argparse.Namespace):
    set_color_enabled(args.color)
    set_tabulate_enabled(args.pretty_print)
    match args.action:
        case "test":
            test(TestArgs(args))
        case "validate":
            validate(ValidateArgs(args))
        case "create":
            create(CreateArgs(args))
        case _:
            pass


if __name__ == "__main__":
    print(
        "This file is not meant to be run directly. Use the 'python testscript' instead."
    )
