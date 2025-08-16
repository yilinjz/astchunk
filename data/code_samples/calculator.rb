# frozen_string_literal: true

require 'bigdecimal'
require 'bigdecimal/util'

# A comprehensive Ruby calculator example showing various language constructs
module MathUtils
  PI = 3.14159265359.freeze
  E = 2.71828182846.freeze

  # Helper module for common mathematical operations
  module Helpers
    def self.factorial(n)
      return 1 if n <= 1
      (1..n).inject(:*)
    end

    def self.fibonacci(n)
      return n if n <= 1
      fibonacci(n - 1) + fibonacci(n - 2)
    end
  end

  # Main calculator class with comprehensive functionality
  class Calculator
    include Helpers

    attr_reader :history, :precision
    attr_accessor :decimal_places

    def initialize(precision: 10, decimal_places: 2)
      @history = []
      @precision = precision
      @decimal_places = decimal_places
      @memory = BigDecimal('0')
    end

    # Basic arithmetic operations
    def add(a, b)
      result = to_decimal(a) + to_decimal(b)
      log_operation(:add, [a, b], result)
      format_result(result)
    end

    def subtract(a, b)
      result = to_decimal(a) - to_decimal(b)
      log_operation(:subtract, [a, b], result)
      format_result(result)
    end

    def multiply(a, b)
      result = to_decimal(a) * to_decimal(b)
      log_operation(:multiply, [a, b], result)
      format_result(result)
    end

    def divide(a, b)
      raise ArgumentError, "Cannot divide by zero" if b.to_f.zero?
      
      result = to_decimal(a) / to_decimal(b)
      log_operation(:divide, [a, b], result)
      format_result(result)
    end

    def power(base, exponent)
      result = to_decimal(base) ** exponent.to_i
      log_operation(:power, [base, exponent], result)
      format_result(result)
    end

    # Advanced mathematical functions
    def square_root(n)
      raise ArgumentError, "Cannot calculate square root of negative number" if n.to_f < 0
      
      result = Math.sqrt(n.to_f)
      log_operation(:sqrt, [n], result)
      format_result(result)
    end

    def logarithm(n, base = Math::E)
      raise ArgumentError, "Cannot calculate logarithm of non-positive number" if n.to_f <= 0
      
      result = Math.log(n.to_f) / Math.log(base.to_f)
      log_operation(:log, [n, base], result)
      format_result(result)
    end

    # Trigonometric functions
    def sin(angle_degrees)
      radians = angle_degrees * Math::PI / 180
      result = Math.sin(radians)
      log_operation(:sin, [angle_degrees], result)
      format_result(result)
    end

    def cos(angle_degrees)
      radians = angle_degrees * Math::PI / 180
      result = Math.cos(radians)
      log_operation(:cos, [angle_degrees], result)
      format_result(result)
    end

    def tan(angle_degrees)
      radians = angle_degrees * Math::PI / 180
      result = Math.tan(radians)
      log_operation(:tan, [angle_degrees], result)
      format_result(result)
    end

    # Memory operations
    def memory_store(value)
      @memory = to_decimal(value)
      log_operation(:memory_store, [value], @memory)
      @memory
    end

    def memory_recall
      format_result(@memory)
    end

    def memory_clear
      @memory = BigDecimal('0')
      log_operation(:memory_clear, [], @memory)
      format_result(@memory)
    end

    def memory_add(value)
      @memory += to_decimal(value)
      log_operation(:memory_add, [value], @memory)
      format_result(@memory)
    end

    # History and utility methods
    def clear_history
      @history.clear
      "History cleared"
    end

    def last_result
      return nil if @history.empty?
      @history.last[:result]
    end

    def show_history(limit = 10)
      @history.last(limit).map.with_index do |entry, index|
        "#{index + 1}. #{entry[:operation]} #{entry[:operands].join(', ')} = #{entry[:result]}"
      end
    end

    # Class methods for quick calculations
    class << self
      def quick_add(a, b)
        new.add(a, b)
      end

      def quick_multiply(a, b)
        new.multiply(a, b)
      end

      def percentage(value, percent)
        new.multiply(value, percent / 100.0)
      end
    end

    private

    def to_decimal(value)
      case value
      when BigDecimal
        value
      when String
        BigDecimal(value)
      else
        BigDecimal(value.to_s)
      end
    rescue ArgumentError
      raise ArgumentError, "Invalid number format: #{value}"
    end

    def format_result(result)
      if result.is_a?(BigDecimal)
        result.round(@decimal_places).to_f
      else
        result.round(@decimal_places)
      end
    end

    def log_operation(operation, operands, result)
      @history << {
        operation: operation,
        operands: operands,
        result: format_result(result),
        timestamp: Time.now
      }
      
      # Keep only last 100 operations
      @history = @history.last(100) if @history.length > 100
    end
  end

  # Scientific calculator extending basic calculator
  class ScientificCalculator < Calculator
    def initialize(**options)
      super(**options)
      @angle_mode = :degrees  # :degrees or :radians
    end

    attr_accessor :angle_mode

    def factorial(n)
      raise ArgumentError, "Factorial only defined for non-negative integers" unless n.is_a?(Integer) && n >= 0
      
      result = Helpers.factorial(n)
      log_operation(:factorial, [n], result)
      result
    end

    def fibonacci(n)
      raise ArgumentError, "Fibonacci only defined for non-negative integers" unless n.is_a?(Integer) && n >= 0
      
      result = Helpers.fibonacci(n)
      log_operation(:fibonacci, [n], result)
      result
    end

    def combination(n, r)
      raise ArgumentError, "Invalid combination parameters" unless n >= r && r >= 0
      
      result = factorial(n) / (factorial(r) * factorial(n - r))
      log_operation(:combination, [n, r], result)
      result
    end

    def permutation(n, r)
      raise ArgumentError, "Invalid permutation parameters" unless n >= r && r >= 0
      
      result = factorial(n) / factorial(n - r)
      log_operation(:permutation, [n, r], result)
      result
    end

    # Convert angle based on current mode
    def to_radians(angle)
      case @angle_mode
      when :degrees
        angle * Math::PI / 180
      when :radians
        angle
      else
        raise ArgumentError, "Unknown angle mode: #{@angle_mode}"
      end
    end

    # Override trigonometric functions to respect angle mode
    def sin(angle)
      radians = to_radians(angle)
      result = Math.sin(radians)
      log_operation(:sin, [angle], result)
      format_result(result)
    end

    def cos(angle)
      radians = to_radians(angle)
      result = Math.cos(radians)
      log_operation(:cos, [angle], result)
      format_result(result)
    end

    def tan(angle)
      radians = to_radians(angle)
      result = Math.tan(radians)
      log_operation(:tan, [angle], result)
      format_result(result)
    end
  end

  # Rails-style concern for calculation validation
  module CalculationValidation
    extend ActiveSupport::Concern if defined?(ActiveSupport)

    included do
      validate :validate_numeric_inputs, if: :should_validate?
    end

    class_methods do
      def valid_number?(value)
        Float(value.to_s)
        true
      rescue ArgumentError, TypeError
        false
      end
    end

    private

    def validate_numeric_inputs
      return unless @last_inputs

      @last_inputs.each_with_index do |input, index|
        unless self.class.valid_number?(input)
          errors.add(:base, "Input #{index + 1} is not a valid number: #{input}")
        end
      end
    end

    def should_validate?
      defined?(@last_inputs) && @last_inputs.any?
    end
  end
