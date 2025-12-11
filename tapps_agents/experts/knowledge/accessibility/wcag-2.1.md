# WCAG 2.1 Guidelines

## Overview

Web Content Accessibility Guidelines (WCAG) 2.1 is a set of guidelines for making web content more accessible to people with disabilities. WCAG 2.1 extends WCAG 2.0 and provides additional success criteria for mobile accessibility and users with low vision and cognitive disabilities.

## Conformance Levels

### Level A (Minimum)
- Basic accessibility requirements
- Must be met for basic accessibility
- Foundation for accessibility

### Level AA (Recommended)
- Enhanced accessibility requirements
- Recommended for most websites
- Meets legal requirements in many jurisdictions

### Level AAA (Enhanced)
- Highest level of accessibility
- Not required for all content
- May not be achievable for all content types

## Four Principles

### 1. Perceivable
Information and user interface components must be presentable to users in ways they can perceive.

### 2. Operable
User interface components and navigation must be operable.

### 3. Understandable
Information and the operation of user interface must be understandable.

### 4. Robust
Content must be robust enough that it can be interpreted by a wide variety of user agents, including assistive technologies.

## Perceivable Guidelines

### 1.1 Text Alternatives (Level A)
- Provide text alternatives for non-text content
- Alt text for images
- Descriptions for complex images
- Text alternatives for audio/video
- Labels for form controls

### 1.2 Time-based Media (Level A/AA/AAA)
- Captions for prerecorded audio (Level A)
- Audio description for video (Level AA)
- Sign language interpretation (Level AAA)
- Extended audio description (Level AAA)
- Media alternative for text (Level AAA)

### 1.3 Adaptable (Level A)
- Info and relationships preserved (Level A)
- Meaningful sequence (Level A)
- Sensory characteristics (Level A)
- Orientation (Level AA - 2.1)
- Identify input purpose (Level AA - 2.1)
- Reflow (Level AA - 2.1)
- Non-text contrast (Level AA - 2.1)
- Text spacing (Level AA - 2.1)
- Content on hover or focus (Level AA - 2.1)

### 1.4 Distinguishable (Level A/AA)
- Use of color (Level A)
- Audio control (Level A)
- Contrast minimum (Level AA)
- Resize text (Level AA)
- Images of text (Level AA)
- Contrast enhanced (Level AAA)
- Low or no background audio (Level AAA)
- Visual presentation (Level AAA)
- Images of text (no exception) (Level AAA)

## Operable Guidelines

### 2.1 Keyboard Accessible (Level A)
- Keyboard (Level A)
- No keyboard trap (Level A)
- Keyboard shortcuts (Level A - 2.1)
- Character key shortcuts (Level A - 2.1)

### 2.2 Enough Time (Level A/AAA)
- Timing adjustable (Level A)
- Pause, stop, hide (Level A)
- No timing (Level AAA)
- Interruptions (Level AAA)
- Re-authenticating (Level AAA)
- Timeouts (Level AAA - 2.1)

### 2.3 Seizures and Physical Reactions (Level AAA)
- Three flashes or below threshold (Level AAA)
- Three flashes (Level AAA)
- Animation from interactions (Level AAA - 2.1)

### 2.4 Navigable (Level A/AA)
- Bypass blocks (Level A)
- Page titled (Level A)
- Focus order (Level A)
- Link purpose (Level A)
- Multiple ways (Level AA)
- Headings and labels (Level AA)
- Focus visible (Level AA)
- Location (Level AA)
- Section headings (Level AA)
- Focus not obscured (Level AA - 2.1)
- Dragging movements (Level AA - 2.1)
- Target size (Level AA - 2.1)
- Concurrent input mechanisms (Level AAA - 2.1)

### 2.5 Input Modalities (Level A/AA - 2.1)
- Pointer gestures (Level A)
- Pointer cancellation (Level A)
- Label in name (Level A)
- Motion actuation (Level A)
- Target size (Level AAA)
- Concurrent input mechanisms (Level AAA)

## Understandable Guidelines

### 3.1 Readable (Level A/AA)
- Language of page (Level A)
- Language of parts (Level AA)
- Unusual words (Level AAA)
- Abbreviations (Level AAA)
- Reading level (Level AAA)
- Pronunciation (Level AAA)

### 3.2 Predictable (Level A/AA)
- On focus (Level A)
- On input (Level A)
- Consistent navigation (Level AA)
- Consistent identification (Level AA)
- Change on request (Level AAA)

### 3.3 Input Assistance (Level A/AA/AAA)
- Error identification (Level A)
- Labels or instructions (Level A)
- Error suggestion (Level AA)
- Error prevention (legal, financial, data) (Level AA)
- Help (Level AAA)
- Error prevention (all) (Level AAA)

## Robust Guidelines

### 4.1 Compatible (Level A)
- Parsing (Level A)
- Name, role, value (Level A)
- Status messages (Level AA - 2.1)

## WCAG 2.1 New Success Criteria

### 1.3.4 Orientation (Level AA)
- Content does not restrict its view and operation to a single display orientation
- Support both portrait and landscape orientations
- Unless a specific display orientation is essential

### 1.3.5 Identify Input Purpose (Level AA)
- Input fields collecting information about the user have an appropriate autocomplete attribute
- Helps users with cognitive disabilities
- Improves form completion

