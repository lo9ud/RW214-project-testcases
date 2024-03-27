import sys
from pathlib import Path

from args import ValidateArgs
from testcase import Testcase, TestSet
from testerror import TestError


def validate(args: ValidateArgs):
    testcase_dir = Path("./testcases")
    testcases: TestSet = TestSet()
    bad = 0
    for testcase_folder in testcase_dir.iterdir():
        if not testcase_folder.is_dir():
            continue
        else:
            try:
                testcases.add(Testcase(testcase_folder))
            except TestError as e:
                print(f"Error in {testcase_folder}: {e}")
                bad += 1
    if bad:
        sys.exit(1)
    elif args.verbose:
        print(testcases.summary(verbosity=args.verbose))
