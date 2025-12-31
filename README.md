# ASTChunk

This repository contains code for AST-based code chunking that preserves syntactic structure and semantic boundaries. ASTChunk intelligently divides source code into meaningful chunks while respecting the Abstract Syntax Tree (AST) structure, making it ideal for code analysis, documentation generation, and machine learning applications.

This work is described in the following paper:  
>[cAST: Enhancing Code Retrieval-Augmented Generation with Structural Chunking via Abstract Syntax Tree](https://arxiv.org/abs/2506.15655)    
> Yilin Zhang, Xinran Zhao, Zora Zhiruo Wang, Chenyang Yang, Jiayi Wei, Tongshuang Wu
<!--
> Conference/Journal, Year
-->

Bibtex for citations:
```bibtex
@misc{zhang-etal-2025-astchunk,
      title={cAST: Enhancing Code Retrieval-Augmented Generation with Structural Chunking via Abstract Syntax Tree}, 
      author={Yilin Zhang and Xinran Zhao and Zora Zhiruo Wang and Chenyang Yang and Jiayi Wei and Tongshuang Wu},
      year={2025},
      url={https://arxiv.org/abs/2506.15655}, 
}
```
<!--
Bibtex for citations:
```bibtex
@inproceedings{<citation_key>,
    title = "<Paper Title>",
    author = "<Authors>",
    booktitle = "<Conference>",
    year = "<Year>",
    url = "<URL>",
    pages = "<Pages>",
}
```
-->

<!--
## Features

- **Structure-aware chunking**: Respects AST boundaries to avoid breaking syntactic constructs
- **Multi-language support**: Python, Java, C#, and TypeScript
- **Configurable chunk sizes**: Based on non-whitespace character count for consistent sizing
- **Metadata preservation**: Maintains file paths, line numbers, and AST context
- **Overlapping support**: Optional overlapping between chunks for better context
- **Efficient processing**: O(1) chunk size lookup with preprocessing
-->

## Installation

From PyPI:
```bash
pip install astchunk
```

From source:
```bash
git clone git@github.com:yilinjz/astchunk.git
pip install -e .
```

**Requirements**: Python 3.10+

ASTChunk depends on [tree-sitter](https://tree-sitter.github.io/tree-sitter/) and [tree-sitter-language-pack](https://github.com/Goldziher/tree-sitter-language-pack) for parsing. All dependencies are automatically installed:

```bash
# Core dependencies (automatically installed)
pip install numpy pyrsistent tree-sitter tree-sitter-language-pack
```

## Configuration Options

- **`max_chunk_size`**: Maximum non-whitespace characters per chunk
- **`language`**: Programming language for parsing
- **`metadata_template`**: Format for chunk metadata
- **`repo_level_metadata`** *(optional)*: Repository-level metadata (e.g., repo name, file path)
- **`chunk_overlap`** *(optional)*: Number of AST nodes to overlap between chunks
- **`chunk_expansion`** *(optional)*: Whether to perform chunk expansion (i.e., add metadata headers to chunks)

## Quick Start

```python
from astchunk import ASTChunkBuilder

# Your source code
code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
"""

# Initialize the chunk builder
configs = {
    "max_chunk_size": 100,             # Maximum non-whitespace characters per chunk
    "language": "python",              # Supports 40+ languages (see below)
    "metadata_template": "default"     # Metadata format for output
}
chunk_builder = ASTChunkBuilder(**configs)

# Create chunks
chunks = chunk_builder.chunkify(code)

# Each chunk contains content and metadata
for i, chunk in enumerate(chunks):
    print(f"[Chunk {i+1}]")
    print(f"{chunk['content']}")
    print(f"Metadata: {chunk['metadata']}")
    print("-" * 50)
```

## Advanced Usage

### Customizing Chunk Parameters

```python

# Add repo-level metadata
configs['repo_level_metadata'] = {
    "filepath": "src/calculator.py"
}

# Enable overlapping between chunks
configs['chunk_overlap'] = 1

# Add chunk expansion (metadata headers)
configs['chunk_expansion'] = True

# NOTE: max_chunk_size apply to the chunks before overlapping or chunk expansion.
# The final chunk size after overlapping or chunk expansion may exceed max_chunk_size.


# Extend current code for illustration
code += """
def divide(self, a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# This is a comment
# Another comment

def subtract(self, a, b):
    return a - b

def exponent(self, a, b):
    return a ** b
"""


# Create chunks
chunks = chunk_builder.chunkify(code, **configs)

for i, chunk in enumerate(chunks):
    print(f"[Chunk {i+1}]")
    print(f"{chunk['content']}")
    print(f"Metadata: {chunk['metadata']}")
    print("-" * 50)
```

### Working with Files

```python
# Process a single file
with open("example.py", "r") as f:
    code = f.read()

# Alternatively, you can also create single-use configs for the optional arguments for each chunkify() call
single_use_configs = {
    "repo_level_metadata": {
        "filepath": "example.py"
    },
    "chunk_expansion": True
}

chunks = chunk_builder.chunkify(code, **single_use_configs)

# Save chunks to separate files
for i, chunk in enumerate(chunks):
    with open(f"chunk_{i+1}.py", "w") as f:
        f.write(chunk['content'])
```

### Processing Multiple Languages

```python
# Python code
python_builder = ASTChunkBuilder(
    max_chunk_size=1500,
    language="python",
    metadata_template="default"
)

# Go code
go_builder = ASTChunkBuilder(
    max_chunk_size=2000,
    language="go",
    metadata_template="default"
)

# Rust code
rust_builder = ASTChunkBuilder(
    max_chunk_size=1800,
    language="rust",
    metadata_template="default"
)

# TypeScript code
ts_builder = ASTChunkBuilder(
    max_chunk_size=1800,
    language="typescript",
    metadata_template="default"
)
```

<!-- ### Metadata Templates

Different metadata templates for various use cases:

```python
# For repoeval
repoeval_builder = ASTChunkBuilder(
    max_chunk_size=2000,
    language="python",
    metadata_template="coderagbench-repoeval"
)

# For swebench-lite
swebench_builder = ASTChunkBuilder(
    max_chunk_size=2000,
    language="python",
    metadata_template="coderagbench-swebench-lite"
)
``` -->

<!-- ## Core Functions

### Preprocessing Functions

```python
from astchunk.preprocessing import preprocess_nws_count, get_nws_count, ByteRange

# Preprocess code for efficient size calculation
code_bytes = code.encode('utf-8')
nws_cumsum = preprocess_nws_count(code_bytes)

# Get non-whitespace character count for any byte range
byte_range = ByteRange(0, 100)  # First 100 bytes
char_count = get_nws_count(nws_cumsum, byte_range)
```

### Direct AST Processing

```python
from astchunk.astnode import ASTNode
from astchunk.astchunk import ASTChunk

# Work directly with AST nodes and chunks for custom processing
# (See API documentation for detailed usage)
``` -->

## Supported Languages

ASTChunk supports **40+ programming languages** via [tree-sitter-language-pack](https://github.com/Goldziher/tree-sitter-language-pack):

| Category | Languages |
|----------|-----------|
| **General Purpose** | Python, Java, C, C++, C#, Go, Rust, Ruby, Swift, Kotlin, Scala, Dart |
| **Web** | JavaScript, TypeScript, HTML, CSS, PHP, Vue, Svelte |
| **Scripting** | Bash/Shell, Lua, Perl, R |
| **Functional** | Haskell, Elixir, Erlang, Clojure, OCaml |
| **Systems** | Zig, Nim |
| **Data/Config** | JSON, YAML, TOML, XML, SQL, Markdown |
| **DevOps** | Dockerfile, Make, CMake |
| **Scientific** | Julia, R |

To list all supported languages programmatically:

```python
from astchunk import get_supported_languages

print(get_supported_languages())
# ['bash', 'c', 'c++', 'clojure', 'cmake', 'cpp', 'csharp', 'css', 'dart', ...]
```

<!-- ## Contributing

We welcome contributions! Please see our [contributing guidelines](<CONTRIBUTING_URL>) for details. -->

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Version

Current version: 0.1.0
