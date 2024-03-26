from pathlib import Path
import json
import subprocess
from table_maker import TableMaker
from common import Status, Direction, ex_v_fd
import os

from testerror import TestError


class Testcase:
    class TestResult:
        def __init__(self, input: str, recieved: str, expected: str):
            self.input: str = input
            self.recieved: str = recieved
            self.expected: str = expected

        def __str__(self):
            return TableMaker(
                [
                    ["Input", self.input],
                    ["Output", self.recieved],
                    ["Expected", self.expected],
                    ["Diff", "\n".join(self.get_diff())],
                ]
            )

        def get_status(self):
            if self.recieved.strip() == self.expected.strip():
                return Status.PASSED
            else:
                return Status.FAILED

        def get_diff(self):
            return ex_v_fd(self.expected, self.recieved)

    def __init__(self, root: Path, strict: bool = True):
        self.root: Path = root
        self.manifest: Path = self.root / "manifest.json"
        self.name: str = None  # type: ignore
        self.description: str = None  # type: ignore
        self.level: str = None  # type: ignore
        self.direction: Direction = None  # type: ignore
        self.tags: list[str] = None  # type: ignore
        self.result: Testcase.TestResult | str | None = None
        self.import_manifest()
        if strict:
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
            raise TestError("Invalid name")
        if not isinstance(self.description, str):
            raise TestError("Invalid description")
        if not isinstance(self.level, str):
            raise TestError("Invalid level")
        if not isinstance(self.direction, Direction):
            raise TestError("Invalid direction")
        if not isinstance(self.tags, list):
            raise TestError("Invalid tags")

        # check for valid level
        if not 0 <= float(self.level) <= 4.1:
            raise TestError("Invalid level")

        # check for valid tags
        if not len(set(self.tags)) == len(self.tags):
            raise TestError("Duplicate tags")
        
        # check files
        # check for valid root
        if not self.root.exists():
            raise TestError("Root does not exist")
        # check for valid contents
        contents = list(path.name for path in self.root.iterdir() if path.is_file())
        if "manifest.json" not in contents:
            raise TestError("Manifest file not found")
        if self.direction == Direction.T2B:
            if "input.txt" not in contents:
                raise TestError("Input file 'input.txt' not found for direction 't2b'")
            if "output.brf" not in contents:
                raise TestError("Output file 'output.brf' not found for direction 't2b'")
        else:
            if "input.brf" not in contents:
                raise TestError("Input file 'input.brf' not found for direction 'b2t'")
            if "output.txt" not in contents:
                raise TestError("Output file 'output.txt' not found for direction 'b2t'")

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


