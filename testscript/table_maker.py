from typing import Any, Callable, Final, Self

TABULATE_ENABLED: Final[bool] = False
try:
    from tabulate import tabulate

    def _tabulate(tabular_data: list[list[Any]]):
        return tabulate(tabular_data, tablefmt="fancy_grid")

    TABULATE_ENABLED = True  # type: ignore
except ImportError:

    def _tabulate(tabular_data: list[list[Any]]):
        col_widths = [max(len(str(cell)) for cell in col) for col in zip(*tabular_data)]
        return "\n".join(
            " | ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row))
            for row in tabular_data
        )


class _TableMaker:
    def __new__(cls, tablefmt: str = "fancy_grid") -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(_TableMaker, cls).__new__(cls)
        return cls.instance

    def __init__(self, tablefmt: str = "fancy_grid"):
        self.tablefmt: str = tablefmt

    def __call__(self, tabular_data: list[list[Any]]):
        return _tabulate(tabular_data)


TableMaker: Callable[[list[list[Any]]], str] = _TableMaker()
