from typing import cast

from bitgen.inst import BsInstType, BsInst, BsAssign



class remove_alias_pass:
    def __init__(self,):
        self.pass_name = "remove_alias"
        self.define_pos: dict[int | list[int], int] = {} # var_id -> inst_id
        self.alias: dict[int | list[int], int] = {} # alias -> defined_var_id

    def run(self, insts: list[BsInst], var_name_map: dict[int | str | list[int], str]) -> tuple[list[BsInst], dict[int | str | list[int], str]]:
        new_insts: list[BsInst | None] = insts.copy() # pyright: ignore[reportAssignmentType]
        for inst_id, inst in enumerate(insts):
            # Update define postion
            if inst.type == BsInstType.WHILE:
                continue
            self.define_pos[inst.ret] = inst_id
            if inst.type == BsInstType.ASSIGN:
                ret_name = var_name_map[inst.ret]
                if ret_name == "output.matches" or ret_name.startswith(  # result
                    "basis"
                ):  # basic stream
                    continue
                # while
                if ret_name.startswith("test") or ret_name.startswith("accum"):
                    operand = cast(BsAssign, inst).operand1
                    if operand in self.alias:
                        new_insts[inst_id].operand1 = self.alias[operand] # type: ignore
                        new_insts[inst_id].operands = (self.alias[operand],) # type: ignore
                    continue
                if inst.operand1 in self.alias and self.alias != None: # type: ignore
                    self.alias[inst.ret] = self.alias[inst.operand1] # type: ignore
                else:
                    self.alias[inst.ret] = inst.operand1 # type: ignore
                new_insts[inst_id] = None
            else:
                # Redefine the alas var
                if inst.ret in self.alias:
                    self.alias.pop(inst.ret)
                # Replace the operand with defined var
                for operand_id in range(inst.n_operand):
                    operand = inst.operands[operand_id]
                    if operand in self.alias:
                        if inst.n_operand == 1:
                            new_insts[inst_id].operands = (self.alias[operand],) # pyright: ignore[reportOptionalMemberAccess, reportArgumentType]
                        else:
                            new_insts[inst_id].operands = (new_insts[inst_id].operands[0],self.alias[operand]) # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess, reportArgumentType]

                        # TODO(tge): Fix operand1 usage
                        if operand_id == 0:
                            new_insts[inst_id].operand1 = self.alias[operand] # pyright: ignore
                        elif operand_id == 1:
                            new_insts[inst_id].operand2 = self.alias[operand] # pyright: ignore
        new_insts_ = [inst for inst in new_insts if inst != None]

        return new_insts_, var_name_map
