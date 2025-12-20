"""Simple calculator with intentional issues for demo."""

def add(a, b):
    """Add two numbers."""
    return a + b

def divide(a, b):
    """Divide two numbers."""
    return a / b  # Bug: No zero check

def calculate_total(items):
    """Calculate total price."""
    total = 0
    for item in items:
        total += item["price"]  # Bug: No error handling
    return total

def process_data(data):
    """Process user data."""
    # Security issue: No input validation
    result = eval(data)  # Dangerous!
    return result
