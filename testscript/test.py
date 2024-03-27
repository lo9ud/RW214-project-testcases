import argparse
import json
import os
from pathlib import Path
import sys
from typing import Final
from testcase import TestSet, Testcase
from common import Status, Direction
from table_maker import TableMaker
from testerror import TestError

##########################################################
VERSION_NUMBER : Final[tuple[int,int,int]] = (0,2,0)

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
        except TestError as e:
            print(f"Skipping {testcase_folder}: {e}")
            continue
    
    print(testcases.summary(verbosity=args.verbose))

    print("Running testcases")
    for i, testcase in enumerate(testcases):
        print(
            f"\rRunning testcase {i + 1}/{len(testcases)} ({100*(i + 1)/len(testcases):.0f}%)     ",
            end="",
        )
        testcase.run(proj_dir)
    print("Done")

    print(testcases.results(verbosity=args.verbose))


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
        print(testcases.summary(verbosity=args.verbose))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test script", epilog="Example: python test.py /path/to/project"
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
    create_parser.add_argument(
        '-n', '--name', type=str, help='Name of the testcase'
    )
    create_parser.add_argument(
        '-d', '--direction', type=str, help='Direction of the testcase'
    )
    create_parser.add_argument(
        '-i', '--info', type=str, help='Description of the testcase'
    )
    create_parser.add_argument(
        '-l', '--level', type=str, help='Level of the testcase'
    )
    create_parser.add_argument(
        '-t', '--tags', type=lambda x:list(x.split(":")), help='Tags of the testcase in the format "tag1:tag2:tag3"', 
    )
    
    args = parser.parse_args()
    print(f"Verbosity: {args.verbose}")
    match args.action:
        case "test":
            test(args)
        case "validate":
            validate(args)
        case "create":
            testcase_name = args.name or input("Enter testcase name: ")
            testcase_dir = Path("./testcases") / testcase_name
            if testcase_dir.exists():
                print("Testcase already exists")
                sys.exit(1)
            else:
                direction = Direction.from_str(args.direction or input("Enter direction (in/out): "))
                if direction == Direction.T2B:
                    out_name = "output.brf"
                    in_name = "input.txt"
                else:
                    out_name = "output.txt"
                    in_name = "input.brf"
                print(f"Creating testcase {testcase_name}")
                print("Creating directories...")
                os.makedirs(testcase_dir)
                print("Creating input file...")
                with open(testcase_dir / in_name, "w") as f:
                    f.write("// Input goes here\n")
                print("Creating output file...")
                with open(testcase_dir / out_name, "w") as f:
                    f.write("// Expected output goes here\n")
                print("Creating manifest file...")
                with open(testcase_dir / "manifest.json", "w") as f:
                    json.dump(
                        {
                            "$schema": "../schema.json",
                            "name": testcase_name,
                            "desc": args.info or "Enter description here",
                            "direction": direction.to_long(),
                            "level": args.level or "Enter level here",
                            "tags": args.tags or [],
                        },
                        f,
                        indent=2,
                    )
                print("Done")
                print(f"Testcase created at {testcase_dir}")
                print("Please edit the input, output and manifest files as required")
                
        case _:
            parser.print_help()
            sys.exit(1)
