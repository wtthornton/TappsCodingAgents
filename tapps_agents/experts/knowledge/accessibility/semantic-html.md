# Semantic HTML Patterns

## Overview

Semantic HTML uses HTML elements to convey meaning and structure, making content more accessible to assistive technologies and improving SEO. Semantic HTML is the foundation of web accessibility.

## Benefits of Semantic HTML

### Accessibility
- Screen readers understand structure
- Navigation by landmarks
- Proper heading hierarchy
- Clear content relationships

### SEO
- Search engines understand content
- Better content indexing
- Improved rankings
- Rich snippets

### Maintainability
- Clear code structure
- Easier to understand
- Better organization
- Reduced complexity

## HTML5 Semantic Elements

### Document Structure
- `<header>`: Site or section header
- `<nav>`: Navigation regions
- `<main>`: Main content area
- `<article>`: Independent content
- `<section>`: Thematic grouping
- `<aside>`: Complementary content
- `<footer>`: Site or section footer

### Text Content
- `<h1>` through `<h6>`: Headings
- `<p>`: Paragraphs
- `<blockquote>`: Quotations
- `<pre>`: Preformatted text
- `<code>`: Code snippets
- `<em>`: Emphasis
- `<strong>`: Strong importance
- `<mark>`: Highlighted text
- `<time>`: Dates and times

### Lists
- `<ul>`: Unordered lists
- `<ol>`: Ordered lists
- `<li>`: List items
- `<dl>`: Description lists
- `<dt>`: Description terms
- `<dd>`: Description details

### Forms
- `<form>`: Form container
- `<fieldset>`: Form group
- `<legend>`: Fieldset label
- `<label>`: Form labels
- `<input>`: Input controls
- `<select>`: Dropdown lists
- `<textarea>`: Multi-line text
- `<button>`: Buttons

### Tables
- `<table>`: Table container
- `<caption>`: Table title
- `<thead>`: Header row group
- `<tbody>`: Body row group
- `<tfoot>`: Footer row group
- `<tr>`: Table rows
- `<th>`: Header cells
- `<td>`: Data cells

### Media
- `<img>`: Images (with alt text)
- `<picture>`: Responsive images
- `<video>`: Video content
- `<audio>`: Audio content
- `<figure>`: Media container
- `<figcaption>`: Media caption

## Heading Hierarchy

### Proper Structure
```html
<h1>Page Title</h1>
  <h2>Section Title</h2>
    <h3>Subsection Title</h3>
      <h4>Sub-subsection Title</h4>
  <h2>Another Section</h2>
```

### Rules
- One `<h1>` per page
- Don't skip heading levels
- Use headings for structure, not style
- Maintain logical hierarchy

## Landmark Elements

### Header
```html
<header>
  <h1>Site Title</h1>
  <nav>...</nav>
</header>
```

### Navigation
```html
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/about">About</a></li>
  </ul>
</nav>
```

### Main Content
```html
<main>
  <article>
    <h1>Article Title</h1>
    <p>Content...</p>
  </article>
</main>
```

### Aside
```html
<aside aria-label="Related articles">
  <h2>Related</h2>
  <ul>...</ul>
</aside>
```

### Footer
```html
<footer>
  <p>Copyright © 2025</p>
  <nav aria-label="Footer navigation">...</nav>
</footer>
```

## Form Semantics

### Proper Labels
```html
<label for="email">Email Address</label>
<input type="email" id="email" name="email" required>
```

### Fieldset Groups
```html
<fieldset>
  <legend>Contact Information</legend>
  <label for="name">Name</label>
  <input type="text" id="name" name="name">
  <label for="email">Email</label>
  <input type="email" id="email" name="email">
</fieldset>
```

### Error Messages
```html
<label for="email">Email</label>
<input type="email" id="email" aria-invalid="true" aria-describedby="email-error">
<span id="email-error" role="alert">Invalid email address</span>
```

