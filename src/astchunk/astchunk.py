from astchunk.astnode import ASTNode
from astchunk.preprocessing import ByteRange, get_nws_count_direct


class ASTChunk():
    """
    A chunk of code represented by a list of ASTNodes.

    This class provides additional information for each chunk, including:
        - chunk_text: rebuilt code text from the list of ASTNodes
        - chunk_size: size of the chunk (in non-whitespace characters)
        - chunk_ancestors: ancestors of the chunk (list of ancestor names)
        - metadata: additional metadata for the chunk (e.g., file path, class path, etc.)

    Attributes:
        - ast_window: list of ASTNode objects
        - max_chunk_size: maximum size for each AST chunk, using non-whitespace character count by default.
        - language: programming language
        - metadata_template: type of metadata to store (e.g., start/end line number, path to file, etc.)
    """
    def __init__(self, ast_window: list[ASTNode], max_chunk_size: int, language: str, metadata_template: str):
        self.ast_window = ast_window
        self.max_chunk_size = max_chunk_size
        self.language = language
        self.metadata_template = metadata_template
        assert len(self.ast_window) > 0, "Expect ASTChunk to be non-empty"

        self.chunk_text = self.rebuild_code(self.ast_window)
        self.chunk_size = get_nws_count_direct(self.chunk_text)

        # build chunk ancestors using the ancestors of the first ASTNode in the window
        self.chunk_ancestors = self.build_chunk_ancestors(self.ast_window[0].ancestors) 

    @property
    def strcode(self):
        return self.chunk_text

    @property
    def brange(self):
        return ByteRange(self.ast_window[0].brange.start, self.ast_window[-1].brange.stop)

    @property
    def start_line(self):
        return self.ast_window[0].start_line

    @property
    def end_line(self):
        return self.ast_window[-1].end_line

    @property
    def size(self):
        """
        Define size as the number of non-whitespace characters.
        """
        return self.chunk_size

    @property
    def length(self):
        """
        Define length as the number of lines covered by the chunk.
        """
        return self.end_line - self.start_line + 1

    def rebuild_code(self, ast_window: list[ASTNode]) -> str:
        """
        Rebuild source code from a list of ASTNodes.

        The code text stored in each ASTNode is inherited from the tree-sitter Node object, which omits 
        leading and trailing spaces and newlines between nodes. Therefore, this function restores the 
        original code by adding the necessary newlines and spaces.

        Args:
            ast_window: list of ASTNode objects

        Returns:
            Rebuilt source code string
        """
        if len(ast_window) == 0:
            return ""

        current_line, current_col = ast_window[0].start_line, ast_window[0].start_col
        code = " " * current_col

        for node in ast_window:
            # If we need to jump to a new line, add newline(s)
            if  node.start_line > current_line:
                # Add as many newlines as needed.
                code += "\n" * (node.start_line - current_line)
                current_line =  node.start_line
                # Reset the column since we are at a new line.
                current_col = 0
            # If we are on the correct line but need to add indentation spaces:
            if  node.start_col > current_col:
                code += " " * (node.start_col - current_col)
                current_col =  node.start_col
            # Append the node_text
            code += node.strcode
            # Update our cursor position to the given end coordinate.
            # (We trust that the given end coordinate is consistent with the node_text.)
            current_line, current_col =  node.end_line,  node.end_col

        return code

    def build_chunk_ancestors(self, node_ancestors: list[ASTNode]) -> list[ASTNode]:
        '''
        Build the class/function/module path to the chunk. The path is built from the ancestors of the first 
        ASTNode in the window. We keep the ancestors that are class, function, or module definitions.

        The intuition is that we want to record where the chunk is located in the AST. This can be useful
        for downstream tasks such as code retrieval (e.g., disambiguating between different functions with the same name).
        For each ancestor that is a class, function, or module definition, we extract the first line in the ancestor's text.
        This simple heuristic is also commonly used in software patching tasks, such as generating GitHub issue fixes, 
        where identifying the location of a change is an essential part of the patch.

        Supported constructs:
        - Python: class_definition, function_definition
        - Ruby: class, module, method, singleton_method, singleton_class

        Args:
            node_ancestors: list of tree-sitter nodes that are ancestors of the first ASTNode in the window

        Returns:
            List of ancestors that are class, function, or module definitions
        '''
        chunk_ancestors = []

        for node in node_ancestors:
            if any([
                node.type == "class_definition",
                node.type == "function_definition",
                node.type == "class",
                node.type == "module",
                node.type == "method",
                node.type == "singleton_method",
                node.type == "singleton_class"
            ]):
                chunk_ancestors.append(node.text.decode("utf8").split("\n")[0])

        return chunk_ancestors

    def build_metadata(self, repo_level_metadata: dict):
        """
        Build metadata for the chunk.

        Args:
            repo_level_metadata: repository-level metadata (e.g., repo name, file path)
        """
        if self.metadata_template == "none":
            self.metadata = {}
        elif self.metadata_template == "default":
            filepath = repo_level_metadata.get("filepath", "")
            self.metadata = {
                "filepath": filepath,
                "chunk_size": self.chunk_size,
                "line_count": self.length,
                "start_line_no": self.start_line,
                "end_line_no": self.end_line,
                "node_count": len(self.ast_window),
            }
        elif self.metadata_template == "coderagbench-repoeval":
            fpath_tuple = repo_level_metadata.get("fpath_tuple", [])
            repo = repo_level_metadata.get("repo", "")
            self.metadata = {
                "fpath_tuple": fpath_tuple,
                "repo": repo,
                "chunk_size": self.chunk_size,
                "line_count": self.length,
                "start_line_no": self.start_line,
                "end_line_no": self.end_line,
                "node_count": len(self.ast_window),
            }
        elif self.metadata_template == "coderagbench-swebench-lite":
            instance_id = repo_level_metadata.get("instance_id", "")
            filename = repo_level_metadata.get("filename", "")
            self.metadata = {
                "_id": f"{instance_id}_{self.start_line}-{self.end_line}",
                "title": filename,
            }
        else:
            raise ValueError(f"Unsupported Metadata Template Name: {self.metadata_template}!")

    def apply_chunk_expansion(self):
        """
        Apply chunk expansion to the chunk. Chunk expansion is the process of adding chunk expansion metadata 
        (e.g., file path, class path) to the beginning of each chunk.
        """
        self.chunk_expansion_metadata = {
            "filepath": "",
            "ancestors": "\n".join(["\t" * i + ancestor for i, ancestor in enumerate(self.chunk_ancestors)]),
        }
        if self.metadata_template == "default":
            self.chunk_expansion_metadata["filepath"] = self.metadata["filepath"]
        elif self.metadata_template == "coderagbench-repoeval":
            self.chunk_expansion_metadata["filepath"] = "/".join(self.metadata["fpath_tuple"]) 
        elif self.metadata_template == "coderagbench-swebench-lite":
            self.chunk_expansion_metadata["filepath"] = self.metadata["title"]

        chunk_expansion = "'''\n"
        chunk_expansion += f"{self.chunk_expansion_metadata['filepath']}\n" if self.chunk_expansion_metadata["filepath"] else ""
        chunk_expansion += f"{self.chunk_expansion_metadata['ancestors']}\n" if self.chunk_expansion_metadata["ancestors"] else ""
        chunk_expansion += "'''"

        self.chunk_text = f"{chunk_expansion}\n{self.chunk_text}"

    def to_code_window(self) -> dict:
        """
        Convert the ASTChunk object into a code window for downstream integration.
        """
        if self.metadata_template == "coderagbench-swebench-lite":
            code_window = {
                "_id": self.metadata["_id"],
                "title": self.metadata['title'],
                "text": self.chunk_text
            }
        else:
            code_window = {
                "content": self.chunk_text,
                "metadata": self.metadata
            }

        return code_window
