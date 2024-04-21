import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Literal, Union

from args import TestArgs
from common import ALLOWED_TAGS, Direction, Status
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
            self.time: float = 0

        def to_dict(self):
            return {
                "input_afr": self.input_afr,
                "recieved_brf": self.recieved_brf,
                "expected_afr": self.expected_afr,
                "input_brf": self.input_brf,
                "recieved_afr": self.recieved_afr,
                "expected_brf": self.expected_brf,
            }

        def get_status(self, direction: Direction) -> Status:
            if direction == Direction.T2B:
                return (
                    Status.PASSED
                    if (self.expected_brf == self.recieved_brf)
                    else Status.FAILED
                )
            elif direction == Direction.B2T:
                return (
                    Status.PASSED
                    if (self.expected_afr == self.recieved_afr)
                    else Status.FAILED
                )

    def __init__(self, root: Path, strict: bool = True):
        self.root: Path = root
        self.manifest: Path = self.root / "manifest.json"
        self.name: str = None  # type: ignore
        self.description: str = None  # type: ignore
        self.level: str = None  # type: ignore
        self.result: Union[Testcase.TestResult, None] = None
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

    def to_dict(
        self,
    ) -> 'dict[ Literal["name","description","level","tags","status","output","error","time","result",],Any,]':
        return {
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "status": self.status,
            "output": self.out,
            "error": self.err,
            "time": self.time,
            "result": self.result.to_dict() if self.result else None,
        }

    def import_manifest(self):
        if self.manifest.exists():
            with open(self.manifest, "r") as f:
                data = json.load(f)
                self.name = data.get("name")
                self.description = data.get("desc")
                self.level = data.get("level")
                # check types
                if not isinstance(self.name, str):
                    raise TestError("Invalid name")
                if not isinstance(self.description, str):
                    raise TestError("Invalid description")
                if not isinstance(self.level, str):
                    raise TestError("Invalid level")
        else:
            raise FileNotFoundError("Manifest file not found")

    def validate(self):
        # check for valid level
        if not 0 <= float(self.level) <= 4.1:
            raise TestError("Invalid level")

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

        with open(self.root / afr_name, "r") as afr_file, open(
            self.root / brf_name, "r"
        ) as brf_file:
            afr = afr_file.read()
            brf = brf_file.read()
            if not afr.strip() or not brf.strip():
                raise TestError("Test file(s) empty")

    def run(self, proj_dir: Path, bin_dir: Path, timeout: float) -> None:
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
            start_time = time.perf_counter()
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
                p.wait(timeout=timeout)
                self.status = Status.COMPLETE
            except subprocess.TimeoutExpired:
                p.kill()
                print(self.out + self.err)
                self.status = Status.ERROR
                return
            finally:
                self.time = time.perf_counter() - start_time

            if p.returncode != 0:
                self.status = Status.ERROR

            self.err = p.stderr.read().decode() if p.stderr else "Unknown error"
            self.out = p.stdout.read().decode() if p.stdout else "Unknown error"

            try:
                with open(expected_path, "r", encoding="utf-8") as out, open(
                    input_path, "r", encoding="utf-8"
                ) as _input, open(results_path, "r", encoding="utf-8") as rec:
                    results[context["direction"]]["input"] = _input.read()
                    results[context["direction"]]["expected"] = out.read()
                    results[context["direction"]]["recieved"] = rec.read()
            except UnicodeDecodeError:
                self.status = Status.ERROR
                results[context["direction"]]["input"] = "UnicodeDecodeError"
                results[context["direction"]]["expected"] = "UnicodeDecodeError"
                results[context["direction"]]["recieved"] = "UnicodeDecodeError"
                return
            except FileNotFoundError:
                self.status = Status.ERROR
                results[context["direction"]]["input"] = "File not found"
                results[context["direction"]]["expected"] = "File not found"
                results[context["direction"]]["recieved"] = "File not found"
                return
            finally:
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
        if self.status == Status.COMPLETE:
            self.status = (
                Status.PASSED
                if (
                    self.result.get_status(Direction.B2T) == Status.PASSED
                    and self.result.get_status(Direction.T2B) == Status.PASSED
                )
                else Status.FAILED
            )


class TestSet:
    def __init__(self, testcases: "list[Testcase]" = []) -> None:
        self.testcases = testcases
        self.complete = False

    def __iter__(self):
        return iter(self.testcases)

    def __len__(self):
        return len(self.testcases)

    def __getitem__(self, index: int) -> Testcase:
        return self.testcases[index]

    @property
    def time(self) -> float:
        return sum(testcase.time for testcase in self.testcases)

    @property
    def passed(self) -> int:
        return len(
            [
                testcase
                for testcase in self.testcases
                if testcase.status == Status.PASSED
            ]
        )

    @property
    def failed(self) -> int:
        return len(
            [
                testcase
                for testcase in self.testcases
                if testcase.status == Status.FAILED
            ]
        )

    @property
    def errored(self) -> int:
        return len(
            [testcase for testcase in self.testcases if testcase.status == Status.ERROR]
        )

    def to_dict(self) -> 'dict[Literal["testcases", "count", "status"], Any]':
        return {
            "testcases": [testcase.to_dict() for testcase in self.testcases],
            "count": len(self.testcases),
            "status": self.complete,
        }

    def add(self, testcase: Testcase):
        if self.complete:
            raise ValueError("Test set complete")
        self.testcases.append(testcase)

    def run(self, proj_dir: Path, bin_dir: Path, timeout: float):
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
            testcase.run(proj_dir, bin_dir, timeout)
            print(f"{testcase.status.name:>10} | {testcase.time:.2f}s")
        self.complete = True
        print(" " * (os.get_terminal_size().columns - 2) + "\r", end="")
        print("All testcases complete")

    def summary(self, args: TestArgs) -> "dict[str, int | float]":
        if not self.complete:
            raise ValueError("Test set incomplete")

        return {
            "Passed ": len(
                [
                    testcase
                    for testcase in self.testcases
                    if testcase.status == Status.PASSED
                ]
            ),
            "Failed ": len(
                [
                    testcase
                    for testcase in self.testcases
                    if testcase.status == Status.FAILED
                ]
            ),
            "Error ": len(
                [
                    testcase
                    for testcase in self.testcases
                    if testcase.status == Status.ERROR
                ]
            ),
            "Total ": len(self.testcases),
            "Time ": self.time,
        }

    def results(
        self, args: TestArgs
    ) -> 'list[dict[ Literal["name","description","level","tags","status","output","error","time","result",],Any,]]':
        if not self.complete:
            raise ValueError("Test set incomplete")
        ret: list[
            dict[
                Literal[
                    "name",
                    "description",
                    "level",
                    "tags",
                    "status",
                    "output",
                    "error",
                    "time",
                    "result",
                ],
                Any,
            ]
        ] = []
        for testcase in self.testcases:
            ret.append(testcase.to_dict())
        return ret
