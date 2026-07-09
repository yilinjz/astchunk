"""
ASTChunk - AST-based code chunking library.

This package provides tools for intelligently chunking source code
while preserving syntactic structure and semantic boundaries.
"""

from .astchunk_builder import ASTChunkBuilder, get_supported_languages, LANGUAGE_MAP
from .astchunk import ASTChunk
from .astnode import ASTNode
from .preprocessing import (
    ByteRange,
    IntRange,
    preprocess_nws_count,
    get_nws_count,
    get_nws_count_direct,
    get_nodes_in_brange,
    get_largest_node_in_brange
)

__version__ = "0.1.0"

__all__ = [
    "ASTChunkBuilder",
    "ASTChunk",
    "ASTNode",
    "ByteRange",
    "IntRange",
    "preprocess_nws_count",
    "get_nws_count",
    "get_nws_count_direct",
    "get_nodes_in_brange",
    "get_largest_node_in_brange",
    "get_supported_languages",
    "LANGUAGE_MAP",
]
