import difflib
import enum
from typing import Literal

COLOR_ENABLED = True

ALLOWED_TAGS = set(
    [
        "text",
        "numbers",
        "punctuation",
        "capitals",
        "contractions",
        "long",
        "diacritics",
    ]
)


def set_color_enabled(enabled: bool) -> None:
    global COLOR_ENABLED
    COLOR_ENABLED = enabled  # type: ignore


class Direction(enum.Enum):
    T2B = enum.auto()
    B2T = enum.auto()

    @staticmethod
    def from_str(label: str) -> "Direction":
        if label in ["t2b", "afrikaans-to-braille"]:
            return Direction.T2B
        elif label in ["b2t", "braille-to-afrikaans"]:
            return Direction.B2T
        else:
            raise ValueError(f"Invalid direction: {label}")

    def to_abv(self) -> str:
        return "t2b" if self == Direction.T2B else "b2t"

    def to_long(self) -> str:
        return (
            "afrikaans-to-braille" if self == Direction.T2B else "braille-to-afrikaans"
        )


class Status(enum.Enum):
    READY = enum.auto()
    RUNNING = enum.auto()
    ERROR = enum.auto()
    PASSED = enum.auto()
    FAILED = enum.auto()
    COMPLETE = enum.auto()


class bcolor(enum.Enum):
    ENDC = "\033[0m" if COLOR_ENABLED else ""
    RED_BACK = "\033[41m" if COLOR_ENABLED else ""
    GREEN_BACK = "\033[42m" if COLOR_ENABLED else ""


def colorize(text: str, color: Literal["red", "green"], omit_ends: bool = False) -> str:
    if COLOR_ENABLED:
        if color == "red":
            color_code = bcolor.RED_BACK.value
        elif color == "green":
            color_code = bcolor.GREEN_BACK.value
        else:
            raise ValueError(f"Invalid color: {color}, must be 'red' or 'green'")
        return f"{color_code}{text}" + (bcolor.ENDC.value if not omit_ends else "")
    else:
        return text


def ex_v_fd(ex: str, fd: str) -> "tuple[str, str]":
    ex = ex.replace("\r\n", "\n").replace("\n", r"\n")
    fd = fd.replace("\r\n", "\n").replace("\n", r"\n")

    def get_match(ex: str, fd: str) -> "tuple[str, str]":
        matcher = difflib.SequenceMatcher()
        matcher.set_seq1(ex)
        matcher.set_seq2(fd)
        mid = matcher.find_longest_match(0, len(ex), 0, len(fd))
        if mid.size == 0:
            return (
                colorize(ex.ljust(max(len(ex), len(fd))), "red", omit_ends=True),
                colorize(fd.ljust(max(len(ex), len(fd))), "red", omit_ends=True),
            )
        else:
            l_ex, l_fd = get_match(ex[: mid.a], fd[: mid.b])
            r_ex, r_fd = get_match(ex[mid.a + mid.size :], fd[mid.b + mid.size :])
            return (
                (
                    l_ex
                    + colorize(ex[mid.a : mid.a + mid.size], "green", omit_ends=True)
                    + r_ex
                ),
                (
                    l_fd
                    + colorize(fd[mid.b : mid.b + mid.size], "green", omit_ends=True)
                    + r_fd
                ),
            )

    a, b = get_match(ex, fd)
    if COLOR_ENABLED:
        return (a + bcolor.ENDC.value, b + bcolor.ENDC.value)
    return (a, b)
