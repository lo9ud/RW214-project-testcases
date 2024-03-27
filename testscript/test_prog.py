import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from testcase import Testcase, TestSet
from testerror import TestError

if TYPE_CHECKING:
    from args import TestArgs


def test(args: TestArgs):
    proj_dir = Path(args.proj)
    testcase_dir = Path("./testcases")
    if not proj_dir.exists():
        raise FileNotFoundError("Project directory not found")
    testcases: TestSet = TestSet()
    for testcase_folder in testcase_dir.iterdir():
        if not testcase_folder.is_dir():
            continue
        try:
            testcases.add(Testcase(testcase_folder))
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
