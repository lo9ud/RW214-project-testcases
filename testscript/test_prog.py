import subprocess
from pathlib import Path

from args import TestArgs
from table_maker import TableMaker
from testcase import Testcase, TestSet
from testerror import TestError


def test(args: TestArgs):
    proj_dir = Path(args.proj)
    src_dir = proj_dir / "src"
    bin_dir = Path.cwd() / "bin"

    print(
        TableMaker(
            [
                ["Project directory", proj_dir],
                ["Source directory", src_dir],
                ["Binary directory", bin_dir],
            ],
        )
    )

    # Build the project
    print("Building project...", end=" ")
    p = subprocess.Popen(
        args=[
            "javac",
            src_dir / "Translate.java",
            "-d",
            bin_dir,
            "-Xlint",
            "-Xdoclint:all",
        ],
        cwd=proj_dir,
        stderr=subprocess.PIPE,
    )
    p.wait()
    print("Done")
    out = None
    if p.stderr:
        out = p.stderr.read().decode("utf-8").splitlines()
        for line in out:
            if "errors" in line or "warnings" in line:
                print(f"  {line}")
                break
        else:
            print("No warnings")

    if p.returncode != 0:
        print("Build failed")
        return
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

    print(testcases.summary(verbosity=0))

    print("Running testcases...")
    testcases.run(proj_dir, bin_dir)
    print("Done")

    print(testcases.results(verbosity=args.verbose))

    if args.verbose:
        print("Cleaning up...")
    subprocess.run(["rm", "-rf", bin_dir], check=True)
    if args.verbose:
        print("Done")

    print(
        "If your results appear incorrect, please re-run the test with verbosity enabled ('-vvv') to see the output of each testcase."
    )
    print(
        "If you believe the testcases are incorrect, please run 'python testscript validate' to check for errors in the testcases."
    )
