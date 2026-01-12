"""
Test file with a bug for bug-fix-agent demonstration.
"""

def calculate_average(numbers):
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0
    
    # BUG: Missing sum calculation - this will cause a NameError
    total = sum(numbers)
    average = total / len(numbers)
    return average


def process_data(data_list):
    """Process a list of data items."""
    results = []
    for item in data_list:
        # BUG: KeyError - accessing 'value' key that may not exist
        value = item['value']
        results.append(value * 2)
    return results


if __name__ == "__main__":
    # Test the buggy function
    numbers = [1, 2, 3, 4, 5]
    avg = calculate_average(numbers)
    print(f"Average: {avg}")
