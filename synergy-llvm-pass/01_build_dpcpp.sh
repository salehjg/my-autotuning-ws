source dpcpp_helper.sh
conda activate py310_cuda11
mkdir -p dpcpp_build
# install cuda from the nivida channel.
build_dpcpp_cuda "dpcpp_build" "installdir" "$CONDA_PREFIX" "gcc-12" "g++-12"
