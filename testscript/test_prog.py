import subprocess
from pathlib import Path

from args import TestArgs
from report_formatter import TableFormatter
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
            if (
                "errors" in line
                or "warnings" in line
                or "error" in line
                or "warning" in line
            ):
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

    print("Running testcases...")
    testcases.run(proj_dir, bin_dir, args.timeout)
    print("Done")

    print(TableFormatter().format(testcases, args.show_passing, args.details))

    subprocess.run(["rm", "-rf", bin_dir], check=True)
