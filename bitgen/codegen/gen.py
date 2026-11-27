from io import TextIOWrapper
import os

from bitgen.inst import BsInst

from .. import config as cfg

class Generator:

    def __init__(self, insts_list: list[list[BsInst]], var_name_map_list: list[dict[int | str | list[int],str]], regex_list: list[str] | None = None) -> None:
        assert len(insts_list) == len(var_name_map_list)
        if (regex_list is not None) and (not cfg.GLOBAL_CONFIG["use_cached_code"]):
            assert len(insts_list) == len(regex_list)
        self.insts_list = insts_list
        self.var_name_map_list = var_name_map_list
        self.regex_list = regex_list
    
    def close(self) -> None:
        pass

    def get_kernel_path(self, kerne_file_name: str) -> str:
        __cached_module_path = cfg.GLOBAL_CONFIG["__cached_module_path"]
        assert __cached_module_path is not None
        kernel_file_path = os.path.join(
            os.getcwd(), __cached_module_path, "kernels/", kerne_file_name
        )
        os.makedirs(os.path.dirname(kernel_file_path), exist_ok=True)
        return kernel_file_path

    def gen_kernel_module_file(self, kernel_file_name_list: list[str]) -> None:
        __cached_module_path = cfg.GLOBAL_CONFIG["__cached_module_path"]
        assert __cached_module_path is not None
        module_file = os.path.join(
            os.getcwd(), __cached_module_path, "kernels/", "__init__.py"
        )
        with open(module_file, "w") as f:
            for kernel_file_name in kernel_file_name_list:
                kernel_file_name = kernel_file_name.split(".")[0]
                f.write(f"import kernels.{kernel_file_name} as {kernel_file_name}\n")

    def add_lines(self, file_handle: TextIOWrapper, lines: list[str] | str, indent: str= "") -> None:
        if isinstance(lines, list):
            lines = [indent + line + "\n" for line in lines]
            file_handle.write("".join(lines))
        else:
            lines = indent + lines
            file_handle.write(lines + "\n")


    def lower_insts(self, insts: list[BsInst], indent: str = "") -> None:
        pass
        # code_lines: list[str] = []
        # for inst in insts:
            # code_lines.append(inst.lower_to_bitstream(self.var_name_map_list, indent))
        # code_lines.append("")
        # self.file_handler.write("\n".join(code_lines))

    def lower(self, input_path: str = "") -> str:
        return ""
        # string_define = "def kernel_generated(input_stream: str):\n"
        # self.file_handler.write(string_define)
        # indent = "   "
        # self.lower_insts(self.insts, indent)
        # self.lower_insts(self.cc_insts, indent)

        # for idx, path in enumerate(self.paths_inst):
            # string_state_path = f"{indent}# path[{idx}]: {self.var_name_map_list[idx]}"
            # self.file_handler.write(string_state_path)
        #    path_insts = list(chain(*path))
        #    self.lower_insts(path_insts, indent)

        # string_return = f"{indent}return bs_result\n"
        # string_main = "result = kernel_generated(input_stream)"
        # self.file_handler.write(string_return)
        # self.file_handler.write(string_main)
