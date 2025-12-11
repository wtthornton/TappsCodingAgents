# Accessible Form Design

## Overview

Forms are critical for user interaction. Making forms accessible ensures that all users, including those using assistive technologies, can successfully complete and submit forms.

## Form Structure

### Form Element
```html
<form action="/submit" method="post" novalidate>
  <!-- Form fields -->
</form>
```

### Fieldset and Legend
```html
<fieldset>
  <legend>Contact Information</legend>
  <!-- Related fields -->
</fieldset>
```

## Labels

### Explicit Labels
```html
<label for="email">Email Address</label>
<input type="email" id="email" name="email">
```

### Implicit Labels
```html
<label>
  Email Address
  <input type="email" name="email">
</label>
```

### Best Practices
- Always provide labels
- Associate labels with inputs
- Use clear, descriptive labels
- Place labels before inputs

## Input Types

### Text Inputs
```html
<label for="name">Full Name</label>
<input type="text" id="name" name="name" required>
```

### Email Inputs
```html
<label for="email">Email Address</label>
<input type="email" id="email" name="email" required>
```

### Number Inputs
```html
<label for="age">Age</label>
<input type="number" id="age" name="age" min="0" max="120">
```

### Date Inputs
```html
<label for="birthdate">Birth Date</label>
<input type="date" id="birthdate" name="birthdate">
```

### Checkboxes
```html
<label>
  <input type="checkbox" name="newsletter" value="yes">
  Subscribe to newsletter
</label>
```

### Radio Buttons
```html
<fieldset>
  <legend>Preferred Contact Method</legend>
  <label>
    <input type="radio" name="contact" value="email" checked>
    Email
  </label>
  <label>
    <input type="radio" name="contact" value="phone">
    Phone
  </label>
</fieldset>
```

### Select Dropdowns
```html
<label for="country">Country</label>
<select id="country" name="country">
  <option value="">Select a country</option>
  <option value="us">United States</option>
  <option value="ca">Canada</option>
</select>
```

### Textareas
```html
<label for="message">Message</label>
<textarea id="message" name="message" rows="5" cols="50"></textarea>
```

## Required Fields

### HTML5 Required
```html
<label for="email">Email Address *</label>
<input type="email" id="email" name="email" required aria-required="true">
```

### Visual Indicators
- Asterisk (*) for required fields
- "Required" text
- Different styling
- Clear indication

### ARIA Required
```html
<input type="email" id="email" aria-required="true">
```

## Error Messages

### Inline Errors
```html
<label for="email">Email Address</label>
<input type="email" id="email" aria-invalid="true" aria-describedby="email-error">
<span id="email-error" role="alert">Please enter a valid email address</span>
```

### Error Summary
```html
<div role="alert" aria-labelledby="error-summary">
  <h2 id="error-summary">Please correct the following errors:</h2>
  <ul>
    <li><a href="#email">Email is required</a></li>
    <li><a href="#name">Name is required</a></li>
  </ul>
</div>
```

### Best Practices
- Provide clear error messages
- Associate errors with fields
- Use aria-invalid
- Use aria-describedby
- Announce errors to screen readers

## Help Text

### Descriptions
```html
<label for="password">Password</label>
<input type="password" id="password" aria-describedby="password-help">
<span id="password-help">Must be at least 8 characters</span>
```

### Instructions
```html
<label for="username">Username</label>
<input type="text" id="username" aria-describedby="username-help">
<span id="username-help">Letters and numbers only, 3-20 characters</span>
```

## Validation

### HTML5 Validation
```html
<input type="email" id="email" required pattern="[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$">
```

### ARIA Validation
```html
<input type="email" id="email" 
       aria-invalid="true" 
       aria-describedby="email-error">
<span id="email-error" role="alert">Invalid email format</span>
```

### Real-time Validation
- Validate on blur
- Provide immediate feedback
- Don't validate on every keystroke
- Clear errors when fixed

## Grouping Related Fields

### Fieldset
```html
<fieldset>
  <legend>Billing Address</legend>
  <label for="street">Street</label>
  <input type="text" id="street" name="street">
  <!-- More fields -->
</fieldset>
```

### ARIA Groups
```html
<div role="group" aria-labelledby="billing-label">
  <h3 id="billing-label">Billing Address</h3>
  <!-- Fields -->
</div>
```

## Autocomplete

### HTML5 Autocomplete
```html
<label for="email">Email</label>
<input type="email" id="email" autocomplete="email">

<label for="name">Full Name</label>
<input type="text" id="name" autocomplete="name">

<label for="phone">Phone</label>
<input type="tel" id="phone" autocomplete="tel">
```

### Benefits
- Helps users with cognitive disabilities
- Faster form completion
- Reduces errors
- Improves user experience

## Keyboard Navigation

### Tab Order
- Logical tab sequence
- Follow visual order
- All fields focusable
- No keyboard traps

### Focus Management
- Set focus to first error
- Return focus after submission
- Maintain focus context
- Visible focus indicators

## Common Issues

### Missing Labels
- Form controls without labels
- Placeholder text as label
- Visual labels only
- Not associated with inputs

### Poor Error Handling
- Errors not announced
- Unclear error messages
- Errors not associated with fields
- No error summary

### Inaccessible Validation
- Validation not announced
- No clear error messages
- Errors not associated with fields
- Poor error recovery

### Missing Required Indicators
- No indication of required fields
- Unclear which fields are required
- Inconsistent indicators
- Not programmatically indicated

## Best Practices

### 1. Always Provide Labels
- Every form control needs a label
- Associate labels with inputs
- Use clear, descriptive labels
- Place labels appropriately

### 2. Group Related Fields
- Use fieldset and legend
- Logical grouping
- Clear organization
- Better understanding

### 3. Provide Help Text
- Instructions when needed
- Format requirements
- Examples
- Associate with aria-describedby

### 4. Handle Errors Properly
- Clear error messages
- Associate with fields
- Announce to screen readers
- Provide error summary

### 5. Support Keyboard Navigation
- Logical tab order
- All fields keyboard accessible
- Visible focus indicators
- No keyboard traps

## Testing Checklist

- [ ] All form controls have labels
- [ ] Labels are associated with inputs
- [ ] Required fields are indicated
- [ ] Error messages are clear
- [ ] Errors are associated with fields
- [ ] Errors are announced to screen readers
- [ ] Help text is provided when needed
- [ ] Forms are keyboard navigable
- [ ] Focus indicators are visible
- [ ] Forms work with screen readers

## Best Practices Summary

1. **Labels**: Always provide and associate labels
2. **Grouping**: Use fieldset for related fields
3. **Required Fields**: Clearly indicate required fields
4. **Error Handling**: Provide clear, associated errors
5. **Help Text**: Provide instructions when needed
6. **Keyboard Navigation**: Ensure full keyboard access
7. **Validation**: Provide accessible validation
8. **Autocomplete**: Use autocomplete attributes
9. **Testing**: Test with assistive technologies
10. **User Feedback**: Gather feedback from users

