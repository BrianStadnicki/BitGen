from .inst import BsInst, BsInstType


class BsGraphBreak(BsInst):
    def __init__(self, operands: tuple[None] = (None,), ret: int = -1):
        super().__init__(BsInstType.GRAPHBREAK, operands, ret)
        self.n_operand = 00
        self.ret = ret
        self.operation = "bs_graph_break"

    def lower_to_bitstream(self, var_map: dict[int | str | list[int], str], indent: str = "") -> str:
        code = f"{indent}{self.operation}"
        return code

    def lower_to_python(self, var_map: dict[int | str | list[int], str], indent: str = "") -> str:
        return ""

    def lower_to_torch(self, var_map: dict[int | str | list[int], str], indent: str = "") -> str:
        return ""

    def lower_to_cuda(self, var_map: dict[int | str | list[int], str] | None, indent: str = "", var_define_map: dict[int | str | list[int], int] | None = None) -> str:
        return ""
