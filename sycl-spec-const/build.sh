rm matmul
icpx -V -std=c++17 -fsycl -fsycl-targets=spir64_gen -Xsycl-target-backend "-device pvc" matmul.cpp -o matmul
./matmul