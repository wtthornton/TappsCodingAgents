# Keyboard Navigation Patterns

## Overview

Keyboard navigation is essential for accessibility. Many users rely on keyboards for navigation, including users with motor disabilities, users who cannot use a mouse, and power users who prefer keyboard shortcuts.

## Keyboard Navigation Basics

### Tab Order
- Elements receive focus in DOM order
- Use `tabindex` to modify order
- `tabindex="0"`: Natural tab order
- `tabindex="-1"`: Programmatic focus only
- `tabindex="1+"`: Avoid (creates accessibility issues)

### Focusable Elements
- Links (`<a>`)
- Buttons (`<button>`)
- Form controls (`<input>`, `<select>`, `<textarea>`)
- Elements with `tabindex="0"` or positive
- Elements with `contenteditable="true"`

### Focus Indicators
- Visible focus outline
- High contrast
- Sufficient size
- Clear indication

## Keyboard Shortcuts

### Standard Navigation
- **Tab**: Move forward
- **Shift+Tab**: Move backward
- **Enter/Space**: Activate
- **Escape**: Cancel/Close
- **Arrow Keys**: Navigate within components

### Browser Shortcuts
- **Alt+Left/Right**: Back/Forward
- **Ctrl+F**: Find
- **F5**: Refresh
- **Ctrl+W**: Close tab

## Common Patterns

### Skip Links
```html
<a href="#main-content" class="skip-link">Skip to main content</a>
<main id="main-content">...</main>
```

### Modal Dialogs
- Trap focus within dialog
- Return focus on close
- Close on Escape
- First focusable element receives focus

### Dropdown Menus
- Open on Enter/Space
- Navigate with Arrow keys
- Close on Escape
- Select with Enter

### Tabs
- Navigate tabs with Arrow keys
- Activate with Enter/Space
- Focus tabpanel content
- Maintain focus state

### Accordions
- Toggle with Enter/Space
- Navigate with Arrow keys
- Expand/collapse content
- Maintain focus

## Focus Management

### Setting Focus
```javascript
element.focus();
```

### Trapping Focus
- Keep focus within component
- Prevent focus from escaping
- Return focus on close
- Handle Escape key

### Returning Focus
- Remember previous focus
- Return focus after closing
- Handle navigation
- Maintain context

## ARIA for Keyboard Navigation

### aria-activedescendant
- Indicates active descendant
- Used for listboxes, comboboxes
- Maintains focus on container
- Updates active item

### aria-controls
- Indicates controlled element
- Links trigger to target
- Maintains relationship
- Helps navigation

### aria-expanded
- Indicates expandable state
- Updates on toggle
- Helps screen readers
- Indicates state

### aria-selected
- Indicates selection state
- Used for lists, tabs
- Updates on selection
- Helps navigation

## Keyboard Navigation Patterns

### Button Pattern
```html
<button onclick="handleClick()">Click me</button>
```
- Focusable by default
- Activates on Enter/Space
- Visible focus indicator

### Link Pattern
```html
<a href="/page">Link text</a>
```
- Focusable by default
- Activates on Enter
- Visible focus indicator

### Custom Button Pattern
```html
<div role="button" tabindex="0" 
     onkeydown="handleKeyDown(event)">
  Custom Button
</div>
```
- Handle Enter and Space
- Provide focus indicator
- Update aria-pressed if toggle

### Menu Pattern
```html
<nav role="menubar">
  <button role="menuitem" aria-haspopup="true">File</button>
</nav>
```
- Arrow keys navigate
- Enter/Space activate
- Escape closes
- Focus management

### Tab Pattern
```html
<div role="tablist">
  <button role="tab" aria-selected="true">Tab 1</button>
  <button role="tab" aria-selected="false">Tab 2</button>
</div>
```
- Arrow keys navigate tabs
- Enter/Space activate
- Focus tabpanel content
- Maintain selection

## Common Issues

### Keyboard Traps
- Focus trapped in component
- Cannot escape with Tab
- No way to close
- Missing Escape handler

### Missing Focus Indicators
- No visible focus
- Low contrast focus
- Too small focus indicator
- Hidden focus

### Incorrect Tab Order
- Logical order not followed
- Important elements skipped
- Hidden elements focusable
- Poor tab sequence

### Non-Focusable Interactive Elements
- Divs acting as buttons
- Spans acting as links
- Missing tabindex
- Not keyboard accessible

### Missing Keyboard Handlers
- No Enter/Space handlers
- No Arrow key navigation
- No Escape handler
- Incomplete keyboard support

## Best Practices

### 1. Logical Tab Order
- Follow visual order
- Use tabindex sparingly
- Avoid positive tabindex
- Test tab sequence

### 2. Visible Focus Indicators
- High contrast outline
- Sufficient size
- Clear indication
- Consistent styling

### 3. Complete Keyboard Support
- All mouse actions work with keyboard
- Provide keyboard shortcuts
- Handle all necessary keys
- Test thoroughly

### 4. Focus Management
- Set focus appropriately
- Trap focus when needed
- Return focus on close
- Maintain context

### 5. Skip Links
- Provide skip to main content
- Provide skip to navigation
- Make skip links visible on focus
- Test skip links

## Testing Keyboard Navigation

### Testing Checklist
- [ ] All interactive elements focusable
- [ ] Logical tab order
- [ ] Visible focus indicators
- [ ] All functions work with keyboard
- [ ] No keyboard traps
- [ ] Escape closes modals
- [ ] Arrow keys navigate components
- [ ] Enter/Space activate elements
- [ ] Skip links work
- [ ] Focus management correct

### Testing Tools
- **Keyboard only**: Unplug mouse
- **Browser DevTools**: Focus indicators
- **Accessibility tree**: Check focusable elements
- **Screen readers**: Test with screen readers

## Keyboard Shortcut Guidelines

### Provide Keyboard Shortcuts
- Common actions
- Power user features
- Document shortcuts
- Allow customization

### Avoid Conflicts
- Don't override browser shortcuts
- Don't override OS shortcuts
- Use modifier keys
- Provide alternatives

### Make Discoverable
- Show in tooltips
- Provide help menu
- Document in help
- Show on hover

## Implementation Examples

### Modal Dialog
```javascript
function openDialog() {
  dialog.showModal();
  const firstFocusable = dialog.querySelector('button');
  firstFocusable.focus();
  
  // Trap focus
  dialog.addEventListener('keydown', trapFocus);
}

function closeDialog() {
  const previousFocus = document.activeElement;
  dialog.close();
  previousFocus.focus();
}
```

### Dropdown Menu
```javascript
function handleKeyDown(event) {
  switch(event.key) {
    case 'ArrowDown':
      event.preventDefault();
      focusNext();
      break;
    case 'ArrowUp':
      event.preventDefault();
      focusPrevious();
      break;
    case 'Escape':
      closeMenu();
      break;
    case 'Enter':
    case ' ':
      selectItem();
      break;
  }
}
```

## Best Practices Summary

1. **Logical Tab Order**: Follow visual order
2. **Visible Focus**: Clear focus indicators
3. **Complete Support**: All functions keyboard accessible
4. **No Traps**: Avoid keyboard traps
5. **Focus Management**: Set and return focus appropriately
6. **Skip Links**: Provide skip navigation
7. **Keyboard Shortcuts**: Provide useful shortcuts
8. **Testing**: Test keyboard-only navigation
9. **Documentation**: Document keyboard support
10. **User Feedback**: Test with keyboard users

