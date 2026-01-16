# Technical Writing Guide

## Overview

Technical writing communicates complex information clearly and effectively. Good technical writing helps readers understand and use technical content efficiently.

## Principles of Technical Writing

### Clarity
- Use simple, direct language
- Avoid jargon when possible
- Define technical terms
- Use active voice
- Be specific

### Conciseness
- Get to the point quickly
- Remove unnecessary words
- Use lists for multiple items
- Eliminate redundancy
- Be brief but complete

### Accuracy
- Verify all facts
- Test all examples
- Keep content current
- Cite sources when appropriate
- Correct errors promptly

### Completeness
- Cover all important aspects
- Provide context
- Include examples
- Explain "why" not just "what"
- Address common questions

## Writing Style

### Voice and Tone
- **Active Voice**: "The system processes data" (preferred)
- **Passive Voice**: "Data is processed by the system" (use sparingly)
- **Consistent Tone**: Professional but approachable
- **Reader-Focused**: Consider your audience

### Language Guidelines

**Do:**
- Use simple words
- Write short sentences
- Use present tense
- Be specific
- Use examples

**Don't:**
- Use unnecessary jargon
- Write long, complex sentences
- Use future tense unnecessarily
- Be vague
- Assume prior knowledge

## Document Structure

### Standard Sections

1. **Title**: Clear, descriptive title
2. **Overview**: What and why
3. **Prerequisites**: What's needed
4. **Main Content**: Detailed information
5. **Examples**: Practical examples
6. **Summary**: Key points
7. **References**: Related resources

### Headings

- Use descriptive headings
- Follow consistent hierarchy (H1, H2, H3)
- Use parallel structure
- Keep headings concise

### Lists

**Unordered Lists:**
- Use for items without order
- Parallel structure
- Consistent punctuation
- Keep items concise

**Ordered Lists:**
- Use for step-by-step procedures
- Number sequentially
- One action per item
- Clear progression

## Code Examples

### Formatting
- Use syntax highlighting
- Include relevant context
- Show complete examples
- Explain what code does
- Comment complex logic

### Good Example
```python
# Calculate total price including tax
def calculate_total(items, tax_rate=0.1):
    """Calculate total with tax.
    
    Args:
        items: List of items with 'price' attribute
        tax_rate: Tax rate as decimal (default: 0.1)
        
    Returns:
        Total price including tax
    """
    subtotal = sum(item['price'] for item in items)
    tax = subtotal * tax_rate
    return subtotal + tax

# Example usage
items = [{'price': 10}, {'price': 20}]
total = calculate_total(items, 0.1)  # Returns 33.0
```

### Bad Example
```python
def calc(items, tr=0.1):
    return sum(i['price'] for i in items) * (1 + tr)
```

## Common Writing Patterns

### How-To Guides
1. Title: "How to [Action]"
2. Prerequisites
3. Step-by-step instructions
4. Verification steps
5. Troubleshooting

### Reference Documentation
1. Quick reference table
2. Detailed descriptions
3. Parameter documentation
4. Return values
5. Examples

### Tutorials
1. Learning objectives
2. Prerequisites
3. Step-by-step with explanations
4. Practice exercises
5. Next steps

## Editing and Review

### Self-Review Checklist
- [ ] Is the purpose clear?
- [ ] Are all terms defined?
- [ ] Do examples work?
- [ ] Is structure logical?
- [ ] Are there typos?
- [ ] Is formatting consistent?

### Peer Review
- Technical accuracy
- Clarity and readability
- Completeness
- Examples work
- Structure makes sense

## Tools

### Writing Tools
- **Markdown**: Lightweight markup
- **AsciiDoc**: Rich text format
- **LaTeX**: Scientific documentation
- **Word Processors**: Rich formatting

### Editing Tools
- **Grammar Checkers**: Grammarly, LanguageTool
- **Style Guides**: Google Style Guide, Microsoft Manual
- **Spell Checkers**: Built-in or external

## Best Practices

1. **Know Your Audience**: Write for your readers
2. **Start with Outline**: Plan before writing
3. **Use Examples**: Show, don't just tell
4. **Keep It Simple**: Avoid unnecessary complexity
5. **Review and Revise**: Edit for clarity
6. **Get Feedback**: Peer review helps
7. **Keep Learning**: Improve writing skills
