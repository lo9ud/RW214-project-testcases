from typing import Any, Callable, Final

TABULATE_ENABLED: Final[bool] = False
try:
    from tabulate import tabulate

    def _tabulate(tabular_data: "list[list[Any]]") -> str:  # type: ignore
        return tabulate(tabular_data, tablefmt="fancy_grid") + "\n"

    TABULATE_ENABLED = True  # type: ignore
except ImportError:

    def _tabulate(tabular_data: "list[list[Any]]") -> str:  # type: ignore
        raise ImportError(
            "Tabulate not found, please install tabulate to use this feature."
        )

    print("Tabulate not found, using custom tabulate instead.")


def custom_tabulate(tabular_data: "list[list[Any]]"):
    col_widths = [max(len(str(cell)) for cell in col) for col in zip(*tabular_data)]
    return (
        "\n".join(
            " | ".join(f"{str(cell):<{col_widths[i]}}" for i, cell in enumerate(row))
            for row in tabular_data
        )
        + "\n"
    )


def set_tabulate_enabled(enabled: bool) -> None:
    global TABULATE_ENABLED
    TABULATE_ENABLED = enabled  # type: ignore


class _TableMaker:
    def __new__(cls) -> "_TableMaker":
        if not hasattr(cls, "instance"):
            cls.instance = super(_TableMaker, cls).__new__(cls)
        return cls.instance

    def __call__(self, tabular_data: "list[list[Any]]") -> str:
        global TABULATE_ENABLED
        if TABULATE_ENABLED:
            return _tabulate(tabular_data)
        return custom_tabulate(tabular_data)


TableMaker: Callable[["list[list[Any]]"], str] = _TableMaker()
