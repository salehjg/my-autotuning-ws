#!/bin/bash

# Benchmark script to compare SYCL specialization constants vs #define
# Usage: ./benchmark_comparison.sh

set -e

# Configuration
MATRIX_SIZE=1024
TILE_SIZES=(4 8 16 32 64 128 4 8 16 32)  # 10 tile sizes with some repetition
REPETITIONS=10
COMPILER="icpx"
COMPILER_FLAGS="-std=c++17 -fsycl -fsycl-targets=spir64_gen -Xsycl-target-backend \"-device pvc\""

# File names
SPEC_CONST_SRC="matmul.sc.cpp"
DEFINE_SRC="matmul.cpp"
RESULTS_DIR="benchmark_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create results directory
mkdir -p "$RESULTS_DIR"

# CSV output files
COMPILE_CSV="$RESULTS_DIR/compile_times_${TIMESTAMP}.csv"
RUNTIME_CSV="$RESULTS_DIR/runtime_${TIMESTAMP}.csv"
SUMMARY_CSV="$RESULTS_DIR/summary_${TIMESTAMP}.csv"

# Initialize CSV files
echo "Method,TileSize,Repetition,CompileTime(s)" > "$COMPILE_CSV"
echo "Method,TileSize,Run,ExecutionTime(ms)" > "$RUNTIME_CSV"

echo "================================================"
echo "SYCL Specialization Constant vs #define Benchmark"
echo "================================================"
echo "Matrix Size: $MATRIX_SIZE"
echo "Tile Sizes: ${TILE_SIZES[*]}"
echo "Repetitions per tile: $REPETITIONS"
echo "Compiler: $COMPILER"
echo "Results directory: $RESULTS_DIR"
echo ""

# Function to measure compilation time
measure_compile_time() {
    local start=$(date +%s.%N)
    "$@" > /dev/null 2>&1
    local end=$(date +%s.%N)
    echo "$end - $start" | bc
}

# Function to extract runtime from program output
extract_runtime() {
    local output="$1"
    # Assuming the program outputs something we can parse for timing
    # This is a placeholder - adjust based on actual output
    echo "$output" | grep -oP 'Time: \K[0-9.]+' || echo "0"
}

# Function to run executable and measure time
measure_runtime() {
    local executable="$1"
    local args="$2"
    local start=$(date +%s.%N)
    $executable $args > /dev/null 2>&1
    local end=$(date +%s.%N)
    local elapsed=$(echo "($end - $start) * 1000" | bc)
    echo "$elapsed"
}

echo "========================================"
echo "1. Benchmarking Specialization Constant"
echo "========================================"

# Compile once for specialization constant version (AOT compilation)
echo "Compiling specialization constant version..."
SPEC_CONST_COMPILE_START=$(date +%s.%N)
eval $COMPILER $COMPILER_FLAGS -o matmul_spec_const "$SPEC_CONST_SRC"
SPEC_CONST_COMPILE_END=$(date +%s.%N)
SPEC_CONST_TOTAL_COMPILE=$(echo "$SPEC_CONST_COMPILE_END - $SPEC_CONST_COMPILE_START" | bc)

echo "Specialization constant compilation time: ${SPEC_CONST_TOTAL_COMPILE}s"
echo ""

# Run with different tile sizes
echo "Running specialization constant version..."
for idx in "${!TILE_SIZES[@]}"; do
    TILE=${TILE_SIZES[$idx]}
    echo -n "  Tile size $TILE (iteration $((idx+1))/10): "
    
    # Record compile time (same for all, but logged per tile for comparison)
    echo "SpecConst,$TILE,$idx,$SPEC_CONST_TOTAL_COMPILE" >> "$COMPILE_CSV"
    
    # Run multiple times
    for rep in $(seq 1 $REPETITIONS); do
        RUNTIME=$(measure_runtime "./matmul_spec_const" "$MATRIX_SIZE $TILE")
        echo "SpecConst,$TILE,$rep,$RUNTIME" >> "$RUNTIME_CSV"
    done
    echo "✓"
done

echo ""
echo "========================================"
echo "2. Benchmarking #define Version"
echo "========================================"

