from typing import cast

from bitgen.inst.inst import BsInst
from bitgen.inst.inst_block_while import BsWhile

from ..inst import BsInstType, BsAssign, BsAdvance, BsStr
from ..passes.pass_utils import update_insts
from .. import config as cfg


class cc_advance_pass:
    def __init__(self):
        self.pass_name = "cc_advance"
        self.advance_count: dict[int | list[int], int] = {}  # var_id -> advance_count
        self.advance_count_dyn: dict[int | list[int], int] = {}

    # Each variable has an advance count.
    # The operation on two variables should have the same advance count.
    # Otherwise, we need to align the two variables.
    def get_advance_count(self, var_id: int | list[int]) -> int:
        if var_id not in self.advance_count:
            self.advance_count[var_id] = 0
        return self.advance_count[var_id]

    def add_new_var(self, var_name_map: dict[int | str | list[int],str], var_name: str):
        new_var_id = len(var_name_map)
        var_name_map[new_var_id] = var_name
        return new_var_id

    def get_max_adv_in_while(self, insts: list[BsInst]):
        max_adv = 0
        for _, inst in enumerate(insts):
            if inst.type == BsInstType.ADVANCE:
                max_adv += 1
                assert cast(BsAdvance, inst).operand2 == 1
        return max_adv

    def insert_cc_shared_memory_store(
        self, adv_var_stored: list[int | str | list[int]], inst_id: int, insert_insts: dict[BsInst, int], var_name_map: dict[int | str | list[int],str], first_adv_pos: int
    ):
        # Insert memory store for previous `cc_advance_max_num` advance inst at first_adv_pos.
        cc_advance_max_num = cfg.GLOBAL_CONFIG["pass_cc_advanced_max"]
        block_size = cfg.GLOBAL_CONFIG["block_size"][0]
        if cc_advance_max_num < len(adv_var_stored):
            raise Exception(
                f"cc_advance_max_num {cc_advance_max_num} < len(adv_var_stored) {len(adv_var_stored)}"
            )
        new_sync_inst_str = BsStr(("__syncthreads();",))
        if first_adv_pos == -1:
            first_adv_pos = inst_id
        assert first_adv_pos >= 0
        insert_insts[new_sync_inst_str] = first_adv_pos
        for adv_var_id, adv_var in enumerate(adv_var_stored):
            align_operand_name = var_name_map[adv_var]
            new_inst_str = BsStr(
                (
                    f"advance_memory[{adv_var_id + 1} * {block_size} + threadIdx.x] = {align_operand_name};",
                )
            )
            insert_insts[new_inst_str] = first_adv_pos
        new_sync_inst_str = BsStr(("__syncthreads();",))
        insert_insts[new_sync_inst_str] = first_adv_pos

    def advance(self, insts: list[BsInst], var_name_map: dict[int | str | list[int],str]):
        new_insts = insts.copy()
        insert_insts: dict[BsInst, int] = {}  # inst -> pos_id
        first_adv_pos = -1
        accum_adv_num = 0
        adv_var_stored:  list[int | str | list[int]] = []
        adv_inst_stored: list[tuple[BsInst, int]] = []

        for inst_id, inst in enumerate(insts):
            ret_id = inst.ret
            cc_advance_max_num = cfg.GLOBAL_CONFIG["pass_cc_advanced_max"]
            block_size = cfg.GLOBAL_CONFIG["block_size"][0]

            # Disable cc_advance for while loop body.
            # reset advance_count to 0.
            if inst.type == BsInstType.WHILE:
                condition_offset = self.get_advance_count(cast(BsWhile, inst).condition)
                assert isinstance(cast(BsWhile, inst).ret, int)
                ret_offset = self.get_advance_count(cast(int, cast(BsWhile, inst).ret))
                assert ret_offset == condition_offset
                var_cc_adv: list[tuple[int, int, int]] = []  # (cc_var, adv_count)
                for _, inst_in_while in enumerate(cast(BsWhile, inst).body.body):
                    ret_id = inst_in_while.ret
                    if inst_in_while.type == BsInstType.WHILE:
                        break
                    if inst_in_while.n_operand == 2:
                        if inst_in_while.type == BsInstType.ADVANCE:
                            advance_count = self.get_advance_count(
                                cast(BsAdvance, inst_in_while).operand1
                            )
                            self.advance_count[cast(BsAdvance, inst_in_while).ret] = advance_count + int(
                                cast(BsAdvance, inst_in_while).operand2
                            )
                            # print(f"adv cc: {var_name_map[inst_in_while.operand1]}, offset={self.get_advance_count(inst_in_while.operand1)}, ret={var_name_map[ret_id]}, offset={self.get_advance_count(ret_id)}")
                        elif inst_in_while.type == BsInstType.AND:
                            advance_count_operand1 = self.get_advance_count(
                                cast(BsAdvance, inst_in_while).operand1
                            )
                            advance_count_operand2 = self.get_advance_count(
                                cast(BsAdvance, inst_in_while).operand2
                            )
                            align_to_operand: int = 0
                            align_operand: int = -1
                            if advance_count_operand1 > advance_count_operand2:
                                align_operand = cast(BsAdvance, inst_in_while).operand2
                                align_to_operand: int = cast(BsAdvance, inst_in_while).operand1
                            elif advance_count_operand1 < advance_count_operand2:
                                align_operand = cast(BsAdvance, inst_in_while).operand1
                                align_to_operand: int = cast(BsAdvance, inst_in_while).operand2
                            
                            if var_name_map[align_operand].startswith("CC__"): # pyright: ignore[reportPossiblyUnboundVariable]
                                adv_count = self.get_advance_count(align_to_operand)
                                assert isinstance(ret_id, int)
                                self.advance_count[ret_id] = adv_count
                                cc_adv_name = (
                                    var_name_map[align_operand] # pyright: ignore[reportPossiblyUnboundVariable]
                                    + "_advance"
                                    + str(adv_count)
                                )

                                try_num = 0
                                while cc_adv_name in var_name_map.values():
                                    try_num += 1
                                    cc_adv_name = cc_adv_name + "_" + str(try_num)
                                cc_adv_id = self.add_new_var(var_name_map, cc_adv_name)
                                var_cc_adv.append((align_operand, cc_adv_id, adv_count)) # pyright: ignore[reportUnknownArgumentType, reportPossiblyUnboundVariable]

                                if cast(BsAdvance, inst_in_while).operand1 == align_operand: # pyright: ignore[reportPossiblyUnboundVariable]
                                    cast(BsAdvance, inst_in_while).operand1 = cc_adv_id
                                else:
                                    cast(BsAdvance, inst_in_while).operand2 = cc_adv_id
                                # print(var_name_map[align_operand])
                            # print(f"op1={var_name_map[inst_in_while.operand1]}, offset={advance_count_operand1}.   op2={var_name_map[inst_in_while.operand2]}, offset={advance_count_operand2}.  ret={var_name_map[ret_id]}, offset={self.get_advance_count(ret_id)}")

                    else:
                        # Same advance count for the output variable.
                        pass
                        # self.advance_count[ret_id] = self.get_advance_count(inst_in_while.operand1)
                        # print(f"op1={var_name_map[inst_in_while.operand1]}.   ret={var_name_map[ret_id]}, offset={self.get_advance_count(ret_id)}")

                if accum_adv_num + len(var_cc_adv) >= cc_advance_max_num:
                    self.insert_cc_shared_memory_store(
                        adv_var_stored,
                        inst_id,
                        insert_insts,
                        var_name_map,
                        first_adv_pos,
                    )
                    # Reset the counter
                    if len(adv_inst_stored) > 0:
                        for adv_inst, adv_inst_id in adv_inst_stored:
                            insert_insts[adv_inst] = adv_inst_id
                        adv_inst_stored = []
                    first_adv_pos = inst_id
                    accum_adv_num = 0
                    adv_var_stored = []

                # assert len(var_cc_adv) < cc_advance_max_num
                if len(var_cc_adv) >= cc_advance_max_num:
                    for cc_var, cc_adv_id, adv_count in var_cc_adv:
                        adv_inst = BsAdvance((cc_var, adv_count), cc_adv_id)
                        adv_inst.operation = "BSAdvanceLeftFunctionSync"
                        adv_inst.shared_adv_mem_offset = f"0"
                        insert_insts[adv_inst] = inst_id
                    var_cc_adv = []

                for cc_var, cc_adv_id, adv_count in var_cc_adv:
                    if (
                        cfg.GLOBAL_CONFIG["pass_cc_advanced_merge_cc"]
                        and cc_var in adv_var_stored
                    ):
                        shared_adv_mem_id = adv_var_stored.index(cc_var) + 1
                    else:
                        adv_var_stored.append(cc_var)
                        accum_adv_num += 1
                        shared_adv_mem_id = accum_adv_num
                    adv_inst = BsAdvance((cc_var, adv_count), cc_adv_id)
                    adv_inst.operation = "BSAdvanceLeftFunction"
                    adv_inst.shared_adv_mem_offset = f"{shared_adv_mem_id} * {block_size}"
                    adv_inst_stored.append((adv_inst, inst_id))
                    # insert_insts[adv_inst] = inst_id
                continue

            if inst.n_operand == 2:
                if inst.type == BsInstType.ADVANCE:
                    if first_adv_pos == -1:
                        first_adv_pos = inst_id
                    # This inst wiill be removed by remove_alias_pass.
                    new_assign_inst = BsAssign((cast(BsAdvance, inst).operand1,), inst.ret)
                    new_insts[inst_id] = new_assign_inst
                    advance_count = self.get_advance_count(cast(BsAdvance, inst).operand1)
                    self.advance_count[ret_id] = advance_count + int(cast(BsAdvance, inst).operand2)
                    self.advance_count_dyn[ret_id] = self.advance_count_dyn.get(
                        cast(BsAdvance, inst).operand1
                    ) or -1
                else:
                    is_result_or = False
                    advance_count_operand1 = self.get_advance_count(inst.operand1) # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownArgumentType, reportIndexIssue]
                    advance_count_operand2 = self.get_advance_count(inst.operand2) # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType, reportAttributeAccessIssue]
                    advance_count_operand1_dyn = self.advance_count_dyn.get(
                        inst.operand1 # type: ignore
                    )
                    # advance_count_operand2_dyn = self.advance_count_dyn.get(
                    #    inst.operand2 # type: ignore
                    # )

                    # The two operands should have the same advance count
                    align_operand: int = -1
                    if advance_count_operand1 > advance_count_operand2:
                        align_operand: int = inst.operand2 # type: ignore
                        align_to_operand = inst.operand1 # type: ignore
                    elif advance_count_operand1 < advance_count_operand2:
                        align_operand: int = inst.operand1 # type: ignore
                        align_to_operand = inst.operand2 # type: ignore
                    else:
                        new_insts[inst_id].comment = (
                            f"{var_name_map[ret_id]}:{self.get_advance_count(ret_id)}"
                        )
                        self.advance_count[ret_id] = advance_count_operand1
                        self.advance_count_dyn[ret_id] = self.advance_count_dyn.get(
                            inst.operand1 # type: ignore
                        ) or -1
                        continue

                    # align_operand wait to be stored in memory in group of `cc_advance_max_num`
                    # Only cc_stream can be preloaded in group.
                    pre_load = False
                    # print(f"align {var_name_map[align_operand]} to {var_name_map[align_to_operand]}., {advance_count_operand1}, {advance_count_operand2}, accum_adv_num = {accum_adv_num}")
                    if var_name_map[align_operand].startswith("CC__"):
                        pre_load = True  

                    # Replace right shift inst to left shift inst.
                    offset = abs(advance_count_operand1 - advance_count_operand2)
                    new_ret_name = (
                        var_name_map[align_operand] + "_advance" + str(offset)
                    )
                    try_num = 0
                    while new_ret_name in var_name_map.values():
                        try_num += 1
                        new_ret_name = new_ret_name + "_" + str(try_num)
                    new_ret_id = self.add_new_var(var_name_map, new_ret_name)
                    new_inst_adv = BsAdvance((align_operand, offset), new_ret_id) # pyright: ignore[reportUnknownArgumentType]
                    # new_inst_adv.dymatic_offset = True
                    if pre_load:
                        if (
                            cfg.GLOBAL_CONFIG["pass_cc_advanced_merge_cc"]
                            and align_operand in adv_var_stored
                        ):
                            shared_adv_mem_id = adv_var_stored.index(align_operand) + 1 # pyright: ignore[reportUnknownArgumentType]
                        else:
                            adv_var_stored.append(align_operand) # pyright: ignore[reportUnknownArgumentType]
                            accum_adv_num += 1
                            shared_adv_mem_id = accum_adv_num
                        new_inst_adv.shared_adv_mem_offset = (
                            f"{shared_adv_mem_id} * {block_size}"
                        )
                        if inst.type == BsInstType.OR:
                            # new_inst_adv.operation = "BSRollLeftFunction"
                            new_inst_adv.operation = "BSAdvanceLeftFunction"
                            # raise NotImplementedError()
                        else:
                            new_inst_adv.operation = "BSAdvanceLeftFunction"
                            # new_inst_adv.operation = "BSAdvanceLeftFunctionSync"
                    else:
                        new_inst_adv.shared_adv_mem_offset = f"0"
                        if inst.type == BsInstType.OR:
                            # Result OR.
                            # Because we can only do block roll left shift here,
                            # We do block adv right shift to align the variable
                            # with longer advance count to the variable with shorter advance count.
                            # So we won't lost bit.
                            advance_count_operand1, advance_count_operand2 = (
                                advance_count_operand2,
                                advance_count_operand1,
                            )
                            new_ret_name = (
                                var_name_map[align_to_operand]
                                + "_advance"
                                + str(offset)
                            )
                            try_num = 0
                            while new_ret_name in var_name_map.values():
                                try_num += 1
                                new_ret_name = new_ret_name + "_" + str(try_num)
                            new_ret_id = self.add_new_var(var_name_map, new_ret_name)
                            new_inst_adv = BsAdvance(
                                (cast(int, align_to_operand), offset), new_ret_id
                            )
                            new_inst_adv.operation = "BSAdvanceRightFunctionSync"
                            is_result_or = True
                            # new_inst_adv.operation = "BSAdvanceLeftFunctionSync"
                        else:
                            new_inst_adv.operation = "BSAdvanceLeftFunctionSync"
                    # if inst.type == BsInstType.AND:
                    #     new_inst_adv.operation = "BSAdvanceLeftFunction"
                    # elif inst.type == BsInstType.OR:
                    #     new_inst_adv.operation = "BSRollLeftFunction"
                    # elif inst.type == BsInstType.MATCHSTAR:
                    #     new_inst_adv.operation = "BSAdvanceLeftFunction"
                    # elif inst.type == BsInstType.SCANTHRU:
                    #     new_inst_adv.operation = "BSAdvanceLeftFunction"
                    # elif inst.type == BsInstType.XOR:
                    #     new_inst_adv.operation = "BSRollLeftFunction"
                    # else:
                    #     raise Exception(f"Unsupported operation: {inst.type}")

                    # Store the variable to be aligned in memory
                    if (
                        var_name_map[align_operand].startswith("CC__")
                        and accum_adv_num >= cc_advance_max_num
                    ):
                        self.insert_cc_shared_memory_store(
                            adv_var_stored,
                            inst_id,
                            insert_insts,
                            var_name_map,
                            first_adv_pos,
                        )
                        # Reset the counter
                        if len(adv_inst_stored) > 0:
                            for adv_inst, adv_inst_id in adv_inst_stored:
                                insert_insts[adv_inst] = adv_inst_id
                            adv_inst_stored = []
                        first_adv_pos = inst_id
                        accum_adv_num = 0
                        adv_var_stored = []

                    insert_insts[new_inst_adv] = inst_id
                    # Update the operand of the original inst.
                    if advance_count_operand1 > advance_count_operand2:
                        new_insts[inst_id].operand2 = new_ret_id # pyright: ignore[reportAttributeAccessIssue]
                        new_insts[inst_id].operands = (new_insts[inst_id].operands[0], new_ret_id) # pyright: ignore[reportAttributeAccessIssue]
                    elif advance_count_operand1 < advance_count_operand2:
                        new_insts[inst_id].operand1 = new_ret_id # pyright: ignore[reportAttributeAccessIssue]
                        new_insts[inst_id].operands = (new_ret_id, new_insts[inst_id].operands[1]) # pyright: ignore[reportGeneralTypeIssues, reportAttributeAccessIssue]
                    if is_result_or:
                        self.advance_count[ret_id] = min(
                            advance_count_operand1, advance_count_operand2
                        )
                    else:
                        self.advance_count[ret_id] = max(
                            advance_count_operand1, advance_count_operand2
                        )
                    self.advance_count_dyn[ret_id] = advance_count_operand1_dyn or -1

            else:
                # Same advance count for the output variable.
                self.advance_count[ret_id] = self.get_advance_count(inst.operand1) # type: ignore
                self.advance_count_dyn[ret_id] = self.advance_count_dyn.get(
                    inst.operand1 # type: ignore
                ) or -1

            new_insts[inst_id].comment = (
                f"{var_name_map[ret_id]}:{self.advance_count[ret_id]}, {self.advance_count_dyn.get(ret_id)}"
            )
            # advance_cound = self.get_advance_count(ret_id)
            # comment += f" -> {advance_cound}"

        # Last group
        if accum_adv_num != 0:
            # Insert memory store for previous `cc_advance_max_num` advance inst at  first_adv_pos.
            new_sync_inst_str = BsStr(("__syncthreads();",))
            insert_insts[new_sync_inst_str] = first_adv_pos
            if first_adv_pos == -1:
                raise Exception("first_adv_pos should not be -1.")
            for adv_var_id, adv_var in enumerate(adv_var_stored):
                align_operand_name = var_name_map[adv_var]
                new_inst_str = BsStr(
                    (
                        f"advance_memory[{adv_var_id + 1} * {block_size} + threadIdx.x] = {align_operand_name};" # pyright: ignore[reportPossiblyUnboundVariable]
                    ,)
                )
                insert_insts[new_inst_str] = first_adv_pos
            new_sync_inst_str = BsStr(("__syncthreads();",))
            insert_insts[new_sync_inst_str] = first_adv_pos
            # Reset the counter
            if len(adv_inst_stored) > 0:
                for adv_inst, adv_inst_id in adv_inst_stored:
                    insert_insts[adv_inst] = adv_inst_id
                adv_inst_stored = []
            first_adv_pos = -1
            accum_adv_num = 0
            adv_var_stored = []
        update_insts(new_insts, insert_insts)
        return new_insts, var_name_map

    def break_insts(self, insts: list[BsInst]) -> list[list[BsInst]]:
        insts_break_group: list[list[BsInst]] = []
        insts_break: list[BsInst] = []
        for _, inst in enumerate(insts):
            insts_break.append(inst)
            if inst.type in [BsInstType.GRAPHBREAK]:
                if len(insts_break) > 0:
                    insts_break_group.append(insts_break)
                    insts_break = []
        if len(insts_break) > 0:
            insts_break_group.append(insts_break)
        return insts_break_group

    def run(self, insts: list[BsInst], var_name_map: dict[int | str | list[int],str]) -> tuple[list[BsInst], dict[int | str | list[int], str]]:
        new_insts: list[BsInst] = []
        insts_subgraphs = self.break_insts(insts)
        if len(insts_subgraphs) != 1:
            raise NotImplementedError(
                f"Multiple subgraphs ({len(insts_subgraphs)}) for cc advance are not supported yet."
            )
        for insts_subgraph in insts_subgraphs:
            new_insts_subgraph, var_name_map = self.advance(
                insts_subgraph, var_name_map
            )
            new_insts += new_insts_subgraph
        return new_insts, var_name_map
