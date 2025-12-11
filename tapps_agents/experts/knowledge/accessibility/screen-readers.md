# Screen Reader Compatibility

## Overview

Screen readers are assistive technologies that read aloud content displayed on a computer screen. They are essential for users who are blind or have low vision. Ensuring compatibility with screen readers is critical for web accessibility.

## Popular Screen Readers

### Windows
- **NVDA (NonVisual Desktop Access)**: Free, open-source
- **JAWS (Job Access With Speech)**: Commercial, widely used
- **Narrator**: Built into Windows

### macOS/iOS
- **VoiceOver**: Built into Apple devices
- **Voice Control**: Speech recognition

### Android
- **TalkBack**: Built into Android
- **Select to Speak**: Text-to-speech

### Linux
- **Orca**: Free, open-source
- **Emacspeak**: Emacs-based

## Screen Reader Navigation

### Navigation Modes
- **Browse Mode**: Reading and navigating content
- **Forms Mode**: Interacting with form controls
- **Virtual Cursor**: Navigating web content
- **Application Mode**: Interacting with applications

### Navigation Commands
- **Headings**: Navigate by headings (H, Shift+H)
- **Landmarks**: Navigate by landmarks (D, Shift+D)
- **Links**: Navigate by links (L, Shift+L)
- **Forms**: Navigate by form controls (F, Shift+F)
- **Lists**: Navigate by lists (L, Shift+L)
- **Tables**: Navigate by tables (T, Shift+T)

## Semantic HTML for Screen Readers

### Headings
- Use proper heading hierarchy (h1-h6)
- Don't skip heading levels
- One h1 per page
- Descriptive heading text

### Landmarks
- Use semantic HTML5 elements
- `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>`
- Use ARIA landmarks when needed
- Provide skip links

### Lists
- Use `<ul>` for unordered lists
- Use `<ol>` for ordered lists
- Use `<dl>` for definition lists
- Don't use lists for layout

### Tables
- Use proper table structure
- Include `<caption>` for table titles
- Use `<th>` for headers
- Associate headers with cells

### Forms
- Use proper form labels
- Associate labels with inputs
- Use fieldset and legend for groups
- Provide error messages

## ARIA for Screen Readers

### Roles
- Use appropriate ARIA roles
- Don't override native semantics
- Use landmark roles when needed
- Provide widget roles

### Properties
- Use `aria-label` for accessible names
- Use `aria-labelledby` for complex labels
- Use `aria-describedby` for descriptions
- Use `aria-live` for dynamic content

### States
- Update `aria-expanded` for collapsibles
- Use `aria-selected` for selections
- Use `aria-checked` for checkboxes
- Use `aria-disabled` for disabled elements

## Screen Reader Testing

### Testing Checklist
- [ ] All content is readable
- [ ] Navigation works properly
- [ ] Forms are accessible
- [ ] Interactive elements are announced
- [ ] Dynamic content is announced
- [ ] Error messages are announced
- [ ] Status messages are announced
- [ ] Focus management works
- [ ] Skip links work
- [ ] Tables are navigable

### Testing Tools
- **NVDA**: Free Windows screen reader
- **JAWS**: Commercial Windows screen reader
- **VoiceOver**: Built into macOS/iOS
- **TalkBack**: Built into Android
- **Browser DevTools**: Accessibility tree inspection

## Common Issues

### Missing Labels
- Form controls without labels
- Buttons without accessible names
- Links without descriptive text
- Images without alt text

### Poor Structure
- Missing headings
- Incorrect heading hierarchy
- Missing landmarks
- Poor list structure

### Dynamic Content
- Changes not announced
- Missing live regions
- Incorrect ARIA usage
- Focus not managed

### Forms
- Missing labels
- Unassociated labels
- Missing error messages
- No fieldset/legend

### Tables
- Missing captions
- Unassociated headers
- Complex tables not explained
- Layout tables not marked

## Best Practices

### 1. Use Semantic HTML
- Proper heading hierarchy
- Semantic HTML5 elements
- Proper list structure
- Correct table markup

### 2. Provide Accessible Names
- Labels for all form controls
- Accessible names for buttons
- Descriptive link text
- Alt text for images

### 3. Manage Dynamic Content
- Use ARIA live regions
- Announce status changes
- Update ARIA states
- Manage focus

### 4. Test with Screen Readers
- Test with multiple screen readers
- Test keyboard navigation
- Test with different browsers
- Test on different platforms

### 5. Provide Context
- Clear headings
- Descriptive link text
- Helpful error messages
- Status announcements

## Screen Reader Announcements

### Page Load
- Page title announced
- Main content identified
- Navigation available
- Skip links available

### Navigation
- Current location announced
- Heading levels announced
- Landmarks identified
- Links announced with context

### Forms
- Form labels announced
- Required fields identified
- Error messages announced
- Success messages announced

### Interactive Elements
- Button purpose announced
- Link destination announced
- Checkbox state announced
- Radio button selection announced

### Dynamic Content
- Status messages announced
- Error messages announced
- Loading states announced
- Content changes announced

## Testing Procedures

### Manual Testing
1. Install screen reader
2. Navigate website with keyboard
3. Test all interactive elements
4. Test form completion
5. Test dynamic content
6. Document issues
7. Fix issues
8. Retest

### Automated Testing
- Use accessibility testing tools
- Check for ARIA issues
- Validate HTML structure
- Check for missing labels
- Verify semantic HTML

### User Testing
- Test with actual screen reader users
- Gather feedback
- Identify pain points
- Improve based on feedback

## Common Patterns

### Skip Links
```html
<a href="#main-content" class="skip-link">Skip to main content</a>
<main id="main-content">...</main>
```

### Accessible Buttons
```html
<button aria-label="Close dialog">×</button>
```

### Accessible Forms
```html
<label for="email">Email</label>
<input type="email" id="email" aria-required="true">
<span id="email-error" role="alert" aria-live="assertive"></span>
```

### Accessible Tables
```html
<table>
  <caption>User Data</caption>
  <thead>
    <tr>
      <th scope="col">Name</th>
      <th scope="col">Email</th>
    </tr>
  </thead>
  <tbody>...</tbody>
</table>
```

## Best Practices Summary

1. **Semantic HTML**: Use proper HTML elements
2. **Accessible Names**: Provide labels and names
3. **Structure**: Proper heading hierarchy and landmarks
4. **ARIA**: Use ARIA appropriately
5. **Testing**: Test with multiple screen readers
6. **Dynamic Content**: Announce changes properly
7. **Forms**: Make forms fully accessible
8. **Tables**: Structure tables correctly
9. **Focus Management**: Manage focus properly
10. **User Feedback**: Test with actual users