# Compile and run for each tile size
for idx in "${!TILE_SIZES[@]}"; do
    TILE=${TILE_SIZES[$idx]}
    echo -n "  Tile size $TILE (iteration $((idx+1))/10): "
    
    # Measure compilation time
    DEFINE_COMPILE_START=$(date +%s.%N)
    eval $COMPILER $COMPILER_FLAGS -DTILE_SIZE=$TILE -o "matmul_define_${TILE}" "$DEFINE_SRC"
    DEFINE_COMPILE_END=$(date +%s.%N)
    DEFINE_COMPILE_TIME=$(echo "$DEFINE_COMPILE_END - $DEFINE_COMPILE_START" | bc)
    
    echo "Define,$TILE,$idx,$DEFINE_COMPILE_TIME" >> "$COMPILE_CSV"
    
    # Run multiple times
    for rep in $(seq 1 $REPETITIONS); do
        RUNTIME=$(measure_runtime "./matmul_define_${TILE}" "$MATRIX_SIZE")
        echo "Define,$TILE,$rep,$RUNTIME" >> "$RUNTIME_CSV"
    done
    echo "✓ (compile: ${DEFINE_COMPILE_TIME}s)"
done

echo ""
echo "========================================"
echo "3. Computing Summary Statistics"
echo "========================================"

# Create summary with Python (if available) or awk
if command -v python3 &> /dev/null; then
    python3 << 'EOF'
import csv
import statistics

# Read compile times
compile_data = {'SpecConst': [], 'Define': []}
with open([f for f in __import__('os').listdir('benchmark_results') if 'compile_times' in f][0]) as f:
    reader = csv.DictReader(f)
    for row in reader:
        compile_data[row['Method']].append(float(row['CompileTime(s)']))

# Read runtime
runtime_data = {'SpecConst': {}, 'Define': {}}
with open([f for f in __import__('os').listdir('benchmark_results') if 'runtime' in f][0]) as f:
    reader = csv.DictReader(f)
    for row in reader:
        method = row['Method']
        tile = row['TileSize']
        if tile not in runtime_data[method]:
            runtime_data[method][tile] = []
        runtime_data[method][tile].append(float(row['ExecutionTime(ms)']))

print("\n" + "="*60)
print("COMPILATION TIME SUMMARY")
print("="*60)
print(f"Specialization Constant (single compilation):")
print(f"  Total: {compile_data['SpecConst'][0]:.3f}s")
print(f"\n#define (per tile compilation):")
print(f"  Mean: {statistics.mean(compile_data['Define']):.3f}s")
print(f"  Median: {statistics.median(compile_data['Define']):.3f}s")
print(f"  Std Dev: {statistics.stdev(compile_data['Define']):.3f}s")
print(f"  Total for all tiles: {sum(compile_data['Define']):.3f}s")

print("\n" + "="*60)
print("RUNTIME SUMMARY (averaged across repetitions)")
print("="*60)

# Create summary CSV
summary_file = [f for f in __import__('os').listdir('benchmark_results') if 'summary' in f][0]
with open(summary_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Method', 'TileSize', 'MeanRuntime(ms)', 'MedianRuntime(ms)', 'StdDev(ms)'])
    
    for method in ['SpecConst', 'Define']:
        print(f"\n{method}:")
        for tile in sorted(runtime_data[method].keys(), key=int):
            times = runtime_data[method][tile]
            mean_time = statistics.mean(times)
            median_time = statistics.median(times)
            std_time = statistics.stdev(times) if len(times) > 1 else 0
            writer.writerow([method, tile, f'{mean_time:.3f}', f'{median_time:.3f}', f'{std_time:.3f}'])
            print(f"  Tile {tile:>3}: {mean_time:>8.3f}ms ± {std_time:>6.3f}ms")

print("\n" + "="*60)
print("OVERALL COMPARISON")
print("="*60)
spec_all_runtimes = [t for times in runtime_data['SpecConst'].values() for t in times]
define_all_runtimes = [t for times in runtime_data['Define'].values() for t in times]

print(f"Specialization Constant - Overall Mean Runtime: {statistics.mean(spec_all_runtimes):.3f}ms")
print(f"#define - Overall Mean Runtime: {statistics.mean(define_all_runtimes):.3f}ms")
print(f"\nCompilation Time Speedup: {sum(compile_data['Define']) / compile_data['SpecConst'][0]:.2f}x")
print(f"Runtime Performance Ratio: {statistics.mean(define_all_runtimes) / statistics.mean(spec_all_runtimes):.3f}x")

EOF
else
    echo "Python3 not found. Raw data saved to CSV files."
fi

echo ""
echo "========================================"
echo "Benchmark Complete!"
echo "========================================"
echo "Results saved to:"
echo "  - $COMPILE_CSV"
echo "  - $RUNTIME_CSV"
echo "  - $SUMMARY_CSV"
echo ""

# Cleanup
echo "Cleaning up executables..."
rm -f matmul_spec_const matmul_define_*
echo "Done!"