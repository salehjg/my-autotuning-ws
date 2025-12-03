#!/usr/bin/env python3

"""
Benchmark script to compare SYCL specialization constants vs #define
Usage: python3 benchmark_comparison.py
"""

import subprocess
import time
import csv
import statistics
import os
from datetime import datetime
from pathlib import Path

# Configuration
MATRIX_SIZE = 1024
TILE_SIZES = [2, 4, 8, 10]  # 10 tile sizes with repetition
REPETITIONS = 10

# Compiler settings
COMPILER = "icpx"
COMPILER_FLAGS = [
    "-std=c++17",
    "-fsycl",
#    "-fsycl-targets=intel_gpu_mtl"  # Meteor Lake target
    "-fsycl-targets=spir64_gen",   # Intel Max 1100
    "-Xsycl-target-backend",
    "-device pvc"
]

# Source files
SPEC_CONST_SRC = "matmul.sc.cpp"
DEFINE_SRC = "matmul.cpp"

# Results directory
RESULTS_DIR = Path("benchmark_results")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def run_command(cmd, capture_output=True):
    """Run a command and return the result."""
    result = subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        check=False
    )
    return result


def measure_compile_time(source_file, output_file, extra_flags=None):
    """Compile a source file and measure compilation time."""
    cmd = [COMPILER] + COMPILER_FLAGS
    if extra_flags:
        cmd.extend(extra_flags)
    cmd.extend(["-o", output_file, source_file])
    
    print(f"    Compiling: {' '.join(cmd)}")
    start = time.time()
    result = run_command(cmd)
    elapsed = time.time() - start
    
    if result.returncode != 0:
        print(f"    ERROR: Compilation failed!")
        print(result.stderr)
        return None
    
    return elapsed