end

# Singleton class for global calculator instance
class GlobalCalculator
  include Singleton
  
  def initialize
    @calculator = MathUtils::Calculator.new
  end

  def method_missing(method, *args, **kwargs)
    if @calculator.respond_to?(method)
      @calculator.send(method, *args, **kwargs)
    else
      super
    end
  end

  def respond_to_missing?(method, include_private = false)
    @calculator.respond_to?(method, include_private) || super
  end

  class << self
    def calculate(&block)
      instance.instance_eval(&block)
    end
  end
end

# Example usage and demonstration
if __FILE__ == $PROGRAM_NAME
  calc = MathUtils::Calculator.new(decimal_places: 3)
  
  puts "Basic operations:"
  puts "5 + 3 = #{calc.add(5, 3)}"
  puts "10 - 4 = #{calc.subtract(10, 4)}"
  puts "6 * 7 = #{calc.multiply(6, 7)}"
  puts "15 / 3 = #{calc.divide(15, 3)}"
  puts "2^8 = #{calc.power(2, 8)}"
  
  puts "\nAdvanced operations:"
  puts "√16 = #{calc.square_root(16)}"
  puts "ln(e) = #{calc.logarithm(Math::E)}"
  puts "sin(90°) = #{calc.sin(90)}"
  
  puts "\nHistory:"
  calc.show_history.each { |entry| puts entry }
  
  # Scientific calculator
  sci_calc = MathUtils::ScientificCalculator.new
  sci_calc.angle_mode = :radians
  
  puts "\nScientific operations:"
  puts "5! = #{sci_calc.factorial(5)}"
  puts "fib(10) = #{sci_calc.fibonacci(10)}"
  puts "C(5,2) = #{sci_calc.combination(5, 2)}"
  
  # Global calculator usage
  result = GlobalCalculator.calculate do
    add(multiply(2, 3), divide(10, 2))
  end
  puts "\nGlobal calculator result: #{result}"
end