### 1.4.10 Reflow (Level AA)
- Content can be presented without loss of information or functionality
- No horizontal scrolling at 320 CSS pixels width
- Supports responsive design

### 1.4.11 Non-text Contrast (Level AA)
- Visual information required to identify user interface components has a contrast ratio of at least 3:1
- Applies to UI components and graphical objects
- Not just text

### 1.4.12 Text Spacing (Level AA)
- No loss of content or functionality when text spacing is adjusted
- Line height, paragraph spacing, letter spacing, word spacing
- Supports user customization

### 1.4.13 Content on Hover or Focus (Level AA)
- Additional content on hover or focus is dismissible, hoverable, and persistent
- Prevents accidental triggering
- Allows users to interact with additional content

### 2.1.4 Character Key Shortcuts (Level A)
- If a keyboard shortcut is implemented using only letter, number, punctuation, or symbol characters, then at least one of the following is true:
  - Turn off: Mechanism to turn off shortcut
  - Remap: Mechanism to remap shortcut
  - Active only on focus: Shortcut only active when component has focus

### 2.2.6 Timeouts (Level AAA)
- Users are warned of the duration of any user inactivity that could cause data loss
- Unless data is preserved for more than 20 hours

### 2.3.3 Animation from Interactions (Level AAA)
- Motion animation triggered by interaction can be disabled
- Unless the animation is essential to the functionality

### 2.4.11 Focus Not Obscured (Minimum) (Level AA)
- When a keyboard interface component receives focus, the component is not entirely hidden due to author-created content
- At least a portion of the component is visible

### 2.4.12 Focus Not Obscured (Enhanced) (Level AAA)
- When a keyboard interface component receives focus, nothing in the viewport obscures it
- Complete visibility of focused component

### 2.5.2 Pointer Cancellation (Level A)
- For functionality that can be operated using a single-pointer, at least one of the following is true:
  - No down-event: The down-event of the pointer is not used to execute any part of the function
  - Abort or undo: Completion of the function is on the up-event, and a mechanism is available to abort the function before completion or to undo the function after completion
  - Up reversal: The up-event reverses any outcome of the preceding down-event
  - Essential: Completing the function on the down-event is essential

### 2.5.3 Label in Name (Level A)
- For user interface components with labels that include text or images of text, the name contains the text that is presented visually
- Accessible name matches visible label

### 2.5.4 Motion Actuation (Level A)
- Functionality that can be operated by device motion or user motion can also be operated by user interface components
- Motion-based functionality can be disabled
- Alternative input method available

### 2.5.5 Target Size (Level AAA)
- Target size for pointer inputs is at least 44 by 44 CSS pixels
- Exceptions for inline, essential, user agent control, equivalent target

### 2.5.6 Concurrent Input Mechanisms (Level AAA)
- Web content does not restrict use of input modalities available on a platform
- Users can switch between input methods

### 4.1.3 Status Messages (Level AA)
- In content implemented using markup languages, status messages can be programmatically determined through role or properties
- Screen readers can announce status messages

## Implementation Checklist

### Perceivable
- [ ] Provide text alternatives for images
- [ ] Provide captions for video
- [ ] Ensure sufficient color contrast
- [ ] Make content resizable
- [ ] Use semantic HTML
- [ ] Provide audio descriptions
- [ ] Support multiple orientations
- [ ] Ensure reflow at 320px width

### Operable
- [ ] Ensure keyboard accessibility
- [ ] Provide skip links
- [ ] Make focus visible
- [ ] Provide sufficient target size
- [ ] Allow time adjustments
- [ ] Prevent keyboard traps
- [ ] Support pointer cancellation
- [ ] Ensure focus not obscured

### Understandable
- [ ] Use clear language
- [ ] Provide error messages
- [ ] Use consistent navigation
- [ ] Identify language of content
- [ ] Provide help text
- [ ] Use predictable interactions

### Robust
- [ ] Use valid HTML
- [ ] Provide proper ARIA labels
- [ ] Ensure name, role, value
- [ ] Announce status messages
- [ ] Test with assistive technologies

## Best Practices

1. **Start with Semantic HTML**: Use proper HTML elements
2. **Test with Screen Readers**: Test with NVDA, JAWS, VoiceOver
3. **Keyboard Navigation**: Ensure full keyboard accessibility
4. **Color Contrast**: Use sufficient contrast ratios
5. **Focus Management**: Make focus visible and logical
6. **Error Handling**: Provide clear error messages
7. **Testing**: Regular accessibility testing
8. **Documentation**: Document accessibility features
9. **Training**: Train team on accessibility
10. **Continuous Improvement**: Regular accessibility audits

## Common Pitfalls

1. **Missing Alt Text**: Images without alt text
2. **Poor Color Contrast**: Insufficient contrast ratios
3. **Keyboard Traps**: Focus trapped in components
4. **Missing Focus Indicators**: No visible focus
5. **Inaccessible Forms**: Forms without proper labels
6. **Missing Skip Links**: No way to skip navigation
7. **Auto-playing Media**: Media that auto-plays
8. **Insufficient Target Size**: Small click targets
9. **Missing ARIA Labels**: Components without labels
10. **Poor Error Messages**: Unclear error messages

