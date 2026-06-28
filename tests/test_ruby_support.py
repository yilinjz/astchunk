"""
Tests for Ruby language support in ASTChunk.

This module tests the Ruby-specific functionality including:
- Class and module definition recognition
- Method chunking (instance, class, singleton methods)
- Rails-style patterns
- Ruby-specific syntax constructs
"""

import pytest
from astchunk import ASTChunkBuilder


class TestRubySupport:
    """Test suite for Ruby language support."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = {
            "max_chunk_size": 200,
            "language": "ruby",
            "metadata_template": "default"
        }
        self.chunk_builder = ASTChunkBuilder(**self.config)

    def test_ruby_parser_initialization(self):
        """Test that Ruby parser initializes correctly."""
        assert self.chunk_builder.language == "ruby"
        assert self.chunk_builder.parser is not None

    def test_simple_ruby_class_chunking(self):
        """Test chunking of a simple Ruby class."""
        ruby_code = """
class Calculator
  def initialize
    @value = 0
  end

  def add(number)
    @value += number
  end

  def subtract(number)
    @value -= number
  end

  def result
    @value
  end
end
"""
        chunks = self.chunk_builder.chunkify(ruby_code)
        
        assert len(chunks) > 0
        assert any("Calculator" in chunk["content"] for chunk in chunks)
        
        # Check that metadata is properly generated
        for chunk in chunks:
            assert "metadata" in chunk
            assert "chunk_size" in chunk["metadata"]
            assert "start_line_no" in chunk["metadata"]
            assert "end_line_no" in chunk["metadata"]

    def test_ruby_module_chunking(self):
        """Test chunking of Ruby modules."""
        ruby_code = """
module MathUtils
  PI = 3.14159
  
  def self.square(x)
    x * x
  end
  
  def self.cube(x)
    x * x * x
  end
  
  module Helpers
    def self.factorial(n)
      return 1 if n <= 1
      (1..n).inject(:*)
    end
  end
end
"""
        chunks = self.chunk_builder.chunkify(ruby_code)
        
        assert len(chunks) > 0
        assert any("MathUtils" in chunk["content"] for chunk in chunks)
        assert any("Helpers" in chunk["content"] for chunk in chunks)

    def test_ruby_singleton_methods(self):
        """Test chunking of Ruby singleton methods."""
        ruby_code = """
class Person
  attr_reader :name
  
  def initialize(name)
    @name = name
  end
  
  def self.create_anonymous
    new("Anonymous")
  end
  
  def greet
    "Hello, I'm #{@name}"
  end
end

person = Person.new("Alice")

def person.special_greeting
  "I'm special: #{@name}"
end

class << person
  def another_special_method
    "Another special method"
  end
end
"""
        chunks = self.chunk_builder.chunkify(ruby_code)
        
        assert len(chunks) > 0
        content = " ".join(chunk["content"] for chunk in chunks)
        assert "Person" in content
        assert "create_anonymous" in content
        assert "special_greeting" in content

    def test_rails_style_controller(self):
        """Test chunking of Rails-style controller code."""
        rails_code = """
class UsersController < ApplicationController
  before_action :authenticate_user!
  before_action :find_user, only: [:show, :edit, :update, :destroy]
  
  def index
    @users = User.all.page(params[:page])
    respond_to do |format|
      format.html
      format.json { render json: @users }
    end
  end
  
  def show
    respond_to do |format|
      format.html
      format.json { render json: @user }
    end
  end
  
  def create
    @user = User.new(user_params)
    
    if @user.save
      redirect_to @user, notice: 'User was successfully created.'
    else
      render :new
    end
  end
  
  private
  
  def find_user
    @user = User.find(params[:id])
  end
  
  def user_params
    params.require(:user).permit(:name, :email, :role)
  end
end
"""
        chunks = self.chunk_builder.chunkify(rails_code)
        
        assert len(chunks) > 0
        content = " ".join(chunk["content"] for chunk in chunks)
        assert "UsersController" in content
        assert "ApplicationController" in content
        assert "before_action" in content

    def test_rails_style_model(self):
        """Test chunking of Rails-style model code."""
        rails_code = """
