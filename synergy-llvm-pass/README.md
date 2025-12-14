# How to (saleh)

## 0. System-wide Setup
```bash
sudo pacman -S nvidia cuda
yay -S gcc-12
```

## 1. Setup Conda For CUDA
```bash
conda create -n py310_cuda118_rt python=3.10 -y
conda activate py310_cuda118_rt
conda install -c nvidia -c conda-forge cuda-runtime=11.8 cudnn=8 -y
conda install ninja cmake
```

## 2. Build LLVM15 (no SYCL support)
```bash
bash 00_build_llvm15_clang15.sh
# source llvm15_installdir/set_envs.sh
```

## 3. Build DPCPP With NVIDIA Support
```bash
bash 01_build_dpcpp.sh
# source dpcpp_build/installdir/set_envs.sh
```

## 4. Build LLVM Passes
```bash
# source llvm15_installdir/set_envs.sh
source dpcpp_build/installdir/set_envs.sh
bash 02_build_passes.sh
```

## 5. Run LLVM Passes
Do NOT close the previous terminal session (to keep the env variables).
```bash
cd training-dataset
bash extract_features.sh
```
