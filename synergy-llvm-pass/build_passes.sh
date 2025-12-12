export CMAKE_PREFIX_PATH=$(pwd)/llvm15_installdir
cd training-dataset/passes
rm -rf build
mkdir build
cd build
export CC=gcc-12
export CXX=g++-12
cmake ..
make -j

