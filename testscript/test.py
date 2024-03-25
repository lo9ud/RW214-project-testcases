import argparse
import difflib
import enum
import os
from pathlib import Path
from typing import Final
import json
import subprocess
import tempfile


TABULATE_ENABLED: Final[bool] = False
try:
    from tabulate import tabulate
    def _tabulate(tabular_data, *args, **kwargs):
        return tabulate(tabular_data, tablefmt="fancy_grid")

    TABULATE_ENABLED = True  # type: ignore
except ImportError:

    def _tabulate(tabular_data, *args, **kwargs):
        col_widths = [max(len(str(cell)) for cell in col) for col in zip(*tabular_data)]
        return "\n".join(
            " | ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row))
            for row in tabular_data
        )

VERBOSITY = 0

def ex_v_fd(ex: str, fd: str):
    class bcolors:
        ENDC = "\033[0m"
        RED_BACK = "\033[41m"
        GREEN_BACK = "\033[42m"

    ex = ex.replace("\r\n", "\n").replace("\n", r"\n")
    fd = fd.replace("\r\n", "\n").replace("\n", r"\n")

    def get_match(ex: str, fd: str) -> tuple[str, str]:
        # if len(ex) < len(fd):
        #     ex = ex + " " * (len(fd) - len(ex))
        # elif len(fd) < len(ex):
        #     fd = fd + " " * (len(ex) - len(fd))

        matcher = difflib.SequenceMatcher()
        matcher.set_seq1(ex)
        matcher.set_seq2(fd)
        mid = matcher.find_longest_match()
        if mid.size == 0:
            return (
                f"{bcolors.RED_BACK}{ex.ljust(max(len(ex), len(fd)))}{bcolors.ENDC}",
                f"{bcolors.RED_BACK}{fd.ljust(max(len(ex), len(fd)))}{bcolors.ENDC}",
            )
        else:
            l_ex, l_fd = get_match(ex[: mid.a], fd[: mid.b])
            r_ex, r_fd = get_match(ex[mid.a + mid.size :], fd[mid.b + mid.size :])
            return (
                (l_ex + bcolors.GREEN_BACK + ex[mid.a : mid.a + mid.size] + r_ex),
                (l_fd + bcolors.GREEN_BACK + fd[mid.b : mid.b + mid.size] + r_fd),
            )

    return get_match(ex, fd)

class Direction(enum.Enum):
    T2B = enum.auto()
    B2T = enum.auto()

    @staticmethod
    def from_str(label: str) -> "Direction":
        if label == "afrikaans-to-braille":
            return Direction.T2B
        elif label == "braille-to-afrikaans":
            return Direction.B2T
        else:
            raise ValueError(f"Invalid direction: {label}")


class Status(enum.Enum):
    READY = enum.auto()
    RUNNING = enum.auto()
    ERROR = enum.auto()
    PASSED = enum.auto()
    FAILED = enum.auto()
    COMPLETE = enum.auto()


