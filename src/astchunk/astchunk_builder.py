import numpy as np
from typing import Generator

import tree_sitter as ts
from tree_sitter_language_pack import get_parser
import pyrsistent

from astchunk.astnode import ASTNode
from astchunk.astchunk import ASTChunk
from astchunk.preprocessing import (
    ByteRange,
    preprocess_nws_count,
    get_nws_count
)

# Language name mapping for tree-sitter-language-pack
# Maps user-friendly names to tree-sitter-language-pack language identifiers
LANGUAGE_MAP = {
    # Original supported languages
    "python": "python",
    "java": "java",
    "csharp": "c_sharp",
    "c_sharp": "c_sharp",
    "typescript": "tsx",
    "tsx": "tsx",
    # Additional languages supported by tree-sitter-language-pack
    "javascript": "javascript",
    "jsx": "javascript",
    "c": "c",
    "cpp": "cpp",
    "c++": "cpp",
    "go": "go",
    "golang": "go",
    "rust": "rust",
    "ruby": "ruby",
    "php": "php",
    "swift": "swift",
    "kotlin": "kotlin",
    "scala": "scala",
    "html": "html",
    "css": "css",
    "json": "json",
    "yaml": "yaml",
    "toml": "toml",
    "markdown": "markdown",
    "bash": "bash",
    "shell": "bash",
    "sql": "sql",
    "lua": "lua",
    "r": "r",
    "julia": "julia",
    "haskell": "haskell",
    "elixir": "elixir",
    "erlang": "erlang",
    "clojure": "clojure",
    "ocaml": "ocaml",
    "zig": "zig",
    "nim": "nim",
    "dart": "dart",
    "perl": "perl",
    "dockerfile": "dockerfile",
    "make": "make",
    "cmake": "cmake",
    "xml": "xml",
    "vue": "vue",
    "svelte": "svelte",
}


def get_supported_languages() -> list[str]:
    """
    Get a list of all supported programming languages.

    Returns:
        A sorted list of supported language names.
    """
    return sorted(set(LANGUAGE_MAP.keys()))


