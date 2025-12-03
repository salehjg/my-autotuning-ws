#include <sycl/sycl.hpp>
#include <iostream>
#include <vector>
#include <cmath>

#ifndef TILE_SIZE
#define TILE_SIZE 16
#endif

// Round up to a multiple of TILE
static inline std::size_t round_up(std::size_t x, std::size_t tile) {
    return (x + tile - 1) / tile * tile;
}

// Simple CPU reference for verification
bool verify_reference(const float* A, const float* B, const float* C,
                      std::size_t N, float tol = 1e-4f) {
    for (std::size_t i = 0; i < N; ++i) {
        for (std::size_t j = 0; j < N; ++j) {
            float ref = 0.0f;
            for (std::size_t k = 0; k < N; ++k) {
                ref += A[i * N + k] * B[k * N + j];
            }
            if (std::fabs(C[i * N + j] - ref) > tol) {
                std::cerr << "Mismatch at (" << i << ", " << j
                          << "): C=" << C[i * N + j]
                          << " ref=" << ref << "\n";
                return false;
            }
        }
    }
    return true;
}

int main(int argc, char** argv) {
    std::size_t N = 256;     // Matrix size
    const std::size_t TILE = TILE_SIZE;   // Tile size from compile-time constant
    
    if (argc >= 2) N = std::stoul(argv[1]);
    
    std::cout << "N=" << N << " TILE=" << TILE << "\n";
    
    // Prefer GPU, fallback to default device
    sycl::device dev;
    try {
        dev = sycl::device{sycl::gpu_selector_v};
    } catch (const std::runtime_error&) {
        std::cerr << "No GPU found; falling back to default device.\n";
        dev = sycl::device{sycl::default_selector_v};
    }
    
    std::cout << "Running on: " << dev.get_info<sycl::info::device::name>() << "\n";
    
    sycl::queue q{dev};
    
    // Allocate USM shared memory
    float* A = sycl::malloc_shared<float>(N * N, q);
    float* B = sycl::malloc_shared<float>(N * N, q);
    float* C = sycl::malloc_shared<float>(N * N, q);
    
    if (!A || !B || !C) {
        std::cerr << "USM allocation failed.\n";
        return 1;
    }
    
    // Initialize matrices
    for (std::size_t i = 0; i < N; ++i) {
        for (std::size_t j = 0; j < N; ++j) {
            A[i * N + j] = static_cast<float>((i + j) % 7);
            B[i * N + j] = static_cast<float>((i - j) % 5);
        }
    }
    std::fill(C, C + N * N, 0.0f);
    
    const std::size_t G0 = round_up(N, TILE);
    const std::size_t G1 = round_up(N, TILE);
    const std::size_t phases = (N + TILE - 1) / TILE;
    
    // Submit kernel without specialization constant
    q.submit([&](sycl::handler& h) {
        sycl::local_accessor<float, 2> tileA({TILE, TILE}, h);
        sycl::local_accessor<float, 2> tileB({TILE, TILE}, h);
        
        h.parallel_for(
            sycl::nd_range<2>{{G0, G1}, {TILE, TILE}},
            [=](sycl::nd_item<2> it) {
                const std::size_t ly = it.get_local_id(0);
                const std::size_t lx = it.get_local_id(1);
                const std::size_t gy = it.get_group(0) * TILE + ly;
                const std::size_t gx = it.get_group(1) * TILE + lx;
                
                float acc = 0.0f;
                
                for (std::size_t p = 0; p < phases; ++p) {
                    const std::size_t a_col = p * TILE + lx;
                    const std::size_t b_row = p * TILE + ly;
                    
                    tileA[ly][lx] = (gy < N && a_col < N) ? A[gy * N + a_col] : 0.0f;
                    tileB[ly][lx] = (b_row < N && gx < N) ? B[b_row * N + gx] : 0.0f;
                    
                    it.barrier(sycl::access::fence_space::local_space);
                    
                    for (std::size_t k = 0; k < TILE; ++k) {
                        acc += tileA[ly][k] * tileB[k][lx];
                    }
                    
                    it.barrier(sycl::access::fence_space::local_space);
                }
                
                if (gy < N && gx < N) {
                    C[gy * N + gx] = acc;
                }
            });
    }).wait();
    
    //bool ok = verify_reference(A, B, C, N);
    //std::cout << (ok ? "Verification PASSED ✅" : "Verification FAILED ❌") << "\n";
    
    sycl::free(A, q);
    sycl::free(B, q);
    sycl::free(C, q);
    
    //return ok ? 0 : 2;
    return 0;
}