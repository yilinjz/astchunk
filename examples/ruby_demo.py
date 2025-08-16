#!/usr/bin/env python3
"""
Ruby chunking demonstration for ASTChunk.

This example shows how to use ASTChunk with Ruby code, demonstrating
the recognition of Ruby-specific constructs like modules, classes, and methods.
"""

from astchunk import ASTChunkBuilder


def main():
    """Demonstrate Ruby chunking capabilities."""
    
    # Ruby code example with various constructs
    ruby_code = """
module UserManagement
  class User
    attr_reader :name, :email
    attr_accessor :status
    
    def initialize(name, email)
      @name = name
      @email = email
      @status = :active
    end
    
    def activate!
      @status = :active
      notify_activation
    end
    
    def deactivate!
      @status = :inactive
      notify_deactivation
    end
    
    private
    
    def notify_activation
      puts "User #{@name} has been activated"
    end
    
    def notify_deactivation
      puts "User #{@name} has been deactivated"
    end
  end
  
  class AdminUser < User
    def initialize(name, email)
      super(name, email)
      @permissions = [:read, :write, :admin]
    end
    
    def grant_permission(permission)
      @permissions << permission unless @permissions.include?(permission)
    end
    
    def has_permission?(permission)
      @permissions.include?(permission)
    end
  end
  
  module Authentication
    def self.authenticate(user, password)
      # Simple authentication logic
      user.status == :active && verify_password(user, password)
    end
    
    private
    
    def self.verify_password(user, password)
      # In a real app, this would check against a secure hash
      password.length >= 8
    end
  end
end
"""
    
    print("Ruby/Rails ASTChunk Demo")
    print("=" * 50)
    
    # Configure the chunk builder for Ruby
    config = {
        "max_chunk_size": 400,  # Moderate chunk size
        "language": "ruby",
        "metadata_template": "default"
    }
    
    chunk_builder = ASTChunkBuilder(**config)
    
    # Add repository-level metadata
    repo_metadata = {
        "filepath": "app/models/user_management.rb"
    }
    
    # Perform chunking
    chunks = chunk_builder.chunkify(ruby_code, 
                                   repo_level_metadata=repo_metadata)
    
    print(f"Generated {len(chunks)} chunks from Ruby code")
    print(f"Original code: {len(ruby_code)} characters")
    print()
    
    # Display chunk information
    for i, chunk in enumerate(chunks):
        content = chunk['content']
        metadata = chunk['metadata']
        
        print(f"Chunk {i+1}:")
        print(f"  File: {metadata['filepath']}")
        print(f"  Lines: {metadata['start_line_no']}-{metadata['end_line_no']} ({metadata['line_count']} lines)")
        print(f"  Size: {metadata['chunk_size']} non-whitespace characters")
        print(f"  AST Nodes: {metadata['node_count']}")
        
        # Show Ruby constructs found
        ruby_keywords = ['module', 'class', 'def ', 'attr_reader', 'attr_accessor', 'include', 'extend']
        found_keywords = [kw for kw in ruby_keywords if kw in content]
        if found_keywords:
            print(f"  Ruby constructs: {', '.join(found_keywords)}")
        
        # Show a preview of the content
        preview = content.strip().split('\n')[0]
        if len(preview) > 60:
            preview = preview[:57] + "..."
        print(f"  Preview: {preview}")
        print()
    
    # Demonstrate chunk expansion
    print("=" * 50)
    print("Chunk Expansion Demo")
    print("=" * 50)
    
    # Create chunks with expansion enabled
    expanded_chunks = chunk_builder.chunkify(
        ruby_code,
        repo_level_metadata=repo_metadata,
        chunk_expansion=True
    )
    
    if expanded_chunks:
        first_chunk = expanded_chunks[0]
        print("First chunk with expansion:")
        print(first_chunk['content'][:300] + "..." if len(first_chunk['content']) > 300 else first_chunk['content'])
    
    print("\n🎉 Ruby chunking demonstration completed!")


if __name__ == "__main__":
    main()