import json
import os
import sys
from pathlib import Path

from args import CreateArgs
from common import ALLOWED_TAGS


def create(args: CreateArgs):
    try:
        testcase_name: str = args.name or input("Enter testcase name: ")
        if not args.info:
            testcase_info: str = input("Enter testcase description: ")
        else:
            testcase_info = args.info

        if not args.level:
            testcase_level: str = input("Enter testcase level: ")
        else:
            testcase_level = args.level

        if not args.tags:
            testcase_tags: list[str] = []
            for x in map(
                lambda x: x.strip().lower(),
                input("Enter testcase tags (colon separated): ").split(":"),
            ):
                if x not in ALLOWED_TAGS:
                    raise ValueError(f"Invalid tag: {x}")
                testcase_tags.append(x)
        else:
            testcase_tags = args.tags
    except ValueError as e:
        print(e)
        sys.exit(1)

    testcase_dir = Path("./testcases").resolve(strict=True) / (
        testcase_name.lower().replace(" ", "-")
    )
    if testcase_dir.exists():
        print("Testcase already exists")
        sys.exit(1)
    else:
        print(f"Creating testcase {testcase_name}")
        print("Creating directories...")
        os.makedirs(testcase_dir)
        print("Creating txt file...")
        with open(testcase_dir / "afr.txt", "w") as f:
            f.write(input("Afrikaans text:\n") or "// Afrikaans goes here\n")
        print("Creating brf file...")
        with open(testcase_dir / "brf.brf", "w") as f:
            f.write(input("Braille text:\n") or "// Braille output goes here\n")
        print("Creating manifest file...")
        with open(testcase_dir / "manifest.json", "w") as f:
            json.dump(
                {
                    "$schema": "../schema.json",
                    "name": testcase_name,
                    "desc": testcase_info,
                    "level": testcase_level,
                    "tags": testcase_tags,
                },
                f,
                indent=2,
            )
        print("Done")
        print(f"Testcase created at {testcase_dir}")
        print("Please edit the input, output and manifest files as required")
