"""
Simple test file with a bug for bug-fix-agent demonstration.
This file has a KeyError bug that will fail when accessing a dictionary key that doesn't exist.
"""

def get_user_email(user_data):
    """Get user email from user data dictionary."""
    # BUG: KeyError - accessing 'email' key that may not exist
    # Should use .get() with default value instead
    return user_data['email']


def main():
    """Test the buggy function."""
    user1 = {'email': 'test@example.com', 'name': 'Test User'}
    user2 = {'name': 'Another User'}  # Missing 'email' key - will cause KeyError
    
    print(f"User 1 email: {get_user_email(user1)}")
    print(f"User 2 email: {get_user_email(user2)}")  # This will fail with KeyError


if __name__ == "__main__":
    main()
