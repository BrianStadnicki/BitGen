from bitgen.inst.inst import BsInst
from bitgen.passes.cc_advance import cc_advance_pass
from bitgen.passes.free_intermediate_tensor import free_intermediate_tensor_pass
from bitgen.passes.graph_break import graph_break_pass
from bitgen.passes.inst_stats import inst_stats_pass
from bitgen.passes.print_computation_graph import print_computation_graph_pass
from bitgen.passes.remove_alias import remove_alias_pass
from bitgen.passes.short_circuit import short_circuit_pass

from ..log import MyLogger

class PassManager:
    def __init__(
        self,
    ):
        self.passes: list[cc_advance_pass | free_intermediate_tensor_pass | graph_break_pass | inst_stats_pass | print_computation_graph_pass | remove_alias_pass | short_circuit_pass] = []

    def add_pass(self, pass_: cc_advance_pass | free_intermediate_tensor_pass | graph_break_pass | inst_stats_pass | print_computation_graph_pass | remove_alias_pass | short_circuit_pass, enabled: bool = True):
        if enabled:
            self.passes.append(pass_)

    def print_passes(self):
        for pass_ in self.passes:
            print(pass_.pass_name)

    def run(self, insts: list[BsInst], var_name_map: dict[int | str | list[int], str]) -> tuple[list[BsInst], dict[int | str | list[int], str]]:
        for pass_ in self.passes:
            MyLogger.debug(f"[Pass] Running pass {pass_.pass_name}")
            insts, var_name_map = pass_.run(insts, var_name_map) # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType, reportUnknownMemberType]
        return insts, var_name_map # pyright: ignore[reportUnknownVariableType]
