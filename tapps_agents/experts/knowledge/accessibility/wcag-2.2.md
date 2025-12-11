# WCAG 2.2 Guidelines

## Overview

Web Content Accessibility Guidelines (WCAG) 2.2 extends WCAG 2.1 with additional success criteria focused on improving accessibility for users with cognitive and learning disabilities, users with low vision, and users with disabilities on mobile devices.

## New Success Criteria in WCAG 2.2

### 2.4.11 Focus Not Obscured (Minimum) (Level AA)
- When a keyboard interface component receives focus, the component is not entirely hidden due to author-created content
- At least a portion of the component is visible
- Prevents focus from being hidden by overlays, modals, or sticky headers

### 2.4.12 Focus Not Obscured (Enhanced) (Level AAA)
- When a keyboard interface component receives focus, nothing in the viewport obscures it
- Complete visibility of focused component
- Higher standard than Level AA

### 2.4.13 Focus Appearance (Minimum) (Level AA)
- When the keyboard focus indicator is visible, an area of the focus indicator meets all the following:
  - Is at least as large as the area of a 2 CSS pixel thick perimeter of the unfocused component or sub-component
  - Has a contrast ratio of at least 3:1 between the same pixels in the focused and unfocused states
  - Has a contrast ratio of at least 3:1 against adjacent colors

### 2.4.14 Focus Appearance (Enhanced) (Level AAA)
- When the keyboard focus indicator is visible, an area of the focus indicator meets all the following:
  - Is at least as large as the area of a 2 CSS pixel thick perimeter of the unfocused component or sub-component
  - Has a contrast ratio of at least 4.5:1 between the same pixels in the focused and unfocused states
  - Has a contrast ratio of at least 4.5:1 against adjacent colors

### 2.5.7 Dragging Movements (Level AA)
- All functionality that uses a dragging movement operates in at least one of the following modes:
  - Pointer cancellation: No down-event, or abort/undo mechanism, or up reversal, or essential
  - Single pointer: Alternative single pointer without dragging
  - Keyboard: Keyboard interface available

### 2.5.8 Target Size (Minimum) (Level AA)
- Target size for pointer inputs is at least 24 by 24 CSS pixels
- Exceptions: Equivalent target, inline, essential, user agent control, not modified by author

### 3.2.6 Consistent Help (Level A)
- If a Web page contains any of the following help mechanisms, and those mechanisms are repeated on multiple Web pages within a set of Web pages, they occur in the same relative order on each page:
  - Human contact details
  - Human contact mechanism
  - Self-help option
  - A fully automated contact mechanism

### 3.3.7 Redundant Entry (Level A)
- Information previously entered by or provided to the user that is required to be entered again in the same process is either:
  - Auto-populated, or
  - Available for the user to select
- Exceptions: When re-entering the information is essential, when information is required to ensure the security of the content, or when previously entered information is no longer valid

### 3.3.8 Accessible Authentication (Minimum) (Level AA)
- A cognitive function test (such as remembering a password or solving a puzzle) is not required for any step in an authentication process unless that step provides at least one of the following:
  - Mechanism to assist the user in completing the cognitive function test
  - Alternative authentication method that does not rely on a cognitive function test
  - Mechanism is available to bypass the cognitive function test

### 3.3.9 Accessible Authentication (Enhanced) (Level AAA)
- A cognitive function test is not required for any step in an authentication process unless that step provides at least one of the following:
  - Mechanism to assist the user in completing the cognitive function test
  - Alternative authentication method that does not rely on a cognitive function test
  - Mechanism is available to bypass the cognitive function test
- No exception for object recognition

### 4.1.3 Status Messages (Level AA)
- In content implemented using markup languages, status messages can be programmatically determined through role or properties such that they can be presented to the user by assistive technologies without receiving focus
- Status messages must be announced by screen readers

## Key Improvements in WCAG 2.2

### Focus Management
- Better focus visibility requirements
- Focus not obscured by overlays
- Enhanced focus appearance standards
- Improved keyboard navigation

### Mobile Accessibility
- Target size requirements
- Dragging movements alternatives
- Touch target accessibility
- Mobile interaction patterns

### Cognitive Accessibility
- Consistent help placement
- Redundant entry prevention
- Accessible authentication
- Reduced cognitive load

### Status Messages
- Programmatic status announcements
- Screen reader compatibility
- Live region usage
- Status message roles

## Implementation Guidelines

### Focus Appearance
- Minimum 2 CSS pixel perimeter
- 3:1 contrast ratio (AA) or 4.5:1 (AAA)
- Visible against adjacent colors
- Sufficient size for visibility

### Target Size
- Minimum 24x24 CSS pixels (AA)
- Minimum 44x44 CSS pixels (AAA)
- Consider touch targets
- Spacing between targets

### Dragging Movements
- Provide alternative input methods
- Support keyboard navigation
- Allow pointer cancellation
- Provide undo mechanisms

### Consistent Help
- Place help in same location
- Maintain consistent order
- Use consistent mechanisms
- Make help easily accessible

### Redundant Entry
- Auto-populate known information
- Provide selection options
- Remember user inputs
- Reduce data re-entry

### Accessible Authentication
- Support password managers
- Provide alternative methods
- Avoid complex puzzles
- Support assistive technologies

### Status Messages
- Use appropriate ARIA roles
- Implement live regions
- Announce status changes
- Test with screen readers

## Testing Checklist

### Focus Management
- [ ] Focus indicators visible
- [ ] Focus not obscured
- [ ] Focus appearance meets contrast
- [ ] Focus size sufficient
- [ ] Keyboard navigation works

### Target Size
- [ ] Targets at least 24x24px (AA)
- [ ] Targets at least 44x44px (AAA)
- [ ] Adequate spacing between targets
- [ ] Touch-friendly on mobile

### Dragging Movements
- [ ] Alternative input methods available
- [ ] Keyboard navigation supported
- [ ] Pointer cancellation works
- [ ] Undo mechanisms available

### Consistent Help
- [ ] Help in consistent location
- [ ] Consistent order maintained
- [ ] Help easily accessible
- [ ] Multiple help mechanisms

### Redundant Entry
- [ ] Auto-population works
- [ ] Selection options available
- [ ] Information remembered
- [ ] Minimal re-entry required

### Accessible Authentication
- [ ] Password managers supported
- [ ] Alternative methods available
- [ ] No complex puzzles
- [ ] Assistive tech compatible

### Status Messages
- [ ] Status messages announced
- [ ] Appropriate ARIA roles used
- [ ] Live regions implemented
- [ ] Screen reader tested

## Best Practices

1. **Enhanced Focus Indicators**: Make focus highly visible
2. **Larger Touch Targets**: Ensure mobile accessibility
3. **Reduce Cognitive Load**: Simplify authentication
4. **Consistent Help**: Place help consistently
5. **Auto-Population**: Remember user information
6. **Status Announcements**: Properly announce status
7. **Alternative Inputs**: Provide multiple input methods
8. **Testing**: Regular accessibility testing
9. **Documentation**: Document accessibility features
10. **Continuous Improvement**: Regular audits

## Common Pitfalls

1. **Hidden Focus**: Focus obscured by overlays
2. **Small Targets**: Touch targets too small
3. **Complex Authentication**: Difficult authentication methods
4. **Inconsistent Help**: Help in different locations
5. **Redundant Entry**: Requiring repeated information
6. **No Status Announcements**: Status not announced
7. **Dragging Only**: No alternative input methods
8. **Poor Focus Appearance**: Weak focus indicators
9. **Mobile Issues**: Poor mobile accessibility
10. **Cognitive Barriers**: High cognitive load

