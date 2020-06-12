#!/usr/bin/env python3
import os
import torch

from setuptools import setup, find_packages
from torch.utils.cpp_extension import BuildExtension, CUDAExtension

cxx_args = ["-std=c++11"]

nvcc_args = [
    "-gencode",
    "arch=compute_62,code=sm_62"
]

setup(
    name="interpolation_cuda",
    ext_modules=[
        CUDAExtension(
            "interpolation_cuda",
            ["interpolation_cuda.cc", "interpolation_cuda_kernel.cu"],
            extra_compile_args={"cxx": cxx_args, "nvcc": nvcc_args},
        )
    ],
    cmdclass={"build_ext": BuildExtension},
)
