"""Windows compatibility check and fixes for TappsCodingAgents workflow execution."""
import os
import sys
from pathlib import Path


def check_windows_compatibility():
    """Check and report Windows compatibility issues."""
    issues = []
    fixes = []
    
    # Check 1: Console encoding
    if sys.platform == "win32":
        try:
            # Try to set UTF-8 encoding
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
                fixes.append("✅ Set stdout encoding to UTF-8")
            else:
                issues.append("⚠️ Cannot set stdout encoding (Python < 3.7)")
        except Exception as e:
            issues.append(f"⚠️ Failed to set encoding: {e}")
    
    # Check 2: Environment variables
    if sys.platform == "win32":
        encoding = os.getenv("PYTHONIOENCODING", "not set")
        if encoding != "utf-8":
            fixes.append("💡 Set PYTHONIOENCODING=utf-8 environment variable for better Unicode support")
    
    # Check 3: Path handling
    test_path = Path("test/path/with/unicode/测试")
    try:
        test_path.mkdir(parents=True, exist_ok=True)
        test_path.rmdir()
        fixes.append("✅ Path handling works correctly")
    except Exception as e:
        issues.append(f"⚠️ Path handling issue: {e}")
    
    # Check 4: Unicode print test
    try:
        test_unicode = "🚀 ✅ ❌ █ ░"
        print(test_unicode)
        fixes.append("✅ Unicode characters can be printed")
    except UnicodeEncodeError as e:
        issues.append(f"⚠️ Unicode print failed: {e}")
        fixes.append("💡 Use encoding fix in cursor_chat.py (already applied)")
    
    return issues, fixes


if __name__ == "__main__":
    print("=" * 60)
    print("Windows Compatibility Check")
    print("=" * 60)
    print()
    
    issues, fixes = check_windows_compatibility()
    
    if issues:
        print("Issues Found:")
        for issue in issues:
            print(f"  {issue}")
        print()
    
    if fixes:
        print("Status/Fixes:")
        for fix in fixes:
            print(f"  {fix}")
        print()
    
    if not issues:
        print("✅ All compatibility checks passed!")
    else:
        print("⚠️ Some issues found. See fixes above.")
    
    print()
    print("=" * 60)

