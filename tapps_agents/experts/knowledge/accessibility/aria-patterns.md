# ARIA Patterns and Best Practices

## Overview

Accessible Rich Internet Applications (ARIA) is a set of attributes that make web content and applications more accessible to people with disabilities. ARIA provides semantic information about UI components to assistive technologies.

## ARIA Principles

### 1. Use Native HTML When Possible
- Prefer semantic HTML elements
- Use ARIA only when necessary
- Native HTML has built-in accessibility
- ARIA enhances, doesn't replace

### 2. Don't Change Native Semantics
- Don't override native HTML semantics
- Use ARIA to add, not replace
- Maintain native behavior
- Enhance, don't break

### 3. All Interactive Elements Must Be Accessible
- Keyboard accessible
- Screen reader accessible
- Focusable
- Operable

### 4. All Interactive Elements Must Have Accessible Names
- Labels for form controls
- Names for buttons
- Descriptions when needed
- Clear identification

## ARIA Attributes

### Roles
- Define what an element is
- Provide semantic meaning
- Override native semantics when needed
- Use sparingly

### Properties
- Define characteristics
- Provide additional information
- Describe relationships
- Enhance understanding

### States
- Define current condition
- Indicate interactive state
- Update dynamically
- Reflect user actions

## Common ARIA Roles

### Landmark Roles
- `banner`: Site header
- `navigation`: Navigation regions
- `main`: Main content
- `complementary`: Sidebars, asides
- `contentinfo`: Site footer
- `search`: Search regions
- `form`: Form regions

### Widget Roles
- `button`: Button controls
- `checkbox`: Checkbox inputs
- `radio`: Radio button groups
- `textbox`: Text input fields
- `slider`: Range inputs
- `switch`: Toggle switches
- `tab`: Tab controls
- `tabpanel`: Tab panels
- `dialog`: Modal dialogs
- `alert`: Alert messages
- `status`: Status messages

### Composite Roles
- `combobox`: Combination of textbox and listbox
- `grid`: Table-like structures
- `listbox`: List of options
- `menu`: Menu structures
- `menubar`: Menu bars
- `radiogroup`: Radio button groups
- `tablist`: Tab lists
- `tree`: Tree structures

## ARIA Properties

### aria-label
- Provides accessible name
- Overrides visible label
- Use when label not visible
- Keep concise

### aria-labelledby
- References element that labels
- Points to ID of labeling element
- Use when label exists elsewhere
- Maintains relationship

### aria-describedby
- References descriptive text
- Provides additional information
- Points to ID of describing element
- Use for help text, errors

### aria-hidden
- Hides decorative content
- Removes from accessibility tree
- Use for icons, decorative images
- Don't hide interactive content

### aria-live
- Announces dynamic content
- `polite`: Waits for pause
- `assertive`: Interrupts immediately
- `off`: No announcements

### aria-atomic
- Controls what is announced
- `true`: Entire region announced
- `false`: Only changes announced
- Use with aria-live

### aria-relevant
- Controls what changes are announced
- `additions`: New content
- `removals`: Removed content
- `text`: Text changes
- `all`: All changes

### aria-expanded
- Indicates expandable state
- `true`: Expanded
- `false`: Collapsed
- `undefined`: Not expandable

### aria-selected
- Indicates selection state
- `true`: Selected
- `false`: Not selected
- Use for lists, tabs, options

### aria-checked
- Indicates checked state
- `true`: Checked
- `false`: Unchecked
- `mixed`: Partially checked

### aria-disabled
- Indicates disabled state
- `true`: Disabled
- `false`: Enabled
- Prevents interaction

### aria-required
- Indicates required field
- `true`: Required
- `false`: Optional
- Use for form validation

### aria-invalid
- Indicates validation state
- `true`: Invalid
- `false`: Valid
- Use with error messages

### aria-current
- Indicates current item
- `page`: Current page
- `step`: Current step
- `location`: Current location
- `date`: Current date
- `time`: Current time
- `true`: Current item

## ARIA Patterns

### Button Pattern
```html
<button aria-label="Close dialog">×</button>
<button aria-pressed="false">Toggle</button>
```

### Checkbox Pattern
```html
<div role="checkbox" aria-checked="false" tabindex="0">
  <span>Option</span>
</div>
```

