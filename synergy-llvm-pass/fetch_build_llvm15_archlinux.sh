echo "make sure you have gcc-12 and g++-12 (install them from AUR"
export CC=gcc-12
export CXX=g++-12
export AR=ar-12
export RANLIB=ranlib-12
export LD=ld-12
sudo pacman -S --needed cmake ninja python git gcc binutils zlib libxml2 libedit
rm llvmorg-15.0.1.zip
rm -rf llvm-project-llvmorg-15.0.1
wget https://github.com/llvm/llvm-project/archive/refs/tags/llvmorg-15.0.1.zip
unzip llvmorg-15.0.1.zip
cd llvm-project-llvmorg-15.0.1
mkdir build
cd build

rm -rf /tmp/llvm15_installdir
mkdir /tmp/llvm15_installdir

# disable sanitizers
cmake -G Ninja ../llvm \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_ENABLE_PROJECTS="clang;clang-tools-extra;lld" \
  -DLLVM_TARGETS_TO_BUILD="X86" \
  -DLLVM_ENABLE_TERMINFO=OFF \
  -DCMAKE_INSTALL_PREFIX=/tmp/llvm15_installdir \
  -DLLVM_ENABLE_RUNTIMES=""

ninja -j$(nproc)  
ninja install
echo "The built binaries are under llvm-project-llvmorg-15.0.1/build/bin"
echo "Installed it under /tmp/llvm15_installdir"

#export CMAKE_PREFIX_PATH=/tmp/llvm15_installdir
