# My AutoTuning Workspace

## Symbolic Regression And CUDA MatMul
https://github.com/salehjg/autotuning-with-symbolic-regression  
  
This is the repo in which I implemented the CUDA kernel and scripts to brute force many combinations to train a symbolic regression model (pysr) to predict runtime of the kernel based on the given values for the tunable parameters.

## LLM Embeddings For A Code
Under `ollama-embed/` is the code to use ollama server and models to extract the embeddings for any code with the purpose of using them to as features that are truely independent from the hardware.

## Effect of SYCL Specialization Constant In Compilation Time
Under `sycl-spec-const` is the script to measure how much spec. const. of SYCL decreases the time spent on compiling many cases in a auto-tuning setup.


