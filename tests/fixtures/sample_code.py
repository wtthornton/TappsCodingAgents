"""
Sample code files for testing code scoring and review functionality.
"""

# Simple, clean code (should score high)
SIMPLE_CODE = '''def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y
'''

# Complex code with high cyclomatic complexity (should score lower)
COMPLEX_CODE = '''def process_data(data: list, filters: dict, options: dict) -> list:
    """Process data with complex logic."""
    result = []
    for item in data:
        if item.get("active"):
            if filters.get("type") == "a":
                if options.get("include_metadata"):
                    if item.get("metadata"):
                        for key, value in item["metadata"].items():
                            if value:
                                if isinstance(value, dict):
                                    result.append({**item, "processed": True})
                                else:
                                    result.append({**item, key: value})
    return result
'''

# Code with security issues (should score low on security)
INSECURE_CODE = '''def process_user_input(user_input: str):
    """Process user input unsafely."""
    # Security issue: eval() with user input
    result = eval(user_input)
    
    # Security issue: exec() with user input
    exec(f"print({user_input})")
    
    # Security issue: pickle with untrusted data
    import pickle
    data = pickle.loads(user_input)
    
    return result

def subprocess_command(command: str):
    """Run system command unsafely."""
    import subprocess
    import os
    
    # Security issue: shell injection
    os.system(command)
    subprocess.call(command, shell=True)
    
    return True
'''

# Well-documented, maintainable code (should score high)
MAINTAINABLE_CODE = '''"""
Math utilities module.

This module provides basic mathematical operations with proper error handling.
"""

from typing import Union


def safe_divide(numerator: float, denominator: float) -> Union[float, None]:
    """
    Safely divide two numbers.
    
    Args:
        numerator: The number to divide
        denominator: The number to divide by
        
    Returns:
        The result of division, or None if denominator is zero
        
    Raises:
        TypeError: If inputs are not numeric
    """
    if not isinstance(numerator, (int, float)):
        raise TypeError(f"numerator must be numeric, got {type(numerator)}")
    if not isinstance(denominator, (int, float)):
        raise TypeError(f"denominator must be numeric, got {type(denominator)}")
    
    if denominator == 0:
        return None
    
    return numerator / denominator


def calculate_average(numbers: list[float]) -> float:
    """
    Calculate the average of a list of numbers.
    
    Args:
        numbers: List of numbers to average
        
    Returns:
        The average value
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    
    return sum(numbers) / len(numbers)
'''

# Code with syntax error (should handle gracefully)
SYNTAX_ERROR_CODE = """def broken_function(
    return True  # Missing closing parenthesis
"""