def measure_runtime(executable, args=None):
    """Run an executable and measure execution time."""
    cmd = [f"./{executable}"]
    if args:
        cmd.extend(map(str, args))
    
    start = time.time()
    result = run_command(cmd, capture_output=True)
    elapsed = (time.time() - start) * 1000  # Convert to milliseconds
    
    if result.returncode != 0:
        print(f"    ERROR: Execution failed!")
        print(result.stderr)
        return None
    
    return elapsed


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def main():
    """Main benchmark function."""
    # Create results directory
    RESULTS_DIR.mkdir(exist_ok=True)
    
    # CSV output files
    compile_csv = RESULTS_DIR / f"compile_times_{TIMESTAMP}.csv"
    runtime_csv = RESULTS_DIR / f"runtime_{TIMESTAMP}.csv"
    summary_csv = RESULTS_DIR / f"summary_{TIMESTAMP}.csv"
    
    # Data storage
    compile_data = {"SpecConst": [], "Define": []}
    runtime_data = {"SpecConst": {}, "Define": {}}
    
    print_header("SYCL Specialization Constant vs #define Benchmark")
    print(f"Matrix Size: {MATRIX_SIZE}")
    print(f"Tile Sizes: {TILE_SIZES}")
    print(f"Repetitions per tile: {REPETITIONS}")
    print(f"Compiler: {COMPILER}")
    print(f"Flags: {' '.join(COMPILER_FLAGS)}")
    print(f"Results directory: {RESULTS_DIR}")
    
    # Initialize CSV files
    with open(compile_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Method", "TileSize", "Repetition", "CompileTime(s)"])
    
    with open(runtime_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Method", "TileSize", "Run", "ExecutionTime(ms)"])
    
    # ========================================
    # 1. Benchmark Specialization Constant
    # ========================================
    print_header("1. Benchmarking Specialization Constant")
    
    print("Compiling specialization constant version...")
    spec_const_compile_time = measure_compile_time(
        SPEC_CONST_SRC,
        "matmul_spec_const"
    )
    
    if spec_const_compile_time is None:
        print("ERROR: Failed to compile specialization constant version. Exiting.")
        return 1
    
    print(f"  Compilation time: {spec_const_compile_time:.3f}s")
    compile_data["SpecConst"].append(spec_const_compile_time)
    
    print("\nRunning specialization constant version...")
    for idx, tile in enumerate(TILE_SIZES):
        print(f"  Tile size {tile} (iteration {idx+1}/{len(TILE_SIZES)}): ", end="", flush=True)
        
        # Record compile time (same for all tiles)
        with open(compile_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["SpecConst", tile, idx, spec_const_compile_time])
        
        # Run multiple times
        tile_runtimes = []
        for rep in range(1, REPETITIONS + 1):
            runtime = measure_runtime("matmul_spec_const", [MATRIX_SIZE, tile])
            if runtime is None:
                print(f"\n    ERROR: Run {rep} failed")
                continue
            tile_runtimes.append(runtime)
            
            with open(runtime_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["SpecConst", tile, rep, runtime])
        
        if tile_runtimes:
            runtime_data["SpecConst"][tile] = runtime_data["SpecConst"].get(tile, []) + tile_runtimes
            print(f"✓ (mean: {statistics.mean(tile_runtimes):.3f}ms)")
        else:
            print("✗ (all runs failed)")
    
    # ========================================
    # 2. Benchmark #define Version
    # ========================================
    print_header("2. Benchmarking #define Version")
    
    for idx, tile in enumerate(TILE_SIZES):
        print(f"  Tile size {tile} (iteration {idx+1}/{len(TILE_SIZES)}): ", end="", flush=True)
        
        # Measure compilation time
        output_file = f"matmul_define_{tile}"
        compile_time = measure_compile_time(
            DEFINE_SRC,
            output_file,
            extra_flags=[f"-DTILE_SIZE={tile}"]
        )
        
        if compile_time is None:
            print(f"✗ (compilation failed)")
            continue
        
        compile_data["Define"].append(compile_time)
        
        with open(compile_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Define", tile, idx, compile_time])
        
        # Run multiple times
        tile_runtimes = []
        for rep in range(1, REPETITIONS + 1):
            runtime = measure_runtime(output_file, [MATRIX_SIZE])
            if runtime is None:
                print(f"\n    ERROR: Run {rep} failed")
                continue
            tile_runtimes.append(runtime)
            
            with open(runtime_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Define", tile, rep, runtime])
        
        if tile_runtimes:
            runtime_data["Define"][tile] = runtime_data["Define"].get(tile, []) + tile_runtimes
            print(f"✓ (compile: {compile_time:.3f}s, mean runtime: {statistics.mean(tile_runtimes):.3f}ms)")
        else:
            print(f"✗ (compile: {compile_time:.3f}s, all runs failed)")
    
    # ========================================
    # 3. Generate Summary
    # ========================================
    print_header("3. Summary Statistics")
    
    # Compilation time summary
    print("\nCOMPILATION TIME SUMMARY")
    print("-" * 60)
    print(f"Specialization Constant (single compilation):")
    print(f"  Total: {compile_data['SpecConst'][0]:.3f}s")
    
    if compile_data['Define']:
        print(f"\n#define (per tile compilation):")
        print(f"  Mean: {statistics.mean(compile_data['Define']):.3f}s")
        print(f"  Median: {statistics.median(compile_data['Define']):.3f}s")
        print(f"  Std Dev: {statistics.stdev(compile_data['Define']) if len(compile_data['Define']) > 1 else 0:.3f}s")
        print(f"  Total for all tiles: {sum(compile_data['Define']):.3f}s")
    
    # Runtime summary
    print("\n" + "-" * 60)
    print("RUNTIME SUMMARY (averaged across repetitions)")
    print("-" * 60)
    
    # Write summary CSV
    with open(summary_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Method', 'TileSize', 'MeanRuntime(ms)', 'MedianRuntime(ms)', 'StdDev(ms)'])
        
        for method in ['SpecConst', 'Define']:
            print(f"\n{method}:")
            for tile in sorted(runtime_data[method].keys(), key=int):
                times = runtime_data[method][tile]
                if not times:
                    continue
                mean_time = statistics.mean(times)
                median_time = statistics.median(times)
                std_time = statistics.stdev(times) if len(times) > 1 else 0
                writer.writerow([method, tile, f'{mean_time:.3f}', f'{median_time:.3f}', f'{std_time:.3f}'])
                print(f"  Tile {tile:>3}: {mean_time:>8.3f}ms ± {std_time:>6.3f}ms")
    
    # Overall comparison
    print("\n" + "-" * 60)
    print("OVERALL COMPARISON")
    print("-" * 60)
    
    spec_all_runtimes = [t for times in runtime_data['SpecConst'].values() for t in times]
    define_all_runtimes = [t for times in runtime_data['Define'].values() for t in times]
    
    if spec_all_runtimes and define_all_runtimes:
        print(f"Specialization Constant - Overall Mean Runtime: {statistics.mean(spec_all_runtimes):.3f}ms")
        print(f"#define - Overall Mean Runtime: {statistics.mean(define_all_runtimes):.3f}ms")
        
        if compile_data['Define']:
            speedup = sum(compile_data['Define']) / compile_data['SpecConst'][0]
            print(f"\nCompilation Time Speedup: {speedup:.2f}x")
            print(f"  (SpecConst compiles once in {compile_data['SpecConst'][0]:.3f}s)")
            print(f"  (#define compiles {len(compile_data['Define'])}x for total {sum(compile_data['Define']):.3f}s)")
        
        ratio = statistics.mean(define_all_runtimes) / statistics.mean(spec_all_runtimes)
        print(f"Performance Ratio (Runtime #define / Runtime SpecConst): {ratio:.3f}x")
    
    # ========================================
    # Cleanup
    # ========================================
    print_header("Benchmark Complete!")
    print(f"Results saved to:")
    print(f"  - {compile_csv}")
    print(f"  - {runtime_csv}")
    print(f"  - {summary_csv}")
    
    print("\nCleaning up executables...")
    for exe in ["matmul_spec_const"] + [f"matmul_define_{tile}" for tile in TILE_SIZES]:
        if os.path.exists(exe):
            os.remove(exe)
    print("Done!")
    
    return 0


if __name__ == "__main__":
    exit(main())
