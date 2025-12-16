"""
Simple test file to review with TappsCodingAgents
"""


def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b


if __name__ == "__main__":
    print(greet("World"))
    print(f"Sum: {calculate_sum(5, 3)}")
