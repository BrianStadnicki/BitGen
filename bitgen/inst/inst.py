from enum import Enum
import copy
import math
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from bitgen.inst import BsAdvance, BsBlock

from .. import config as cfg


class BsInstType(Enum):
    AND = 0
    OR = 1
    NOT = 2
    XOR = 3
    ADD = 4
    MATCHSTAR = 5
    SCANTHRU = 6
    ASSIGN = 7
    SEL = 8
    IF = 9
    WHILE = 10
    ADVANCE = 11
    TERNARY = 12
    MATCH = 13
    CALL = 14
    BLOCK = 15
    STATE = 16
    GRAPHBREAK = 17
    STREAMSTORE = 18
    STREAMLOAD = 19
    STREAMDEFINE = 20
    SCANTHRUSTREAM = 21
    STR = 22


class BsInst:
    def __init__(self, inst_type: BsInstType, operands: tuple[int] | tuple[int, int] | tuple["BsBlock", "BsBlock | None"] | tuple[list["BsInst"]] | tuple["BsInst"] | tuple[None] | tuple[str, str] | tuple[int, str] | tuple[str] | tuple[int | str], ret: int | list[int]) -> None:
        self.type = inst_type
        self.operands = operands
        self.ret = ret
        self.ret_type = "uint32_t "
        self.operation = ""
        self.comment = ""
        self.n_operand = 0
        self.stream_index = ""

    def get_var_name(self, var_map: dict[int | str | list[int], str], operand: int | str | list[int]) -> str | int | list[int]:
        operandname = var_map[operand] if operand in var_map else operand
        if operandname == "output.matches":
            return "bs_result"
        if operandname == "0":
            raise NotImplementedError("0 should be replaced by create_zeros")
            return "create_zeros(self.n_char, device = basic_stream.device)"
        if operandname == "1":
            raise NotImplementedError("1 should be replaced by create_ones")
        return operandname

    def get_var_name_cuda(self, var_map: dict[int | str | list[int], str] | None, operand: int | str | list[int]) -> int | str | list[int]:
        if var_map is None:
            return operand
        operandname = var_map[operand] if operand in var_map else operand
        if operandname == "input_stream":
            # operation on global input_stream will be replaced by local input_stream_unit
            return "input_stream_unit"
        if operandname == "bs_result":
            # operation on global bs_result will be replaced by local bs_result_unit
            return "bs_result_unit"
        if operandname == "output.matches":
            return "bs_result_unit"
        if operandname == "0":
            return "0U"
        if operandname == "1":
            return "0xFFFFFFFF"
        return operandname

    def update_var_define_map(self, ret: int | list[int], var_define_map: dict[int | str | list[int], int]) -> bool:
        if ret in var_define_map:
            var_define_map[ret] += 1
            self.ret_type = ""
            return False
        else:
            var_define_map[ret] = 1
            self.ret_type = "uint32_t "
            return True

    def lower_to_cuda(self, var_map: dict[int | str | list[int], str] | None, indent: str = "", var_define_map: dict[int | str | list[int], int] | None = None) -> str:
        if var_define_map is not None:
            self.update_var_define_map(self.ret, var_define_map)
        return ""

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__
    
    def deepcopy(self):
        return copy.deepcopy(self)

    def lower_to_bitstream(self, var_map: dict[int | str | list[int], str], indent: str = "") -> str:
        return ""

    def lower_to_python(self, var_map: dict[int | str | list[int], str], indent: str = "") -> str:
        return ""

    def lower_to_torch(self, var_map: dict[int | str | list[int], str], indent: str = "") -> str:
        return ""


def get_max_advance_offset(insts: list[BsInst]) -> int:
        max_advance_offset = 0
        if cfg.GLOBAL_CONFIG["pass_cc_advanced"]:
            for inst in insts:
                if inst.type == BsInstType.ADVANCE:
                    max_advance_offset = max(max_advance_offset, cast("BsAdvance", inst).operand2)
        else:
            for inst in insts:
                if inst.type == BsInstType.ADVANCE:
                    max_advance_offset += cast("BsAdvance", inst).operand2
        if max_advance_offset != 0:
            max_advance_offset = math.ceil(max_advance_offset / 32)
        return max_advance_offset
