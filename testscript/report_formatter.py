import json
import os
import re
from typing import Any

from common import Direction, Status, colorize, ex_v_fd
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
        error_output: bool = False,
    ) -> str:
        MAX_LEN = max(os.get_terminal_size().columns - 20, 80)

        def ellipsis_string(S, max_len=MAX_LEN):
            if len(S) > max_len:
                return S[: max_len - 3] + "..."
            return S

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
                    [
                        "Input",
                        ellipsis_string(
                            testcase.result.input_brf.replace("\n", r"\n").strip()
                        ),
                    ],
                    [
                        "Expected",
                        ellipsis_string(
                            testcase.result.expected_afr.replace("\n", r"\n").strip()
                        ),
                    ],
                    [
                        "Actual",
                        ellipsis_string(
                            testcase.result.recieved_afr.replace("\n", r"\n").strip()
                        ),
                    ],
                    [
                        "Diff",
                        colorize(ellipsis_string(afr_ex), "green")
                        + "\n"
                        + colorize(ellipsis_string(afr_fd), "green"),
                    ],
                ]
                table_t2b = [
                    ["Direction", "T2B"],
                    [
                        "Result",
                        "PASSED" if testcase.passed(Direction.T2B) else "FAILED",
                    ],
                    [
                        "Input",
                        ellipsis_string(
                            testcase.result.input_afr.replace("\n", r"\n").strip()
                        ),
                    ],
                    [
                        "Expected",
                        ellipsis_string(
                            testcase.result.expected_brf.replace("\n", r"\n").strip()
                        ),
                    ],
                    [
                        "Actual",
                        ellipsis_string(
                            testcase.result.recieved_brf.replace("\n", r"\n").strip()
                        ),
                    ],
                    [
                        "Diff",
                        colorize(ellipsis_string(brf_ex), "green")
                        + "\n"
                        + colorize(ellipsis_string(brf_fd), "green"),
                    ],
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
                    ret += TableMaker(b2t)
                if not testcase.passed(Direction.T2B) or show_passing:
                    ret += TableMaker(t2b)
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
            if (testcase.status != Status.PASSED or show_passing) and error_output:
                ret += (
                    f"Error: "
                    + "\n\t\t".join(
                        list(filter(lambda x: bool(x), testcase.err.split("\n")))
                        or ["Unknown error"]
                    )
                    + "\n"
                )
        return ret
