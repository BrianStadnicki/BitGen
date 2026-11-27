from .inst import BsInst, BsInstType


class BsStreamLoad(BsInst):
    def __init__(self, operands: tuple[int], ret: int = 0):
        super().__init__(BsInstType.STREAMLOAD, operands, ret)
        self.n_operand = 1
        if operands:
            self.operand1 = operands[0]
        else:
            self.operand1 = -1
        self.ret = ret
        self.operation = "bs_stream_load"
        self.stream_index = ""

    def lower_to_bitstream(self, var_map: dict[int | str | list[int], str], indent: str = "") -> str:
        code = f"{indent}{self.operation}"
        return code

    def lower_to_python(self, var_map: dict[int | str | list[int], str], indent: str = "") -> str:
        return ""

    def lower_to_torch(self, var_map: dict[int | str | list[int], str], indent: str = "") -> str:
        return ""

    def lower_to_cuda(self, var_map: dict[int | str | list[int], str] | None, indent: str = "", var_define_map: dict[int | str | list[int], int] | None = None) -> str:
        super().lower_to_cuda(var_map, indent, var_define_map)
        ret = self.get_var_name_cuda(var_map, self.ret)
        operand1 = self.get_var_name_cuda(var_map, self.operand1)
        code = f"{indent}{self.ret_type}{ret} = {operand1}[{self.stream_index}];"
        if self.comment != "":
            code += f" // {self.comment}"
        return code