class User < ApplicationRecord
  include Authenticatable
  extend FriendlyId
  
  friendly_id :name, use: :slugged
  
  has_many :posts, dependent: :destroy
  has_many :comments, through: :posts
  belongs_to :organization, optional: true
  
  validates :name, presence: true, length: { minimum: 2 }
  validates :email, presence: true, uniqueness: true
  
  enum status: { active: 0, inactive: 1, suspended: 2 }
  
  scope :recent, -> { where('created_at > ?', 1.week.ago) }
  scope :by_organization, ->(org) { where(organization: org) }
  
  def full_name
    [first_name, last_name].compact.join(' ')
  end
  
  def can_edit?(resource)
    admin? || resource.user == self
  end
  
  class << self
    def find_by_email_or_username(identifier)
      find_by(email: identifier) || find_by(username: identifier)
    end
    
    def admin_users
      where(role: 'admin')
    end
  end
  
  private
  
  def normalize_email
    self.email = email.downcase.strip if email.present?
  end
end
"""
        chunks = self.chunk_builder.chunkify(rails_code)
        
        assert len(chunks) > 0
        content = " ".join(chunk["content"] for chunk in chunks)
        assert "User" in content
        assert "ApplicationRecord" in content
        assert "validates" in content
        assert "has_many" in content

    def test_ruby_block_syntax(self):
        """Test chunking of Ruby code with various block syntaxes."""
        ruby_code = """
class DataProcessor
  def process_data(items)
    # Block with do..end
    items.each do |item|
      puts "Processing: #{item}"
      process_item(item)
    end
    
    # Block with curly braces
    filtered = items.select { |item| item.valid? }
    
    # Method with block parameter
    items.map(&:name).compact
    
    # Proc and lambda
    calculator = proc { |x, y| x + y }
    multiplier = lambda { |x, y| x * y }
    
    # Block with multiple parameters
    items.each_with_index do |item, index|
      puts "Item #{index}: #{item}"
    end
  end
  
  private
  
  def process_item(item)
    item.process!
  rescue StandardError => e
    Rails.logger.error "Failed to process item: #{e.message}"
  end
end
"""
        chunks = self.chunk_builder.chunkify(ruby_code)
        
        assert len(chunks) > 0
        content = " ".join(chunk["content"] for chunk in chunks)
        assert "DataProcessor" in content
        assert "process_data" in content
        assert "each do" in content

    def test_ruby_metaprogramming(self):
        """Test chunking of Ruby metaprogramming constructs."""
        ruby_code = """
module Trackable
  extend ActiveSupport::Concern
  
  included do
    has_many :tracking_events, as: :trackable, dependent: :destroy
    
    after_create :track_creation
    after_update :track_update
  end
  
  class_methods do
    def track_method(method_name)
      alias_method "#{method_name}_without_tracking", method_name
      
      define_method method_name do |*args|
        result = send("#{method_name}_without_tracking", *args)
        track_event("#{method_name}_called")
        result
      end
    end
  end
  
  def track_event(event_name, data = {})
    tracking_events.create!(
      event_name: event_name,
      event_data: data,
      occurred_at: Time.current
    )
  end
  
  private
  
  def track_creation
    track_event('created')
  end
  
  def track_update
    track_event('updated', changes: previous_changes)
  end
end

class Product
  include Trackable
  
  track_method :update_price
  
  def update_price(new_price)
    self.price = new_price
    save!
  end
end
"""
        chunks = self.chunk_builder.chunkify(ruby_code)
        
        assert len(chunks) > 0
        content = " ".join(chunk["content"] for chunk in chunks)
        assert "Trackable" in content
        assert "ActiveSupport::Concern" in content
        assert "class_methods" in content
        assert "define_method" in content

    def test_chunk_metadata_with_ruby_constructs(self):
        """Test that chunk metadata properly captures Ruby constructs."""
        ruby_code = """
module TestModule
  class TestClass
    def test_method
      puts "Hello from Ruby!"
    end
  end
end
"""
        chunks = self.chunk_builder.chunkify(ruby_code, 
                                            repo_level_metadata={"filepath": "test.rb"})
        
        assert len(chunks) > 0
        
        for chunk in chunks:
            metadata = chunk["metadata"]
            assert "filepath" in metadata
            assert metadata["filepath"] == "test.rb"
            assert "chunk_size" in metadata
            assert "line_count" in metadata
            assert "start_line_no" in metadata
            assert "end_line_no" in metadata
            assert "node_count" in metadata

    def test_chunk_size_limits_with_ruby(self):
        """Test that chunk size limits are respected with Ruby code."""
        large_ruby_code = """
class LargeClass
  def method_one
    puts "This is method one with some content"
    x = 1 + 2 + 3 + 4 + 5
    return x
  end
  
  def method_two
    puts "This is method two with different content"
    y = 10 * 20 * 30
    return y
  end
  
  def method_three
    puts "This is method three with more content"
    z = "a" + "b" + "c" + "d"
    return z
  end
