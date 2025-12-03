rm matmul.sc
icpx -V -std=c++17 -fsycl -fsycl-targets=spir64_gen -Xsycl-target-backend "-device pvc" matmul.sc.cpp -o matmul.sc
./matmul.sc