### Dialog Pattern
```html
<div role="dialog" aria-labelledby="dialog-title" aria-modal="true">
  <h2 id="dialog-title">Dialog Title</h2>
  <button aria-label="Close">×</button>
</div>
```

### Tab Pattern
```html
<div role="tablist">
  <button role="tab" aria-selected="true" aria-controls="panel-1">Tab 1</button>
  <button role="tab" aria-selected="false" aria-controls="panel-2">Tab 2</button>
</div>
<div role="tabpanel" id="panel-1" aria-labelledby="tab-1">Content 1</div>
<div role="tabpanel" id="panel-2" aria-labelledby="tab-2">Content 2</div>
```

### Menu Pattern
```html
<nav role="menubar">
  <button role="menuitem" aria-haspopup="true" aria-expanded="false">
    File
  </button>
  <ul role="menu">
    <li role="menuitem">New</li>
    <li role="menuitem">Open</li>
  </ul>
</nav>
```

### Alert Pattern
```html
<div role="alert" aria-live="assertive">
  Error: Invalid input
</div>
```

### Status Pattern
```html
<div role="status" aria-live="polite" aria-atomic="true">
  Form submitted successfully
</div>
```

## ARIA Best Practices

### 1. Use Semantic HTML First
- Prefer `<button>` over `<div role="button">`
- Prefer `<nav>` over `<div role="navigation">`
- Use native elements when possible
- Add ARIA only when needed

### 2. Provide Accessible Names
- Use `aria-label` for icon buttons
- Use `aria-labelledby` for complex labels
- Ensure all interactive elements have names
- Test with screen readers

### 3. Manage Focus
- Set focus to new content
- Return focus after closing dialogs
- Manage focus in dynamic content
- Provide skip links

### 4. Announce Changes
- Use `aria-live` for dynamic content
- Use appropriate live region roles
- Update `aria-expanded` for collapsibles
- Announce status changes

### 5. Maintain Relationships
- Use `aria-controls` for relationships
- Use `aria-describedby` for descriptions
- Use `aria-labelledby` for labels
- Maintain logical structure

### 6. Indicate State
- Use `aria-selected` for selections
- Use `aria-checked` for checkboxes
- Use `aria-expanded` for collapsibles
- Use `aria-disabled` for disabled elements

### 7. Provide Context
- Use `aria-describedby` for help text
- Use `aria-invalid` for validation
- Use `aria-required` for required fields
- Provide clear error messages

### 8. Test with Screen Readers
- Test with NVDA (Windows)
- Test with JAWS (Windows)
- Test with VoiceOver (macOS/iOS)
- Test with TalkBack (Android)

## Common ARIA Mistakes

### 1. Overusing ARIA
- Adding ARIA when HTML is sufficient
- Redundant ARIA attributes
- Conflicting with native semantics
- Unnecessary complexity

### 2. Missing Accessible Names
- Buttons without labels
- Links without text
- Form controls without labels
- Icons without descriptions

### 3. Incorrect Role Usage
- Using wrong roles
- Overriding native semantics incorrectly
- Missing required properties
- Incomplete implementations

### 4. Poor State Management
- Not updating states
- Incorrect state values
- Missing state information
- Inconsistent states

### 5. Broken Relationships
- Missing `aria-controls`
- Incorrect `aria-labelledby`
- Broken `aria-describedby`
- Missing relationships

## ARIA Testing Checklist

- [ ] All interactive elements have accessible names
- [ ] ARIA roles used correctly
- [ ] ARIA states updated dynamically
- [ ] Relationships properly defined
- [ ] Live regions announce changes
- [ ] Focus management implemented
- [ ] Tested with screen readers
- [ ] Keyboard navigation works
- [ ] No ARIA conflicts with HTML
- [ ] Semantic HTML preferred over ARIA

## Best Practices Summary

1. **Prefer HTML**: Use semantic HTML first
2. **Add ARIA When Needed**: Enhance, don't replace
3. **Provide Names**: All interactive elements need names
4. **Manage States**: Update ARIA states dynamically
5. **Maintain Relationships**: Use ARIA to show relationships
6. **Announce Changes**: Use live regions appropriately
7. **Test Thoroughly**: Test with multiple screen readers
8. **Keep It Simple**: Don't overuse ARIA
9. **Document Usage**: Document ARIA implementations
10. **Stay Updated**: Follow ARIA specification updates

