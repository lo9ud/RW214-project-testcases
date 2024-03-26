import difflib
import enum

ALLOWED_TAGS = [
    "text",
    "numbers",
    "punctuation",
    "capitalization",
    "contractions",
    "long"
]

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
        return "afrikaans-to-braille" if self == Direction.T2B else "braille-to-afrikaans"

class Status(enum.Enum):
    READY = enum.auto()
    RUNNING = enum.auto()
    ERROR = enum.auto()
    PASSED = enum.auto()
    FAILED = enum.auto()
    COMPLETE = enum.auto()
    
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