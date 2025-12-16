"""
Example file with a bug for testing the quick-fix workflow
"""


def calculate_total(items):
    """Calculate total price of items."""
    total = 0
    for item in items:
        total += item["price"]  # Bug: doesn't handle missing 'price' key
    return total


def process_user_data(user_data):
    """Process user data and return formatted result."""
    # Bug: No validation - will crash if user_data is None
    name = user_data["name"]
    email = user_data["email"]
    return f"{name} <{email}>"


if __name__ == "__main__":
    # Test cases that will fail
    items = [{"price": 10}, {"price": 20}, {}]  # Missing price in last item
    print(calculate_total(items))

    user = None  # Will cause error
    print(process_user_data(user))
