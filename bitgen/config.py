GLOBAL_CONFIG = {
    "warmup_iters": 0,
    "exec_iters": 0,
    "dry_run": False,

    # Regex config
    "regex_num": 0,
    "regex_group_number": 0,
    "regex_group_serial": 0, 
    "balance_regex_groups": 0,

    # Input config
    "input_size": 0,
    "repeat_input": 0,
    "multi_input": 0,
    "split_input": 0,

    #  Compilation config
    "pass_cc_advanced": 0,
    "pass_cc_advanced_max": 0,
    "pass_cc_advanced_merge_cc": 0,
    "pass_short_circuit": 0,
    "pass_short_circuit_start": 0,
    "pass_short_circuit_interval": 0,
    "pass_short_circuit_interval_disable": 0,
    "pass_short_circuit_syncpoint": 0,
    "pass_graph_break": 0,
    "pass_print_graph": 0,
    "pass_inst_stats": 0,
    "pass_inst_stats_dyn": 0,
    "parallel_compile_parabix": 0,
    "parallel_compile_cuda": 0,
    "parallel_compile_cuda_lto": 0,
    "backend": "cuda",

    # Backend config: CUDA
    "block_size": 0,
    "cuda_register_num": 0,

    # Backend config: Torch
    "torch_compile": 0,
    "debug_torch": 0,

    # Debug config
    "profile": True,
    "print_bitstream": True,
    "print_bit_start": 0,
    "print_zeros": True,
    "validation": 0,
    "use_cached_code": False,
    "cached_code_dir": ".cache_bitgen",
    "__cached_module_path": "kernels/pablo",
    "__cached_path": "",
    "cache_dir": ".cache_bitgen"
}
