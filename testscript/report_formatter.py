import json
from typing import Any

from common import Direction, Status
from table_maker import TableMaker
from testcase import Testcase, TestSet


class OutputFormatter:
    def format(
        self,
        testset: TestSet,
        breakdown: bool,
        show_passing: bool,
        details: bool,
    ) -> str:
        return f"Report: {testset}"


class JsonFormatter(OutputFormatter):

    def format(
        self,
        testset: TestSet,
        breakdown: bool,
        show_passing: bool,
        details: bool,
    ) -> str:
        return json.dumps(
            testset.to_dict(),
            indent=4,
        )


class TableFormatter(OutputFormatter):

    def format(
        self,
        testset: TestSet,
        breakdown: bool,
        show_passing: bool,
        details: bool,
    ) -> str:
        def make_row(testcase: Testcase) -> tuple[list[Any], list[Any]]:
            if testcase.result:
                return (
                    [
                        testcase.name,
                        testcase.level,
                        testcase.status,
                        testcase.result.expected_brf,
                        testcase.result.recieved_brf,
                        testcase.result.input_afr,
                    ],
                    [
                        testcase.name,
                        testcase.level,
                        testcase.status,
                        testcase.result.expected_afr,
                        testcase.result.recieved_afr,
                        testcase.result.input_brf,
                    ],
                )
            else:
                return (
                    [testcase.name, testcase.level, testcase.status, "", "", ""],
                    [testcase.name, testcase.level, testcase.status, "", "", ""],
                )

        data = [["Name", "Level", "Status", "Expected", "Recieved", "Input"]]
        for testcase in testset:
            if not (testcase.status != Status.PASSED or show_passing):
                continue
            data.extend(make_row(testcase))
        return TableMaker(data)


class ReportFormatter:
    def format(
        self,
        testset: TestSet,
        breakdown: bool,
        show_passing: bool,
        details: bool,
        detail_max_width: int = 40,
    ) -> str:
        import datetime

        def ellipsis(string: str, length: int = detail_max_width) -> str:
            return string[: length - 3] + "..." if len(string) > length else string

        return (
            f"Report for tests run on {datetime.datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}\n"
            + "\n"
            + f"{len(testset)} testcases run, {testset.passed} passed, {testset.failed} failed, {testset.errored} ended with an error.\n"
            + (
                "Testcase summary:\n"
                + "\n".join(
                    [
                        f"{testcase.name:>{max(len(case.name) for case in testset) + 1}}: {testcase.status}"
                        for testcase in testset
                        if (testcase.status != Status.PASSED or show_passing)
                    ]
                )
                if breakdown
                else ""
            )
            + (
                "\n\nTestcase Details\n"
                + "\n".join(
                    [
                        f"Name       : {testcase.name}\n"
                        f"Description: {testcase.description}\n"
                        f"Level      : {testcase.level}\n"
                        f"Tags       : {', '.join(testcase.tags)}\n"
                        f"Status     : {'PASSED' if testcase.passed(Direction.T2B) else 'FAILED':<{detail_max_width}} | {'PASSED' if testcase.passed(Direction.B2T) else 'FAILED':<{detail_max_width}}\n"
                        f"Input:     : {ellipsis(testcase.result.input_afr.strip()):<{detail_max_width}} | {ellipsis(testcase.result.input_brf.strip()):<{detail_max_width}}\n"
                        f"Expected   : {ellipsis(testcase.result.expected_brf.strip()):<{detail_max_width}} | {ellipsis(testcase.result.expected_afr.strip()):<{detail_max_width}}\n"
                        f"Recieved   : {ellipsis(testcase.result.recieved_brf.strip()):<{detail_max_width}} | {ellipsis(testcase.result.recieved_afr.strip()):<{detail_max_width}}\n"
                        for testcase in testset
                        if testcase.result
                        and (testcase.status != Status.PASSED or show_passing)
                    ]
                )
                if details
                else ""
            )
        )