class Testcase:
    class TestResult:
        def __init__(self, input: str, recieved: str, expected: str):
            self.input: str = input
            self.recieved: str = recieved
            self.expected: str = expected

        def __str__(self):
            return _tabulate(
                [
                    ["Input", self.input],
                    ["Output", self.recieved],
                    ["Expected", self.expected],
                    ["Diff", "\n".join(self.get_diff())],
                ],
                tablefmt="fancy_grid",
            )
            
        def get_status(self):
            if self.recieved.strip() == self.expected.strip():
                return Status.PASSED
            else:
                return Status.FAILED
            
        def get_diff(self):
            return ex_v_fd(self.expected, self.recieved)

    def __init__(self, root: Path):
        self.root: Path = root
        self.manifest: Path = self.root / "manifest.json"
        self.name: str = None  # type: ignore
        self.description: str = None  # type: ignore
        self.level: str = None  # type: ignore
        self.direction: Direction = None  # type: ignore
        self.tags: list[str] = None  # type: ignore
        self.result: Testcase.TestResult | str | None = None
        self.import_manifest()
        self.validate()
        self.status: Status = Status.READY

    def import_manifest(self):
        if self.manifest.exists():
            with open(self.manifest, "r") as f:
                data = json.load(f)
                self.name = data.get("name")
                self.description = data.get("description")
                self.level = data.get("level")
                self.direction = Direction.from_str(data.get("direction"))
                self.tags = data.get("tags")
        else:
            raise FileNotFoundError("Manifest file not found")

    def validate(self):
        # check types
        if not isinstance(self.name, str):
            raise TypeError("Invalid name")
        if not isinstance(self.description, str):
            raise TypeError("Invalid description")
        if not isinstance(self.level, str):
            raise TypeError("Invalid level")
        if not isinstance(self.direction, Direction):
            raise TypeError("Invalid direction")
        if not isinstance(self.tags, list):
            raise TypeError("Invalid tags")

        # check for valid level
        if not 0 <= float(self.level) <= 4.1:
            raise ValueError("Invalid level")

        # check for valid root
        if not self.root.exists():
            raise FileNotFoundError("Root does not exist")

        # check for valid tags
        if not sorted(list(set(self.tags))) == sorted(self.tags):
            raise ValueError("Duplicate tags")

    def run(self, proj_dir: Path):
        input_file = "input.txt" if self.direction == Direction.T2B else "input.brf"
        output_file = "output.brf" if self.direction == Direction.T2B else "output.txt"
        results_file = (
            "input_t2b.brf" if self.direction == Direction.T2B else "input_b2t.txt"
        )

        input_path = self.root / input_file
        output_path = self.root / output_file
        results_path = proj_dir / "out" / results_file

        self.status = Status.RUNNING
        p = subprocess.Popen(
            args=[
                "java",
                "-cp",
                "./bin",
                "src.Translate",
                "noGUI",
                "t2b" if self.direction == Direction.T2B else "b2t",
                self.level,
                input_path.absolute(),
            ],
            cwd=proj_dir,
            stderr=subprocess.PIPE,
        )
        try:
            p.wait(timeout=5)
            self.status = Status.COMPLETE
        except subprocess.TimeoutExpired:
            p.kill()
            self.result = p.stderr.read().decode() if p.stderr else "Unknown error"
            self.status = Status.ERROR
            return

        if p.returncode != 0:
            self.result = p.stderr.read().decode() if p.stderr else "Unknown error"
            self.status = Status.ERROR
            return

        with (
            open(output_path, "r") as out,
            open(input_path, "r") as _input,
            open(results_path, "r") as rec,
        ):
            self.result = Testcase.TestResult(
                input=_input.read(), recieved=rec.read(), expected=out.read()
            )
        self.status = self.result.get_status()
        results_path.unlink()


