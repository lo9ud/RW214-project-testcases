import argparse

from args import CreateArgs, TestArgs, ValidateArgs
from common import set_color_enabled
from create_case import create
from test_prog import test
from validate_cases import validate


def main(args: argparse.Namespace):
    if hasattr(args, "verbose"):
        print(f"Verbosity: {args.verbose}")
    set_color_enabled(args.color)
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
