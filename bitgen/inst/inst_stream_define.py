from .inst import BsInst, BsInstType


class BsStreamDefine(BsInst):
    def __init__(self, operands: tuple[int], ret: int = 0):
        super().__init__(BsInstType.STREAMDEFINE, operands, ret)
        self.n_operand = 1
        self.operand1 = operands[0]
        self.ret = ret
        self.operation = "bs_stream_define"
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
        self.ret_type = "uint32_t* "
        ret = self.get_var_name_cuda(var_map, self.ret)
        operand1 = self.get_var_name_cuda(var_map, self.operand1)
        code = f"{indent}{self.ret_type}{ret} = {operand1} + {self.stream_index};"
        if self.comment != "":
            code += f" // {self.comment}"
        return code
