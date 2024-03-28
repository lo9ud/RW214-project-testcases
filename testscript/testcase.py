import json
import os
import subprocess
from pathlib import Path

from common import ALLOWED_TAGS, Direction, Status, colorize, ex_v_fd
from table_maker import TableMaker
from testerror import TestError


class Testcase:
    class TestResult:
        def __init__(
            self,
            input_afr: str,
            recieved_brf: str,
            expected_afr: str,
            input_brf: str,
            recieved_afr: str,
            expected_brf: str,
        ):
            self.input_afr = input_afr
            self.recieved_brf = recieved_brf
            self.expected_afr = expected_afr
            self.input_brf = input_brf
            self.recieved_afr = recieved_afr
            self.expected_brf = expected_brf

        def __str__(self):
            return TableMaker(
                [
                    ["", "T2B", "B2T"],
                    ["Input", self.input_afr, self.input_brf],
                    ["Recieved", self.recieved_brf, self.recieved_afr],
                    ["Expected", self.expected_brf, self.expected_afr],
                    [
                        "Diff",
                        "\n".join(self.get_diff(self.expected_brf, self.recieved_brf)),
                        "\n".join(self.get_diff(self.expected_afr, self.recieved_afr)),
                    ],
                ]
            )

        def get_status(self, direction: Direction) -> Status:
            match (direction):
                case Direction.T2B:
                    return (
                        Status.PASSED
                        if (self.expected_brf == self.recieved_brf)
                        else Status.FAILED
                    )
                case Direction.B2T:
                    return (
                        Status.PASSED
                        if (self.expected_afr == self.recieved_afr)
                        else Status.FAILED
                    )

        def get_diff(self, ex: str, rec: str) -> tuple[str, str]:
            return ex_v_fd(ex, rec)

    def __init__(self, root: Path, strict: bool = True):
        self.root: Path = root
        self.manifest: Path = self.root / "manifest.json"
        self.name: str = None  # type: ignore
        self.description: str = None  # type: ignore
        self.level: str = None  # type: ignore
        self.tags: list[str] = None  # type: ignore
        self.result: Testcase.TestResult | None = None
        self.import_manifest()
        if strict:
            self.validate()
        self.status: Status = Status.READY
        self.out = ""
        self.err = ""

    def passed(self, direction: Direction) -> bool:
        if self.result is None:
            return False
        return self.result.get_status(direction) == Status.PASSED

    def import_manifest(self):
        if self.manifest.exists():
            with open(self.manifest, "r") as f:
                data = json.load(f)
                self.name = data.get("name")
                self.description = data.get("desc")
                self.level = data.get("level")
                self.tags = data.get("tags")
                # check types
                if not isinstance(self.name, str):
                    raise TestError("Invalid name")
                if not isinstance(self.description, str):
                    raise TestError("Invalid description")
                if not isinstance(self.level, str):
                    raise TestError("Invalid level")
                if not isinstance(self.tags, list):
                    raise TestError("Invalid tags")
        else:
            raise FileNotFoundError("Manifest file not found")

    def validate(self):
        # check for valid level
        if not 0 <= float(self.level) <= 4.1:
            raise TestError("Invalid level")

        # check for valid tags
        if not len(set(self.tags)) == len(self.tags):
            raise TestError("Duplicate tags")
        if not all(x in ALLOWED_TAGS for x in self.tags):
            raise TestError("Invalid tags: " + ", ".join(set(self.tags) - ALLOWED_TAGS))

        # check files
        # check for valid root
        if not self.root.exists():
            raise TestError("Root does not exist")
        # check for valid contents
        contents = list(path.name for path in self.root.iterdir() if path.is_file())
        if "manifest.json" not in contents:
            raise TestError("Manifest file not found")

        with open(self.root / "manifest.json", "r") as output_file:
            try:
                json.load(output_file)
            except json.JSONDecodeError:
                raise TestError("Invalid manifest file") from None

            output_file.seek(0)
            if not output_file.read().strip():
                raise TestError("Empty manifest file")

        afr_name = "afr.txt"
        brf_name = "brf.brf"

        if afr_name not in contents:
            raise TestError("Afrikaans file 'afr.txt' not found.")
        if brf_name not in contents:
            raise TestError("Braille file 'brf.brf' not found.")

        with (
            open(self.root / afr_name, "r") as afr_file,
            open(self.root / brf_name, "r") as brf_file,
        ):
            afr = afr_file.read()
            brf = brf_file.read()
            if not afr.strip() or not brf.strip():
                raise TestError("Test file(s) empty")

    def run(self, proj_dir: Path, bin_dir: Path) -> None:
        cases = {
            Direction.B2T: {
                "input": "brf.brf",
                "expected": "afr.txt",
                "recieved": "brf_b2t.txt",
                "direction": "b2t",
            },
            Direction.T2B: {
                "input": "afr.txt",
                "expected": "brf.brf",
                "recieved": "afr_t2b.brf",
                "direction": "t2b",
            },
        }
        results: dict[str, dict[str, str]] = {
            "t2b": {
                "input": "None",
                "expected": "None",
                "recieved": "None",
            },
            "b2t": {
                "input": "None",
                "expected": "None",
                "recieved": "None",
            },
        }
        for context in cases.values():
            input_path = self.root / context["input"]
            expected_path = self.root / context["expected"]
            results_path = proj_dir / "out" / context["recieved"]

            if not proj_dir.exists():
                raise FileNotFoundError("Project directory not found")
            if not bin_dir.exists():
                raise FileNotFoundError("Binary directory not found")
            if not input_path.exists():
                raise FileNotFoundError("Input file not found")

            if results_path.exists():
                results_path.unlink()

            self.status = Status.RUNNING
            p = subprocess.Popen(
                args=[
                    "java",
                    "-cp",
                    bin_dir.absolute(),
                    "src.Translate",
                    "noGUI",
                    context["direction"],
                    self.level,
                    input_path.absolute(),
                    # "--debug",
                ],
                cwd=proj_dir,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
            )
            self.err = p.stderr.read().decode() if p.stderr else "Unknown error"
            self.out = p.stdout.read().decode() if p.stdout else "Unknown error"
            try:
                p.wait(timeout=60)
                self.status = Status.COMPLETE
            except subprocess.TimeoutExpired:
                p.kill()
                print(self.out + self.err)
                self.status = Status.ERROR
                return

            if p.returncode != 0:
                self.err = p.stderr.read().decode() if p.stderr else "Unknown error"
                self.out = p.stdout.read().decode() if p.stdout else "Unknown error"
                self.status = Status.ERROR
                return

            with (
                open(expected_path, "r", encoding="utf-8") as out,
                open(input_path, "r", encoding="utf-8") as _input,
                open(results_path, "r", encoding="utf-8") as rec,
            ):
                results[context["direction"]]["input"] = _input.read()
                results[context["direction"]]["expected"] = out.read()
                results[context["direction"]]["recieved"] = rec.read()
            p.wait()
            results_path.unlink()

        self.result = self.TestResult(
            input_afr=results["t2b"]["input"],
            recieved_brf=results["t2b"]["recieved"],
            expected_brf=results["t2b"]["expected"],
            input_brf=results["b2t"]["input"],
            recieved_afr=results["b2t"]["recieved"],
            expected_afr=results["b2t"]["expected"],
        )
        self.status = (
            Status.PASSED
            if (
                self.result.get_status(Direction.B2T) == Status.PASSED
                and self.result.get_status(Direction.T2B) == Status.PASSED
            )
            else Status.FAILED
        )


