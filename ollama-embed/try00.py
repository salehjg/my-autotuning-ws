from ollama import Client

# Connect to the local Ollama server
client = Client(host='http://localhost:11434')

# The code snippet you want to embed
code1 = """
#include <iostream>
int add(int *a, int *b) {
    int c = 0;
    #pragma unroll factor=2
    for (int i = 0; i < 1000000; i++) {
        c += (*a + *b);
    }
    return c;
}
"""

code2 = """
#include <iostream>
int add(int *a, int *bbbb) {
    int c = 0;
    #pragma unroll factor=4
    for (int i = 0; i < 1000000; i++) {
        c += (*a + *bbbb);
    }
    return c;
}
"""

# Generate embeddings
response1 = client.embed(
    model='qwen3-embedding:8b',
    input=code1
)
# Generate embeddings
response2 = client.embed(
    model='qwen3-embedding:8b',
    input=code2
)

# The embedding vector
embedding1 = response1['embeddings'][0]
embedding2 = response2['embeddings'][0]

print("Embedding length:", len(embedding1))
print("First 10 dims:", embedding1[:10])

print("Embedding length:", len(embedding2))
print("First 10 dims:", embedding2[:10])

# Compute cosine similarity
import numpy as np
def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)
similarity = cosine_similarity(np.array(embedding1), np.array(embedding2))
print(f"Cosine similarity between code snippets: {similarity:.4f}")
