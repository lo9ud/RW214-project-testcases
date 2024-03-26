import argparse
import os
from pathlib import Path
import sys
from typing import Final
from testcase import TestSet, Testcase
from common import Status, Direction
from table_maker import TableMaker
from testerror import TestError

##########################################################
VERSION_NUMBER : Final[tuple[int,int,int]] = (0,1,0)

VERSION_STR : Final[str] = ".".join(str(x) for x in VERSION_NUMBER)
##########################################################

def test(args: argparse.Namespace):
    proj_dir = Path(args.proj)
    testcase_dir = Path("./testcases")
    if not proj_dir.exists():
        raise FileNotFoundError("Project directory not found")
    testcases: TestSet = TestSet()
    for testcase_folder in testcase_dir.iterdir():
        if not testcase_folder.is_dir():
            continue
        try:
            testcases.add(
                Testcase(testcase_folder)
            )
        except Exception as e:
            print(f"Skipping {testcase_folder}: {e}")
            continue
    
    print(testcases.summary())

    print("Running testcases")
    for i, testcase in enumerate(testcases):
        print(
            f"\rRunning testcase {i + 1}/{len(testcases)} ({100*(i + 1)/len(testcases):.0f}%)     ",
            end="",
        )
        testcase.run(proj_dir)
    print("Done".ljust(80, " "))

    print(testcases.results(args.verbose))


def validate(args):
    testcase_dir = Path("./testcases")
    testcases: TestSet = TestSet()
    bad = 0
    for testcase_folder in testcase_dir.iterdir():
        if not testcase_folder.is_dir():
            continue
        else:
            try:
                testcases.add(
                    Testcase(testcase_folder)
                )
            except TestError as e:
                print(f"Error in {testcase_folder}: {e}")
                bad += 1
    if bad:
        sys.exit(1)
    else:
        print(testcases.summary())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test script", epilog="Example: python test.py /path/to/project"
    )
    parser.add_argument(
        "-v", "--verbose", action="count", help="Increase output verbosity"
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

    validate_parser = subparsers.add_parser("validate", help="Validate testcases")

    args = parser.parse_args()
    if args.action == "test":
        test(args)
    elif args.action == "validate":
        validate(args)