class TestSet:
    def __init__(self, testcases: list[Testcase] = []) -> None:
        self.testcases = testcases
        self.complete = False

    def add(self, testcase: Testcase):
        if self.complete:
            raise ValueError("Test set complete")
        self.testcases.append(testcase)

    def run(self, proj_dir: Path, bin_dir: Path):
        if self.complete:
            raise ValueError("Test set complete")
        log_len = len(str(len(self.testcases)))
        for i, testcase in enumerate(self.testcases):
            print(
                f"\rRunning testcase | {i + 1:{log_len}}/{len(self.testcases):<{log_len}} | {testcase.name:>20} | ".ljust(
                    30
                ),
                end="",
            )
            testcase.run(proj_dir, bin_dir)
            print(" | Done!")
        self.complete = True

    def summary(self, verbosity: int = 0) -> str:
        levels: dict[str, list[Testcase]] = {}
        tags: dict[str, list[Testcase]] = {}
        for testcase in self.testcases:
            if testcase.level not in levels:
                levels[testcase.level] = []
            levels[testcase.level].append(testcase)

            for tag in testcase.tags:
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(testcase)

        return TableMaker(
            (
                [
                    *[
                        ["Level " + level, len(_testcases)]
                        for level, _testcases in levels.items()
                    ],
                    *[
                        ["Tag '" + tag + "'", len(_testcases)]
                        for tag, _testcases in tags.items()
                    ],
                    ["Total", len(self.testcases)],
                ]
                if verbosity > 0
                else []
            ),
        )

    def __iter__(self):
        return iter(self.testcases)

    def __len__(self):
        return len(self.testcases)

    def __getitem__(self, index: int) -> Testcase:
        return self.testcases[index]

    def results(self, verbosity: int) -> str:
        term_width = os.get_terminal_size().columns - 1
        ret: list[str] = ["", ""]
        levels: dict[str, list[Testcase]] = {}
        tags: dict[str, list[Testcase]] = {}
        for testcase in self.testcases:
            if testcase.level not in levels:
                levels[testcase.level] = []
            levels[testcase.level].append(testcase)

            for tag in testcase.tags:
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(testcase)

        passed = [
            testcase for testcase in self.testcases if testcase.status == Status.PASSED
        ]
        failed = [
            testcase for testcase in self.testcases if testcase.status == Status.FAILED
        ]
        error = [
            testcase for testcase in self.testcases if testcase.status == Status.ERROR
        ]
        ret.append("\n")
        ret.append("-" * term_width)
        ret.append("| Results |".center(term_width))
        ret.append("-" * term_width)
        ret.append("\n")
        ret += [
            (
                TableMaker(
                    [
                        ["Status", "Count", "Percentage"],
                        [
                            "Passed",
                            len(passed),
                            f"{len(passed) / len(self.testcases) * 100:.0f}%",
                        ],
                        [
                            "Failed",
                            len(failed),
                            f"{len(failed) / len(self.testcases) * 100:.0f}%",
                        ],
                        [
                            "Error",
                            len(error),
                            f"{len(error) / len(self.testcases) * 100:.0f}%",
                        ],
                        ["Total", len(self.testcases), "100%"],
                    ],
                )
            )
        ]
        if not failed and not error:
            ret.append(TableMaker([[colorize(" All testcases passed ", "green")]]))
            if verbosity < 1:
                return "\n".join(ret)
        ret.append("\n")
        ret.append("-" * term_width)
        ret.append("| Breakdown |".center(term_width, "-"))
        ret.append("-" * term_width)
        ret.append("\n")
        ret.append("| By Level |".center(term_width, "-"))
        ret.append("\n")
        ret += [
            (
                TableMaker(
                    [
                        ["Level", "Passed", "Failed", "Error", "Total"],
                        *[
                            [
                                level,
                                len(
                                    [
                                        testcase
                                        for testcase in self.testcases
                                        if testcase.level == level
                                        and testcase.status == Status.PASSED
                                    ]
                                ),
                                len(
                                    [
                                        testcase
                                        for testcase in self.testcases
                                        if testcase.level == level
                                        and testcase.status == Status.FAILED
                                    ]
                                ),
                                len(
                                    [
                                        testcase
                                        for testcase in self.testcases
                                        if testcase.level == level
                                        and testcase.status == Status.ERROR
                                    ]
                                ),
                                len(
                                    [
                                        testcase
                                        for testcase in self.testcases
                                        if testcase.level == level
                                    ]
                                ),
                            ]
                            for level in levels.keys()
                        ],
                        [
                            "Total",
                            len(passed),
                            len(failed),
                            len(error),
                            len(self.testcases),
                        ],
                    ],
                )
            )
        ]
        ret.append("\n")
        ret.append("| By Tag |".center(term_width, "-"))
        ret.append("\n")
        ret += [
            (
                TableMaker(
                    [
                        ["Tag", "Passed", "Failed", "Error", "Total"],
                        *[
                            [
                                tag,
                                len(
                                    [
                                        testcase
                                        for testcase in self.testcases
                                        if tag in testcase.tags
                                        and testcase.status == Status.PASSED
                                    ]
                                ),
                                len(
                                    [
                                        testcase
                                        for testcase in self.testcases
                                        if tag in testcase.tags
                                        and testcase.status == Status.FAILED
                                    ]
                                ),
                                len(
                                    [
                                        testcase
                                        for testcase in self.testcases
                                        if tag in testcase.tags
                                        and testcase.status == Status.ERROR
                                    ]
                                ),
                                len(
                                    [
                                        testcase
                                        for testcase in self.testcases
                                        if tag in testcase.tags
                                    ]
                                ),
                            ]
                            for tag in tags.keys()
                        ],
                        [
                            "Total",
                            len(passed),
                            len(failed),
                            len(error),
                            len(self.testcases),
                        ],
                    ],
                )
            )
        ]
        ret.append("\n")
        ret.append("| By Direction |".center(term_width, "-"))
        ret.append("\n")
        ret += [
            (
                TableMaker(
                    [
                        ["Direction", "Passed", "Failed", "Error", "Total"],
                        [
                            "T2B",
                            len(
                                [
                                    testcase
                                    for testcase in self.testcases
                                    if testcase.passed(Direction.T2B)
                                    and testcase.status == Status.PASSED
                                ]
                            ),
                            len(
                                [
                                    testcase
                                    for testcase in self.testcases
                                    if testcase.passed(Direction.T2B)
                                    and testcase.status == Status.FAILED
                                ]
                            ),
                            len(
                                [
                                    testcase
                                    for testcase in self.testcases
                                    if testcase.passed(Direction.T2B)
                                    and testcase.status == Status.ERROR
                                ]
                            ),
                            len(
                                [
                                    testcase
                                    for testcase in self.testcases
                                    if testcase.passed(Direction.T2B)
                                ]
                            ),
                        ],
                        [
                            "B2T",
                            len(
                                [
                                    testcase
                                    for testcase in self.testcases
                                    if testcase.passed(Direction.B2T)
                                    and testcase.status == Status.PASSED
                                ]
                            ),
                            len(
                                [
                                    testcase
                                    for testcase in self.testcases
                                    if testcase.passed(Direction.B2T)
                                    and testcase.status == Status.FAILED
                                ]
                            ),
                            len(
                                [
                                    testcase
                                    for testcase in self.testcases
                                    if testcase.passed(Direction.B2T)
                                    and testcase.status == Status.ERROR
                                ]
                            ),
                            len(
                                [
                                    testcase
                                    for testcase in self.testcases
                                    if testcase.passed(Direction.B2T)
                                ]
                            ),
                        ],
                        [
                            "Total",
                            len(passed),
                            len(failed),
                            len(error),
                            len(self.testcases),
                        ],
                    ],
                )
            )
        ]
        if 0 < verbosity <= 1:
            ret.append("\n")
            ret.append("| Details |".center(term_width, "-"))
            ret.append("\n")
            ret += [
                (
                    TableMaker(
                        [
                            ["Name", "Description", "Level", "Tags", "Status"],
                            *[
                                [
                                    testcase.name,
                                    testcase.description,
                                    testcase.level,
                                    testcase.tags,
                                    testcase.status.name,
                                ]
                                for testcase in self.testcases
                            ],
                        ],
                    )
                )
            ]
            ret.append("\n")
        elif 1 < verbosity:
            ret.append("-" * term_width)
            ret.append("| Verbose |".center(term_width))
            ret.append("-" * term_width)
            ret.append("\n")
            for testcase in self.testcases:
                ret.append(f"   Testcase : {testcase.name}")
                ret.append(f"Description : {testcase.description}")
                ret.append(f"      Level : {testcase.level}")
                ret.append(f"       Tags : {testcase.tags}")
                ret.append(
                    f"     Status : {colorize(testcase.status.name,'green' if testcase.status == Status.PASSED else 'red')}"
                )
                if testcase.status == Status.ERROR:
                    ret += [
                        f"Error: \n{'\n'.join(map(lambda x:'\t' + x,testcase.err.splitlines()))}"
                    ]
                ret.append(str(testcase.result))
                ret.append("\n")

        ret.append("-" * term_width)
        return "\n".join(ret)

    def validate(self):
        for testcase in self.testcases:
            testcase.validate()
        return True
