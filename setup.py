from pathlib import Path

from setuptools import find_packages, setup
from torch.utils.cpp_extension import BuildExtension, CUDAExtension
from cuda.core import Device

root = Path(__file__).parent.resolve()



def get_sources():
    cpp_files = list(root.glob("bitgen/template/cuda/*.cpp"))
    cuda_files = list(root.glob("bitgen/template/cuda/*.cu"))
    sources = cpp_files + cuda_files
    # Optional: Remove the print statement or replace it with logging if needed
    print("Source files:", sources)
    return [str(file) for file in sources]


def get_cuda_arch_flags():
    dev = Device()
    # Initialize CUDA Driver API
    dev.set_current()

    arch_flag = f"-arch=sm_{dev.compute_capability.major}{dev.compute_capability.minor}"
    return [arch_flag]


setup(
    name="bitgen",
    version="0.1",
    packages=find_packages(),
    package_data={
        "bitgen": ["backend/cuda/template/*.cu", "datasets_small/*"],
    },
    # include_package_data=True,
    ext_modules=[
        CUDAExtension(
            name="bitgen.cuda",
             sources=[
                "bitgen/template/cuda/pybind.cpp",
                "bitgen/template/cuda/kernel.cu",
            ],
            include_dirs=["bitgen/template/cuda"],
            extra_compile_args={
                "cxx": ["-O3", "-std=c++17"],
                "nvcc": ["-O3", "-std=c++17"] + get_cuda_arch_flags(),
            },
        )
    ],
    cmdclass={"build_ext": BuildExtension},
)
