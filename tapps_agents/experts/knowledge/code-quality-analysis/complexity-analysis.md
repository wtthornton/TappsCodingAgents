# Complexity Analysis

## What is Code Complexity?

Code complexity measures how difficult code is to understand, test, and maintain. High complexity increases the likelihood of bugs and makes code harder to modify.

## Types of Complexity

### Cyclomatic Complexity

Measures the number of linearly independent paths through program code.

**Formula:**
```
M = E - N + 2P
```
Where:
- E = Number of edges (flow graph connections)
- N = Number of nodes (statements)
- P = Number of connected components

**Python Example:**
```python
# Low complexity (M = 2)
def is_even(n):
    return n % 2 == 0

# Medium complexity (M = 4)
def categorize_age(age):
    if age < 13:
        return "child"
    elif age < 20:
        return "teenager"
    elif age < 65:
        return "adult"
    else:
        return "senior"

# High complexity (M = 8+)
def process_user(user, permissions, role, context):
    if user.is_active:
        if permissions.has_access:
            if role == "admin":
                if context.is_secure:
                    # ... many nested conditions
                    return result
```

### Cognitive Complexity

Measures how difficult code is to understand by humans, focusing on readability rather than testability.

**Factors:**
- Nesting levels
- Logical operators (AND, OR)
- Recursion
- Control flow structures

### Time Complexity (Big O)

Measures how algorithm runtime scales with input size.

**Common Complexities:**
- **O(1)**: Constant time (best)
- **O(log n)**: Logarithmic (excellent)
- **O(n)**: Linear (good)
- **O(n log n)**: Linearithmic (acceptable)
- **O(n²)**: Quadratic (poor)
- **O(2ⁿ)**: Exponential (very poor)

### Space Complexity

Measures memory usage relative to input size.

## Reducing Complexity

### Strategy Pattern
Replace complex conditionals with strategy objects.

```python
# Before: High complexity
def calculate_shipping(country, weight, method):
    if country == "US":
        if method == "standard":
            if weight < 1:
                return 5.00
            elif weight < 5:
                return 10.00
            # ... many nested conditions

# After: Lower complexity
class ShippingCalculator:
    def calculate(self, country, weight, method):
        strategy = self._get_strategy(country, method)
        return strategy.calculate(weight)
```

### Extract Methods
Break large functions into smaller ones.

```python
# Before: Complex function
def process_order(order):
    # 50+ lines of code with multiple responsibilities
    pass

# After: Simpler functions
def process_order(order):
    validate_order(order)
    calculate_totals(order)
    apply_discounts(order)
    process_payment(order)
    send_confirmation(order)
```

### Early Returns
Reduce nesting with early exit conditions.

```python
# Before: Nested conditions
def process_user(user):
    if user:
        if user.is_active:
            if user.has_permissions:
                # Main logic here
                return result
    return None

# After: Early returns
def process_user(user):
    if not user or not user.is_active:
        return None
    if not user.has_permissions:
        return None
    # Main logic here
    return result
```

## Complexity Metrics

### Acceptable Thresholds

| Metric | Excellent | Good | Acceptable | Poor |
|--------|-----------|------|------------|------|
| Cyclomatic Complexity | 1-5 | 6-10 | 11-20 | 21+ |
| Cognitive Complexity | 1-5 | 6-10 | 11-15 | 16+ |
| Function Length (LOC) | < 20 | 20-50 | 50-100 | 100+ |
| Nesting Depth | 1-2 | 3 | 4 | 5+ |

### Warning Signs

1. **High Cyclomatic Complexity**: Many conditional paths
2. **Deep Nesting**: 4+ levels of indentation
3. **Long Functions**: 100+ lines
4. **Many Parameters**: 5+ function parameters
5. **God Classes**: 1000+ lines per class

## Tools for Analysis

### Python
- **radon**: Complexity metrics
- **mccabe**: Cyclomatic complexity
- **xenon**: Complexity monitoring

### JavaScript/TypeScript
- **complexity-report**: Code complexity
- **escomplex**: Complexity analysis

### Multi-Language
- **SonarQube**: Comprehensive analysis
- **CodeClimate**: Complexity scoring

## Best Practices

1. **Keep Functions Small**: Single responsibility
2. **Limit Nesting**: Maximum 3-4 levels
3. **Use Early Returns**: Reduce nesting
4. **Extract Methods**: Break down complex logic
5. **Apply Patterns**: Strategy, Command, Factory
6. **Refactor Regularly**: Continuously improve
7. **Set Thresholds**: Enforce in CI/CD