## Table Semantics

### Proper Structure
```html
<table>
  <caption>User Data</caption>
  <thead>
    <tr>
      <th scope="col">Name</th>
      <th scope="col">Email</th>
      <th scope="col">Role</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">John Doe</th>
      <td>john@example.com</td>
      <td>Admin</td>
    </tr>
  </tbody>
</table>
```

### Scope Attributes
- `scope="col"`: Column header
- `scope="row"`: Row header
- `scope="colgroup"`: Column group
- `scope="rowgroup"`: Row group

## List Semantics

### Unordered Lists
```html
<ul>
  <li>Item 1</li>
  <li>Item 2</li>
  <li>Item 3</li>
</ul>
```

### Ordered Lists
```html
<ol>
  <li>First step</li>
  <li>Second step</li>
  <li>Third step</li>
</ol>
```

### Description Lists
```html
<dl>
  <dt>Term 1</dt>
  <dd>Definition 1</dd>
  <dt>Term 2</dt>
  <dd>Definition 2</dd>
</dl>
```

## Common Mistakes

### Using Divs for Everything
```html
<!-- Bad -->
<div class="header">...</div>
<div class="nav">...</div>
<div class="main">...</div>

<!-- Good -->
<header>...</header>
<nav>...</nav>
<main>...</main>
```

### Incorrect Heading Usage
```html
<!-- Bad -->
<h1>Title</h1>
<h3>Subtitle</h3> <!-- Skipped h2 -->

<!-- Good -->
<h1>Title</h1>
<h2>Subtitle</h2>
```

### Styling with Headings
```html
<!-- Bad -->
<h4 style="font-size: 18px;">Not a heading</h4>

<!-- Good -->
<p class="large-text">Not a heading</p>
```

### Missing Labels
```html
<!-- Bad -->
<input type="text" name="email">

<!-- Good -->
<label for="email">Email</label>
<input type="text" id="email" name="email">
```

## Best Practices

### 1. Use Semantic Elements
- Prefer semantic HTML5 elements
- Use appropriate elements for content
- Avoid generic divs and spans
- Convey meaning through HTML

### 2. Maintain Structure
- Proper heading hierarchy
- Logical content flow
- Clear relationships
- Consistent structure

### 3. Provide Context
- Use landmarks
- Provide labels
- Use captions
- Add descriptions

### 4. Test with Assistive Technologies
- Test with screen readers
- Test keyboard navigation
- Verify structure
- Check landmarks

### 5. Validate HTML
- Use HTML validator
- Fix validation errors
- Ensure proper nesting
- Use valid attributes

## Accessibility Benefits

### Screen Reader Navigation
- Navigate by headings
- Navigate by landmarks
- Understand structure
- Access content efficiently

### Keyboard Navigation
- Logical tab order
- Skip links work
- Focus management
- Proper structure

### SEO Benefits
- Better indexing
- Rich snippets
- Improved rankings
- Clear content structure

## Implementation Checklist

- [ ] Use semantic HTML5 elements
- [ ] Proper heading hierarchy
- [ ] One h1 per page
- [ ] Use landmarks appropriately
- [ ] Proper form labels
- [ ] Proper table structure
- [ ] Use lists for lists
- [ ] Provide alt text for images
- [ ] Use proper button/link elements
- [ ] Validate HTML

## Best Practices Summary

1. **Use Semantic Elements**: Prefer HTML5 semantic elements
2. **Maintain Hierarchy**: Proper heading structure
3. **Provide Context**: Labels, captions, descriptions
4. **Test Accessibility**: Test with assistive technologies
5. **Validate HTML**: Ensure valid markup
6. **Avoid Generic Elements**: Use specific elements
7. **Structure Content**: Logical content organization
8. **Document Structure**: Clear code organization
9. **Consider SEO**: Semantic HTML helps SEO
10. **Continuous Improvement**: Regular audits

