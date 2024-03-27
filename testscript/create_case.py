import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from common import Direction

if TYPE_CHECKING:
    from args import CreateArgs


def create(args: CreateArgs):
    testcase_name = args.name or input("Enter testcase name: ")
    testcase_dir = Path("./testcases") / testcase_name
    if testcase_dir.exists():
        print("Testcase already exists")
        sys.exit(1)
    else:
        direction = Direction.from_str(
            args.direction or input("Enter direction (in/out): ")
        )
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
