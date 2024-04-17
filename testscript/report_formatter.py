import json
from typing import Any

from common import Direction, Status, ex_v_fd
from table_maker import TableMaker
from testcase import Testcase, TestSet


class OutputFormatter:
    def format(
        self,
        testset: TestSet,
        show_passing: bool,
        details: bool,
    ) -> str:
        return f"Report: {testset}"


class TableFormatter(OutputFormatter):

    def format(
        self,
        testset: TestSet,
        show_passing: bool,
        details: bool,
    ) -> str:
        def get_table(testcase: Testcase) -> "list[list[Any]]":
            if testcase.result:
                afr_ex, afr_fd = ex_v_fd(
                    testcase.result.expected_afr, testcase.result.recieved_afr
                )
                brf_ex, brf_fd = ex_v_fd(
                    testcase.result.expected_brf, testcase.result.recieved_brf
                )
                table_b2t = [
                    ["Direction", "B2T"],
                    [
                        "Result",
                        "PASSED" if testcase.passed(Direction.B2T) else "FAILED",
                    ],
                    ["Input", testcase.result.input_brf.replace("\n", r"\n").strip()],
                    [
                        "Expected",
                        testcase.result.expected_afr.replace("\n", r"\n").strip(),
                    ],
                    [
                        "Actual",
                        testcase.result.recieved_afr.replace("\n", r"\n").strip(),
                    ],
                    ["Diff", afr_ex + "\n" + afr_fd],
                ]
                table_t2b = [
                    ["Direction", "T2B"],
                    [
                        "Result",
                        "PASSED" if testcase.passed(Direction.T2B) else "FAILED",
                    ],
                    ["Input", testcase.result.input_afr.replace("\n", r"\n").strip()],
                    [
                        "Expected",
                        testcase.result.expected_brf.replace("\n", r"\n").strip(),
                    ],
                    [
                        "Actual",
                        testcase.result.recieved_brf.replace("\n", r"\n").strip(),
                    ],
                    ["Diff", brf_ex + "\n" + brf_fd],
                ]
                return [table_b2t, table_t2b]
            else:
                return [[], []]

        ret = ""
        for testcase in testset:
            if not (testcase.status != Status.PASSED or show_passing):
                continue
            ret += "\n"
            ret += f"Name: {testcase.name}\n"
            if details:
                ret += f"Description: {testcase.description}\n"
                ret += f"Level: {testcase.level}\n"
                ret += f"Status: {testcase.status.name}\n"
                b2t, t2b = get_table(testcase)
                if not testcase.passed(Direction.B2T) or show_passing:
                    ret += TableMaker(b2t) + "\n"
                if not testcase.passed(Direction.T2B) or show_passing:
                    ret += TableMaker(t2b) + "\n"
            elif testcase.result:
                afr_ex, afr_fd = ex_v_fd(
                    testcase.result.expected_afr, testcase.result.recieved_afr
                )
                brf_ex, brf_fd = ex_v_fd(
                    testcase.result.expected_brf, testcase.result.recieved_brf
                )
                ret += f"Status: {testcase.status.name}\n"
                if not testcase.passed(Direction.B2T) or show_passing:
                    ret += "Expected: " + afr_ex + "\n"
                    ret += "Recieved: " + afr_fd + "\n"
                if not testcase.passed(Direction.T2B) or show_passing:
                    ret += "Expected: " + brf_ex + "\n"
                    ret += "Recieved: " + brf_fd + "\n"
        return ret