class ASTChunkBuilder():
    """
    Attributes:
        - max_chunk_size: Maximum size for each AST chunk, using non-whitespace character count by default.
        - language: Supported languages. Now supports 40+ languages via tree-sitter-language-pack.
        - metadata_template: Type of metadata to store (e.g., start/end line number, path to file, etc).
    """
    def __init__(self, **configs):
        self.max_chunk_size: int = configs['max_chunk_size']
        self.language: str = configs['language']
        self.metadata_template: str = configs['metadata_template']

        # Normalize language name and get the parser
        lang_key = self.language.lower()
        if lang_key not in LANGUAGE_MAP:
            available = sorted(set(LANGUAGE_MAP.keys()))
            raise ValueError(
                f"Unsupported Programming Language: {self.language}! "
                f"Available languages: {', '.join(available)}"
            )

        ts_language = LANGUAGE_MAP[lang_key]
        self.parser = get_parser(ts_language)

    # ------------------------------ #
    #            Step #1             #
    # ------------------------------ #
    def assign_tree_to_windows(self, code: str, root_node: ts.Node) -> Generator[list[ASTNode], None, None]:
        """
        Assign AST tree to windows. A window is a tentative chunk consists of ASTNode before being converted into ASTChunk.

        This function serves as a wrapper function for self.assign_nodes_to_windows(). 
        Additionally, it also
            1. performs preprocessing for efficient AST node size computation.
            2. handles the edge case where the entire AST tree can fit in one window.

        Args:
            code: code to be chunked
            root_node: root node of the AST tree

        Yields:
            Lists (windows) of ASTNode
        """
        # Preprocessing non-whitespace character count
        nws_cumsum = preprocess_nws_count(bytes(code, "utf8"))
        tree_range = ByteRange(root_node.start_byte, root_node.end_byte)
        tree_size = get_nws_count(nws_cumsum, tree_range)

        # If the entire tree can fit in one window, assign tree to window
        if tree_size <= self.max_chunk_size:
            yield [ASTNode(root_node, tree_size)]
        # Otherwise, recursively assign children to windows
        else:
            ancestors = pyrsistent.v(root_node)
            yield from self.assign_nodes_to_windows(root_node.children, nws_cumsum, ancestors)
    
    def assign_nodes_to_windows(self, nodes: list[ts.Node], nws_cumsum: np.ndarray, ancestors: pyrsistent.pvector) -> Generator[list[ASTNode], None, None]:
        """
        Assign AST nodes to windows. A window is a tentative chunk consists of ASTNode before being converted into ASTChunk.

        This function:
            1. greedily assigns AST nodes to windows based on their non-whitespace character count.
            2. recursively processes child nodes if the current node exceeds the max chunk size.
            3. keeps track of the ancestors of each node for path construction.

        Args:
            nodes: list of AST nodes to be assigned to windows
            nws_cumsum: cumulative sum of non-whitespace characters
            ancestors: ancestors of the current node

        Yields:
            Lists (windows) of ASTNode
        """
        # Base case: no nodes to assign
        if not nodes:
            yield from []
            return

        # Initialize the current window
        current_window = []
        current_window_size = 0

        for node in nodes:
            node_range = ByteRange(node.start_byte, node.end_byte)
            node_size = get_nws_count(nws_cumsum, node_range)
            
            # Check if node needs recursive processing (i.e., too large to fit in a window)
            node_exceeds_limit = node_size > self.max_chunk_size
            
            # Handle the cases where we cannot add the current node to the current window
            # Case 1: current window is empty and node exceeds limit
            # Case 2: current window is not empty and adding the node exceeds limit
            if (len(current_window) == 0 and node_exceeds_limit) or \
            (current_window_size + node_size > self.max_chunk_size):
                
                # Clear current window if not empty
                if len(current_window) > 0:
                    yield current_window
                    current_window = []
                    current_window_size = 0
                
                # If node still exceeds limit, recursively process the node's children
                if node_exceeds_limit:
                    childs_ancestors = ancestors.append(node)
                    child_windows = list(self.assign_nodes_to_windows(node.children, nws_cumsum, childs_ancestors))
                    if child_windows:
                        # (optional) Greedily merge adjacent windows from the beginning if merged window does not exceed self.max_chunk_size
                        yield from self.merge_adjacent_windows(child_windows)
                else:
                    # Node fits in an empty window
                    current_window.append(ASTNode(node, node_size, ancestors))
                    current_window_size += node_size
                    
            # Case 3: node fits in current window
            else:
                current_window.append(ASTNode(node, node_size, ancestors))
                current_window_size += node_size

        # Add the last window if it's not empty
        if len(current_window) > 0:
            yield current_window
    
    def merge_adjacent_windows(self, ast_windows: list[list[ASTNode]]) -> Generator[list[ASTNode], None, None]:
        """
        Greedily merge adjacent windows of ASTNode if the merged window's total non whitespace character count
        does not exceed max_char_count.

        We choose to merge child windows in this function instead of self.assign_nodes_to_windows() because
        we want to maintain the structure of the original AST as much as possible. Therefore, we should only
        merge windows if all ASTNodes in the window are siblings.
        
        Args:
            ast_windows: A list of list (windows) of ASTNode
            
        Yields:
            Lists (windows) of ASTNode with adjacent windows merged where possible
        """
        assert ast_windows, "Expect non-empty ast_windows"
        
        # Start with a copy of the first list
        merged_windows = [ast_windows[0][:]]  
        
        for window in ast_windows[1:]:
            current_extending_window = merged_windows[-1]
            
            # Calculate the total character count if we merge
            merged_window_size = sum(n.size for n in current_extending_window) + sum(n.size for n in window)
            
            # If merging won't exceed the limit, merge the lists
            if merged_window_size <= self.max_chunk_size:
                current_extending_window.extend(window)
            else:
                # Otherwise, add the current list as a new entry
                merged_windows.append(window[:])
        
        yield from merged_windows
    
    # ------------------------------ #
    #            Step #2             #
    # ------------------------------ #
    def add_window_overlapping(self, ast_windows: list[list[ASTNode]], chunk_overlap: int) -> list[list[ASTNode]]:
        """
        Extend each window by adding overlapping ASTNodes from the previous and next window.

        Similar to regular document chunking, we add overlapping ASTNodes from the previous and next window
        to each window to provide context. However, we make this step optional since (1) AST Chunking naturally
        avoids breaking the struture of code, hence overlapping is less necessary for maintaining the completeness of
        code blocks (though the additional context may still be useful for downstream tasks); (2) overlapping
        ASTNodes from adjacent windows may cause high variance in chunk size, which makes it difficult to
        control each chunk's token count (especially when the downstream model has a strict limit on context length).

        Args:
            ast_windows: A list of list (windows) of ASTNode
            chunk_overlap: Number of ASTNodes to overlap between adjacent windows

        Returns:
            A list of list (windows) of ASTNode with overlapping ASTNodes added
        """
        assert chunk_overlap >= 0, f"Expect non-negative chunk_overlap, got {chunk_overlap}"

        if chunk_overlap == 0:
            return ast_windows

        new_code_windows = list[list[ASTNode]]()

        for i in range(len(ast_windows)):
            # Create a copy of the current window
            current_node_list = ast_windows[i].copy()
            
            # If there is a previous window, prepend its last chunk_overlap elements
            if i > 0:
                assert len(ast_windows[i-1]) > 0, f"Attempting to take elements from an empty window at {i-1}!"
                prev_window = ast_windows[i-1]
                last_k_nodes = prev_window[-min(chunk_overlap, len(prev_window)):]
                # Insert at the beginning (prepending all elements)
                current_node_list = last_k_nodes + current_node_list
            
            # If there is a next window, append its first chunk_overlap elements
            if i < len(ast_windows) - 1:
                assert len(ast_windows[i+1]) > 0, f"Attempting to take elements from an empty window at {i+1}!"
                next_window = ast_windows[i+1]
                first_k_nodes = next_window[:min(chunk_overlap, len(next_window))]
                # Append all elements
                current_node_list = current_node_list + first_k_nodes
                
            new_code_windows.append(current_node_list)
            
        return new_code_windows
    
    # ------------------------------ #
    #            Step #3             #
    # ------------------------------ #
    def convert_windows_to_chunks(self, ast_windows: list[list[ASTNode]], 
                                  repo_level_metadata: dict, chunk_expansion: bool) -> list[ASTChunk]:
        """
        Convert each tentative window of ASTNode into an ASTChunk object.

        This function finalizes the boundary of each chunk and build metadata for each chunk.
        Additionally, it also applies chunk expansion if specified. Chunk expansion is the process of
        adding chunk metadata (e.g., file path, class path) to the beginning of each chunk. It can consist of information
        (1) available in all chunking frameworks (e.g., file path, start line, end line, etc.) and
        (2) specific to AST Chunking (e.g., class path, function path, etc.).
        We found that chunk expansion can be helpful for downstream retrieval and sometimes generation tasks. 
        However, it is also worth noting that chunk expansion consumes additional tokens, thereby reducing the number of chunks that can fit in the context window.
        Hence, we make chunk expansion an optional step that can be turned on / off via the `chunk_expansion` flag.

        Args:
            ast_windows: A list of list (windows) of ASTNode
            repo_level_metadata: Repository-level metadata (e.g., repo name, file path)
            chunk_expansion: Whether to perform chunk expansion (i.e., add metadata headers to chunks)

        Returns:
            A list of ASTChunk objects
        """
        ast_chunks = list[ASTChunk]()

        for current_window in ast_windows:
            current_chunk = ASTChunk(
                ast_window=current_window,
                max_chunk_size=self.max_chunk_size,
                language=self.language,
                metadata_template=self.metadata_template
            )
            current_chunk.build_metadata(repo_level_metadata)
            
            # (optional) apply chunk expansion
            if chunk_expansion:
                current_chunk.apply_chunk_expansion()
            ast_chunks.append(current_chunk)

        return ast_chunks
    
    # ------------------------------ #
    #            Step #4             #
    # ------------------------------ #
    def convert_chunks_to_code_windows(self, ast_chunks: list[ASTChunk]) -> list[dict]:
        """
        Convert each ASTChunk object into a code window for downstream integration.

        Args:
            ast_chunks: A list of ASTChunk objects

        Returns:
            A list of code windows, where each code window is a dict with keys "content" and "metadata"
        """
        code_windows = []

        for current_chunk in ast_chunks:
            code_windows.append(current_chunk.to_code_window())
        
        return code_windows

    # ------------------------------ #
    #       AST Chunking Logic       #
    # ------------------------------ #
    def chunkify(self, code: str, **configs) -> list[dict]:
        '''
        Parse a piece of code into structual-aware chunks using AST.

        Args:
            code: code to be chunked
            **configs: additional arguments for building chunks and/or chunk metadata
        '''
        # step 1: greedily assign AST tree / AST nodes to windows
        #         see self.assign_tree_to_windows() and self.assign_nodes_to_windows() for details
        ast = self.parser.parse(bytes(code, "utf8"))
        ast_windows = list(self.assign_tree_to_windows(
            code=code, 
            root_node=ast.root_node
        ))
        # [after this step]: list[list[ASTNode]] where each sublist represents an AST window

        # step 2 (optional): add overlapping
        #                    for each window, take the last k ASTNodes from the previous window and the first k ASTNodes from the next window
        ast_windows = self.add_window_overlapping(
            ast_windows=ast_windows,
            chunk_overlap=configs.get("chunk_overlap", 0)
        )
        # [after this step]: list[list[ASTNode]] where each sublist represents an AST window

        # step 3: convert each AST window into an ASTChunk object
        ast_chunks = self.convert_windows_to_chunks(
            ast_windows=ast_windows,
            repo_level_metadata=configs.get("repo_level_metadata", {}),
            chunk_expansion=configs.get("chunk_expansion", False)
        )
        # [after this step]: list[ASTChunk]

        # step 4: convert each ASTChunk to a code window for downstream integration
        code_windows = self.convert_chunks_to_code_windows(
            ast_chunks=ast_chunks
        )
        # [after this step]: list[dict] where each dict represents a code window

        return code_windows
