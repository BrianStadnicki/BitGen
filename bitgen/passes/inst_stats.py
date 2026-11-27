from typing import cast

from bitgen.inst import BsInstType
from bitgen.inst.inst import BsInst
from bitgen.inst.inst_block import BsBlock
from bitgen.inst.inst_block_while import BsWhile
from bitgen.inst.inst_str import BsStr
from bitgen.inst.inst_block_if import BsIf

from .pass_utils import inst_name_map
from ..tool import global_timer


class inst_stats_pass:
    def __init__(self):
        self.pass_name = "inst_stats"

    def inst_stats(self, insts: list[BsInst], result: dict[str, int]):
        result["inst"] = result.get("inst", 0) + len(insts)
        for inst in insts:
            if inst.type == BsInstType.STR:
                if "__syncthreads" in cast(BsStr, inst).str:
                    result["sync"] = result.get("sync", 0) + 1
                elif "advance_memory[" in cast(BsStr, inst).str:
                    result["smem_store"] = result.get("smem_store", 0) + 1
                elif "goto" in cast(BsStr, inst).str:
                    result["goto"] = result.get("goto", 0) + 1
                elif cast(BsStr, inst).str.startswith("LABEL") and cast(BsStr, inst).str.endswith(":"):
                    result["exit_label"] = result.get("exit_label", 0) + 1
                else:
                    raise Exception(f"Unknown STR instruction: {cast(BsStr, inst).str}")
            elif inst.type == BsInstType.ADVANCE:
                if "Right" in inst.operation:
                    result["advance_right"] = result.get("advance_right", 0) + 1
                elif "Left" in inst.operation:
                    result["advance_left"] = result.get("advance_left", 0) + 1
                # sync, smem_store in adv
                if "FunctionSync" in inst.operation:
                    result["sync"] = result.get("sync", 0) + 2
                    result["smem_store"] = result.get("smem_store", 0) + 1
            else:
                result[inst_name_map[inst.type]] = (
                    result.get(inst_name_map[inst.type], 0) + 1
                )
                if inst.type == BsInstType.IF:
                    self.inst_stats(cast(BsIf, inst).body_1.body, result)
                    if cast(BsIf, inst).body_2 is not None:
                        self.inst_stats(cast(BsBlock, cast(BsIf, inst).body_2).body, result)
                elif inst.type == BsInstType.WHILE:
                    self.inst_stats(cast(BsWhile, inst).body.body, result)

    def run(self, insts: list[BsInst], var_name_map: dict[int | str | list[int], str]):
        insts_cpoy = insts.copy()
        result: dict[str, int] = {}
        self.inst_stats(insts_cpoy, result)
        if not hasattr(global_timer, "inst_result") or len(global_timer.inst_result) == 0:
            global_timer.inst_result = result
        else:
            for key, value in result.items():
                global_timer.inst_result[key] = (
                    global_timer.inst_result.get(key, 0) + value
                )
        return insts, var_name_map