def main(args: argparse.Namespace):
    VERBOSITY = args.verbose
    proj_dir = Path(args.proj)
    testcase_dir = Path("./testcases")
    if not proj_dir.exists():
        raise FileNotFoundError("Project directory not found")
    testcases : list[Testcase] = []
    for testcase_folder in testcase_dir.iterdir():
        if not testcase_folder.is_dir():
            continue
        try:
            if not (
                any(
                    [
                        (testcase_folder / "input.txt").exists(),
                        (testcase_folder / "input.brf").exists(),
                    ]
                )
                and any(
                    [
                        (testcase_folder / "output.txt").exists(),
                        (testcase_folder / "output.brf").exists(),
                    ]
                )
                and (testcase_folder / "manifest.json").exists()
            ):
                raise FileNotFoundError("Invalid testcase")
            testcases.append(Testcase(testcase_folder))
        except Exception as e:
            print(f"Skipping {testcase_folder}: {e}")
            continue
        
    # Get testcase stats
    t2b = 0
    b2t = 0
    tags = {}
    levels = {}
    for testcase in testcases:
        if testcase.direction == Direction.T2B:
            t2b += 1
        else:
            b2t += 1
            
        if testcase.level not in levels:
            levels[testcase.level] = []
        levels[testcase.level].append(testcase)
        
        for tag in testcase.tags:
            if tag not in tags:
                tags[tag] = []
            tags[tag].append(testcase)
            
    term_width = os.get_terminal_size().columns - 1
    print(f"Found {len(testcases)} testcases")
    print(_tabulate(
        [
            ["T2B", t2b],
            ["B2T", b2t],
            *[["Level " + level, len(testcases)] for level, testcases in levels.items()],
            *[["Tag " + tag, len(testcases)] for tag, testcases in tags.items()],
            ["Total", len(testcases)],
        ],
    ))
    
    print("Running testcases")
    for i, testcase in enumerate(testcases):
        print(f"\rRunning testcase {i + 1}/{len(testcases)} ({100*(i + 1)/len(testcases):.0f}%)     ", end="")
        testcase.run(proj_dir)
    print("Done".ljust(80, " "))
    
    passed = [testcase for testcase in testcases if testcase.status == Status.PASSED]
    failed = [testcase for testcase in testcases if testcase.status == Status.FAILED]
    error = [testcase for testcase in testcases if testcase.status == Status.ERROR]
    
    print()
    print("-" * term_width)
    print("| Results |".center(term_width))
    print("-" * term_width)
    print()
    print(_tabulate(
        [
            ["Status", "Count", "Percentage"],
            ["Passed", len(passed), len(passed) / len(testcases) * 100],
            ["Failed", len(failed), len(failed) / len(testcases) * 100],
            ["Error", len(error), len(error) / len(testcases) * 100],
            ["Total", len(testcases), 100],
        ],
    ))
    print()
    print("-" * term_width)
    print("| Breakdown |".center(term_width, "-"))
    print("-" * term_width)
    print()
    print("| By Level |".center(term_width, "-"))
    print()
    print(_tabulate(
        [
            ["Level", "Passed", "Failed", "Error", "Total"],
            *[
                [
                    level,
                    len([testcase for testcase in testcases if testcase.level == level and testcase.status == Status.PASSED]),
                    len([testcase for testcase in testcases if testcase.level == level and testcase.status == Status.FAILED]),
                    len([testcase for testcase in testcases if testcase.level == level and testcase.status == Status.ERROR]),
                    len([testcase for testcase in testcases if testcase.level == level]),
                ]
                for level in levels.keys()
            ],
        ],
    ))
    print()
    print("| By Tag |".center(term_width, "-"))
    print()
    print(_tabulate(
        [
            ["Tag", "Passed", "Failed", "Error", "Total"],
            *[
                [
                    tag,
                    len([testcase for testcase in testcases if tag in testcase.tags and testcase.status == Status.PASSED]),
                    len([testcase for testcase in testcases if tag in testcase.tags and testcase.status == Status.FAILED]),
                    len([testcase for testcase in testcases if tag in testcase.tags and testcase.status == Status.ERROR]),
                    len([testcase for testcase in testcases if tag in testcase.tags]),
                ]
                for tag in tags.keys()
            ],
        ],
    ))
    print()
    print("| By Direction |".center(term_width, "-"))
    print()
    print(_tabulate(
        [
            ["Direction", "Passed", "Failed", "Error", "Total"],
            [
                "T2B",
                len([testcase for testcase in testcases if testcase.direction == Direction.T2B and testcase.status == Status.PASSED]),
                len([testcase for testcase in testcases if testcase.direction == Direction.T2B and testcase.status == Status.FAILED]),
                len([testcase for testcase in testcases if testcase.direction == Direction.T2B and testcase.status == Status.ERROR]),
                t2b,
            ],
            [
                "B2T",
                len([testcase for testcase in testcases if testcase.direction == Direction.B2T and testcase.status == Status.PASSED]),
                len([testcase for testcase in testcases if testcase.direction == Direction.B2T and testcase.status == Status.FAILED]),
                len([testcase for testcase in testcases if testcase.direction == Direction.B2T and testcase.status == Status.ERROR]),
                b2t,
            ],
        ],
    ))
    print()
    print("| Details |".center(term_width, "-"))
    print()
    print(_tabulate(
        [
            ["Name", "Description", "Level", "Tags", "Status"],
            *[[testcase.name, testcase.description, testcase.level, testcase.tags, testcase.status] for testcase in testcases],
        ],
    ))
    print()
    if args.verbose:
        print("-" * term_width)
        print("| Verbose |".center(term_width))
        print("-" * term_width)
        print()
        for testcase in testcases:
            print(f"Testcase: {testcase.name}")
            print(f"Description: {testcase.description}")
            print(f"Level: {testcase.level}")
            print(f"Tags: {testcase.tags}")
            print(f"Status: {testcase.status.name}")
            print(testcase.result)
            print()
                
    print("-" * term_width)
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test script", epilog="Example: python test.py /path/to/project"
    )

    parser.add_argument("proj", type=str, help="project directory")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase output verbosity"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1",
    )
    parser.add_argument(
        "-p",
        "--pretty-print",
        action=argparse.BooleanOptionalAction,
        help="Pretty print the output",
    )
    args = parser.parse_args()
    main(args)
