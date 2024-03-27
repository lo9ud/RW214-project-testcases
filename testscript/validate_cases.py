import sys
from pathlib import Path
from typing import TYPE_CHECKING

from testcase import Testcase, TestSet
from testerror import TestError

if TYPE_CHECKING:
    from args import ValidateArgs


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
    else:
        print(testcases.summary(verbosity=args.verbose))