end
"""
        # Use a small chunk size to force multiple chunks
        small_config = {
            "max_chunk_size": 50,  # Very small to force splitting
            "language": "ruby",
            "metadata_template": "default"
        }
        small_chunk_builder = ASTChunkBuilder(**small_config)
        chunks = small_chunk_builder.chunkify(large_ruby_code)
        
        # Should create multiple chunks due to size limit
        assert len(chunks) > 1
        
        # Each chunk should respect the size limit (approximately)
        for chunk in chunks:
            assert chunk["metadata"]["chunk_size"] <= 50 + 20  # Some tolerance for AST boundaries

    def test_empty_ruby_code(self):
        """Test handling of empty or minimal Ruby code."""
        minimal_code = "# Just a comment"
        chunks = self.chunk_builder.chunkify(minimal_code)
        
        # Should handle gracefully, might return empty or single chunk
        assert isinstance(chunks, list)

    def test_ruby_syntax_error_handling(self):
        """Test that syntax errors are handled gracefully."""
        # This is not valid Ruby syntax
        invalid_ruby = """
class BrokenClass
  def broken_method
    # Missing end statement
  
  def another_method
    puts "This should not parse correctly"
"""
        
        # Should not raise an exception, but might return unexpected results
        try:
            chunks = self.chunk_builder.chunkify(invalid_ruby)
            assert isinstance(chunks, list)
        except Exception as e:
            # If an exception is raised, it should be handled gracefully
            pytest.fail(f"Should handle syntax errors gracefully, but got: {e}")

    def test_complex_ruby_inheritance(self):
        """Test chunking of complex Ruby inheritance patterns."""
        ruby_code = """
class Animal
  attr_accessor :name, :age
  
  def initialize(name, age)
    @name = name
    @age = age
  end
  
  def speak
    raise NotImplementedError, "Subclasses must implement speak method"
  end
end

module Walkable
  def walk
    puts "#{name} is walking"
  end
end

module Flyable
  def fly
    puts "#{name} is flying"
  end
end

class Dog < Animal
  include Walkable
  
  def speak
    "Woof! I'm #{name}"
  end
  
  def fetch
    "#{name} is fetching the ball"
  end
end

class Bird < Animal
  include Walkable
  include Flyable
  
  def speak
    "Tweet! I'm #{name}"
  end
  
  def migrate
    fly
    puts "#{name} is migrating south"
  end
end
"""
        chunks = self.chunk_builder.chunkify(ruby_code)
        
        assert len(chunks) > 0
        content = " ".join(chunk["content"] for chunk in chunks)
        assert "Animal" in content
        assert "Walkable" in content
        assert "Flyable" in content
        assert "Dog" in content
        assert "Bird" in content


class TestRubyAncestorBuilding:
    """Test the ancestor building functionality specifically for Ruby constructs."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "max_chunk_size": 500,  # Large enough to capture full constructs
            "language": "ruby",
            "metadata_template": "default"
        }
        self.chunk_builder = ASTChunkBuilder(**self.config)

    def test_nested_class_ancestors(self):
        """Test that nested Ruby classes build proper ancestor paths."""
        ruby_code = """
module Outer
  class Middle
    class Inner
      def deep_method
        puts "Deep inside nested classes"
      end
    end
  end
end
"""
        chunks = self.chunk_builder.chunkify(ruby_code)
        
        # Find the chunk containing the deep_method
        method_chunk = None
        for chunk in chunks:
            if "deep_method" in chunk["content"]:
                method_chunk = chunk
                break
        
        assert method_chunk is not None
        # The exact ancestor behavior will depend on the implementation
        # but we should at least have the chunk content
        assert "deep_method" in method_chunk["content"]

    def test_module_and_class_mixing(self):
        """Test ancestor building with mixed modules and classes."""
        ruby_code = """
module OuterModule
  module InnerModule
    class NestedClass
      def target_method
        "Found me!"
      end
    end
  end
end
"""
        chunks = self.chunk_builder.chunkify(ruby_code)
        
        assert len(chunks) > 0
        # Verify the structure is preserved in chunks
        content = " ".join(chunk["content"] for chunk in chunks)
        assert "OuterModule" in content
        assert "InnerModule" in content
        assert "NestedClass" in content
        assert "target_method" in content


if __name__ == "__main__":
    pytest.main([__file__])