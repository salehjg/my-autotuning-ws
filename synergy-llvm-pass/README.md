# How to (saleh)

## Build LLVM15 from source (Archlinux)
```bash
bash fetch_build_llvm15_archlinux.sh
```

## Build The LLVM Pass
```bash
export CC=gcc-12
export CXX=g++-12
export AR=ar-12
export RANLIB=ranlib-12
export LD=ld-12
export CMAKE_PREFIX_PATH=/tmp/llvm15_installdir

cd my-autotuning-ws/synergy-llvm-pass/training-dataset/passes
rm -rf build
mkdir build
cd build
cmake ..
make -j
echo "The built libfeature_pass.so should be under my-autotuning-ws/synergy-llvm-pass/training-dataset/passes/build/feature-pass"
```