class TestSet:
    def __init__(self, testcases: list[Testcase] = []) -> None:
        self.testcases = testcases
        self.complete = False
        
    def add(self, testcase: Testcase):
        if self.complete:
            raise ValueError("Test set complete")
        self.testcases.append(testcase)

    def run(self, proj_dir: Path):
        if self.complete:
            raise ValueError("Test set complete")
        for testcase in self.testcases:
            testcase.run(proj_dir)
        self.complete = True

    def summary(self, verbosity: int = 0) -> str:
        levels = {}
        tags = {}
        t2b = []
        b2t = []
        for testcase in self.testcases:
            if testcase.direction == Direction.T2B:
                t2b.append(testcase)
            else:
                b2t.append(testcase)

            if testcase.level not in levels:
                levels[testcase.level] = []
            levels[testcase.level].append(testcase)

            for tag in testcase.tags:
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(testcase)
                
        return TableMaker(
            [
                ["Type", "Count"],
                ["T2B", len(t2b)],
                ["B2T", len(b2t)],
            ]
            + (
                [
                    *[
                        ["Level " + level, len(_testcases)]
                        for level, _testcases in levels.items()
                    ],
                    *[
                        ["Tag " + tag, len(_testcases)]
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
    
    def __getitem__(self, index):
        return self.testcases[index]
    
    def results(self, verbosity):
        term_width = os.get_terminal_size().columns - 1
        
        levels = {}
        tags = {}
        t2b = []
        b2t = []
        for testcase in self.testcases:
            if testcase.direction == Direction.T2B:
                t2b.append(testcase)
            else:
                b2t.append(testcase)

            if testcase.level not in levels:
                levels[testcase.level] = []
            levels[testcase.level].append(testcase)

            for tag in testcase.tags:
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(testcase)
        
        passed = [testcase for testcase in self.testcases if testcase.status == Status.PASSED]
        failed = [testcase for testcase in self.testcases if testcase.status == Status.FAILED]
        error = [testcase for testcase in self.testcases if testcase.status == Status.ERROR]

        print()
        print("-" * term_width)
        print("| Results |".center(term_width))
        print("-" * term_width)
        print()
        print(
            TableMaker(
                [
                    ["Status", "Count", "Percentage"],
                    ["Passed", len(passed), len(passed) / len(self.testcases) * 100],
                    ["Failed", len(failed), len(failed) / len(self.testcases) * 100],
                    ["Error", len(error), len(error) / len(self.testcases) * 100],
                    ["Total", len(self.testcases), 100],
                ],
            )
        )
        print()
        print("-" * term_width)
        print("| Breakdown |".center(term_width, "-"))
        print("-" * term_width)
        print()
        print("| By Level |".center(term_width, "-"))
        print()
        print(
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
                ],
            )
        )
        print()
        print("| By Tag |".center(term_width, "-"))
        print()
        print(
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
                                [testcase for testcase in self.testcases if tag in testcase.tags]
                            ),
                        ]
                        for tag in tags.keys()
                    ],
                ],
            )
        )
        print()
        print("| By Direction |".center(term_width, "-"))
        print()
        print(
            TableMaker(
                [
                    ["Direction", "Passed", "Failed", "Error", "Total"],
                    [
                        "T2B",
                        len(
                            [
                                testcase
                                for testcase in self.testcases
                                if testcase.direction == Direction.T2B
                                and testcase.status == Status.PASSED
                            ]
                        ),
                        len(
                            [
                                testcase
                                for testcase in self.testcases
                                if testcase.direction == Direction.T2B
                                and testcase.status == Status.FAILED
                            ]
                        ),
                        len(
                            [
                                testcase
                                for testcase in self.testcases
                                if testcase.direction == Direction.T2B
                                and testcase.status == Status.ERROR
                            ]
                        ),
                        t2b,
                    ],
                    [
                        "B2T",
                        len(
                            [
                                testcase
                                for testcase in self.testcases
                                if testcase.direction == Direction.B2T
                                and testcase.status == Status.PASSED
                            ]
                        ),
                        len(
                            [
                                testcase
                                for testcase in self.testcases
                                if testcase.direction == Direction.B2T
                                and testcase.status == Status.FAILED
                            ]
                        ),
                        len(
                            [
                                testcase
                                for testcase in self.testcases
                                if testcase.direction == Direction.B2T
                                and testcase.status == Status.ERROR
                            ]
                        ),
                        b2t,
                    ],
                ],
            )
        )
        if 0 < verbosity <= 1:
            print()
            print("| Details |".center(term_width, "-"))
            print()
            print(
                TableMaker(
                    [
                        ["Name", "Description", "Level", "Tags", "Status"],
                        *[
                            [
                                testcase.name,
                                testcase.description,
                                testcase.level,
                                testcase.tags,
                                testcase.status,
                            ]
                            for testcase in self.testcases
                        ],
                    ],
                )
            )
            print()
        elif 1 < verbosity <= 2:
            print("-" * term_width)
            print("| Verbose |".center(term_width))
            print("-" * term_width)
            print()
            for testcase in self.testcases:
                print(f"Testcase: {testcase.name}")
                print(f"Description: {testcase.description}")
                print(f"Level: {testcase.level}")
                print(f"Tags: {testcase.tags}")
                print(f"Status: {testcase.status.name}")
                print(testcase.result)
                print()

        print("-" * term_width)
