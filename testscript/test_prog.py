import subprocess
import sys
from pathlib import Path

from args import TestArgs
from report_formatter import TableFormatter
from table_maker import TableMaker
from testcase import Testcase, TestSet
from testerror import TestError


def test(args: TestArgs):
    try:
        if args.debug:
            print("Resolving project directory")
        proj_dir = Path(args.proj).resolve(strict=True)
        if args.debug:
            print("Resolved project directory")
    except FileNotFoundError:
        if args.debug:
            print("Project directory resolution failed, using provided path")
        proj_dir = Path(args.proj)
    src_dir = proj_dir / "src"
    bin_dir = proj_dir / "bin"

    if not proj_dir.exists():
        print("The provided path does not exist.")
        print("Provided path:", proj_dir)
        return

    elif not proj_dir.stem.endswith("-RW214-project"):
        print("The provided path does not appear to be a valid project directory.")
        print(
            "Ensure the directory name ends with '-RW214-project'.\n\tFor example, '123456789-RW214-project'."
        )
        print("Provided path:", proj_dir)
        return

    if not all(proj_dir / ext for ext in ["src", "bin", "out"]):
        print("The provided path does not appear to be a valid project directory.")
        print("Ensure the directory contains 'src', 'bin', and 'out' subdirectories.")
        print("Provided path:", proj_dir)
        return

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
    print("Building project...")
    p = subprocess.Popen(
        args=["javac", *src_dir.glob("*.java"), "-d", bin_dir, "-Xlint"]
        + (["-verbose"] if args.debug else []),
        cwd=proj_dir,
        stderr=sys.stdout if args.debug else subprocess.PIPE,
    )
    total_compiled = 0
    while total_compiled < 12:
        # Try to compile 24 times 5 seconds each = 2 minutes total allowed time
        try:
            p.wait(timeout=5)
            if args.debug:
                print("Build successful")
            break
        except subprocess.TimeoutExpired:
            total_compiled += 1
            print("Compiling... ")
    else:
        print("Build failed due to timeout, please check your code and try again.")
    out = p.stdout.read().decode("utf-8") if p.stdout else "no output"
    err = p.stderr.read().decode("utf-8") if p.stderr else "no error output"
    if args.debug:
        print("stdout:\n", out)
        print("stderr:\n", err)
    else:
        for line in out.splitlines():
            if (
                "errors" in line
                or "warnings" in line
                or "error" in line
                or "warning" in line
            ) and args.debug:
                print(f"  {line}")
            if line.startswith("[wrote"):
                print("Compiled ", line.split()[1])
        else:
            print("No warnings")

    if p.returncode != 0:
        print(
            f"Build failed with return code {0 if p.returncode == None else p.returncode}, please check your code and try again."
        )
        return

    testcase_dir = Path("./testcases").resolve(strict=True)
    if not proj_dir.exists():
        raise FileNotFoundError("Project directory not found")
    testcases: TestSet = TestSet()
    for testcase_folder in testcase_dir.iterdir():
        if not testcase_folder.is_dir():
            continue
        try:
            if args.debug:
                print(f"Adding {testcase_folder}")
            testcases.add(Testcase(testcase_folder))
        except TestError as e:
            print(f"Skipping {testcase_folder}: {e}")
            continue

    print("Running testcases...")
    testcases.run(proj_dir, bin_dir, args.timeout, debug=args.debug)

    print(
        TableFormatter().format(
            testcases, args.show_passing, args.details, args.error_output
        )
    )

    def rec_del(p: Path):
        for f in p.iterdir():
            if f.is_dir():
                rec_del(f)
                f.rmdir()
            else:
                if p.name == ".gitkeep":
                    continue
                if args.debug:
                    print(f"Deleting {f}")
                f.unlink()

    rec_del(bin_dir)
