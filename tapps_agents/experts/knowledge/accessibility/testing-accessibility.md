# Accessibility Testing Techniques

## Overview

Accessibility testing ensures that websites and applications are usable by people with disabilities. Comprehensive testing includes automated tools, manual testing, and user testing with assistive technologies.

## Testing Approaches

### Automated Testing
- Quick identification of issues
- Consistent testing
- Part of CI/CD
- Limited coverage

### Manual Testing
- Human judgment required
- Keyboard navigation
- Screen reader testing
- Comprehensive evaluation

### User Testing
- Real user feedback
- Actual assistive technology users
- Identifies real issues
- Most valuable feedback

## Automated Testing Tools

### axe DevTools
- Browser extension
- Automated scanning
- Detailed reports
- CI/CD integration

### WAVE
- Web accessibility evaluation
- Visual feedback
- Browser extension
- Online tool

### Lighthouse
- Built into Chrome DevTools
- Accessibility audit
- Performance metrics
- Scoring system

### Pa11y
- Command-line tool
- CI/CD integration
- Multiple standards
- Automated reports

### HTML_CodeSniffer
- Bookmarklet tool
- Multiple standards
- Detailed reports
- Free and open-source

## Manual Testing

### Keyboard Navigation
- Unplug mouse
- Navigate with keyboard only
- Test all interactive elements
- Check tab order
- Verify focus indicators
- Test skip links

### Screen Reader Testing
- Test with NVDA (Windows)
- Test with JAWS (Windows)
- Test with VoiceOver (macOS/iOS)
- Test with TalkBack (Android)
- Verify announcements
- Check navigation

### Color Contrast
- Use contrast checkers
- Test text contrast
- Test UI component contrast
- Test in different conditions
- Use color blindness simulators

### Zoom Testing
- Test at 200% zoom
- Test at 400% zoom
- Verify content remains usable
- Check for horizontal scrolling
- Test responsive design

## Testing Checklist

### Perceivable
- [ ] Text alternatives for images
- [ ] Captions for video
- [ ] Sufficient color contrast
- [ ] Content resizable
- [ ] Semantic HTML
- [ ] Audio descriptions

### Operable
- [ ] Keyboard accessible
- [ ] No keyboard traps
- [ ] Sufficient time
- [ ] No seizures
- [ ] Navigable
- [ ] Focus visible

### Understandable
- [ ] Clear language
- [ ] Predictable
- [ ] Error messages
- [ ] Help available
- [ ] Consistent navigation

### Robust
- [ ] Valid HTML
- [ ] Proper ARIA
- [ ] Name, role, value
- [ ] Status messages
- [ ] Compatible

## Screen Reader Testing

### NVDA (Windows)
- Free, open-source
- Download and install
- Test navigation
- Test announcements
- Document issues

### JAWS (Windows)
- Commercial software
- Widely used
- Comprehensive testing
- Professional evaluation

### VoiceOver (macOS/iOS)
- Built into Apple devices
- Enable in settings
- Test with gestures
- Test navigation
- Verify announcements

### Testing Procedures
1. Enable screen reader
2. Navigate website
3. Test all interactive elements
4. Verify announcements
5. Check navigation
6. Document issues

## Keyboard Testing

### Testing Steps
1. Unplug mouse
2. Navigate with Tab
3. Activate with Enter/Space
4. Test all functions
5. Check tab order
6. Verify focus indicators
7. Test skip links
8. Document issues

### Key Commands
- Tab: Move forward
- Shift+Tab: Move backward
- Enter/Space: Activate
- Escape: Cancel/Close
- Arrow keys: Navigate within components

## Color Contrast Testing

### Tools
- WebAIM Contrast Checker
- Colour Contrast Analyser
- Browser DevTools
- axe DevTools

### Testing
- Test all text combinations
- Test UI components
- Test interactive states
- Use color blindness simulators
- Test in different lighting

## Responsive Design Testing

### Viewport Sizes
- Mobile (320px)
- Tablet (768px)
- Desktop (1024px+)
- Large screens (1920px+)

### Zoom Testing
- 200% zoom
- 400% zoom
- Verify usability
- Check for scrolling
- Test reflow

## Form Testing

### Checklist
- [ ] All fields have labels
- [ ] Labels associated with inputs
- [ ] Required fields indicated
- [ ] Error messages clear
- [ ] Errors associated with fields
- [ ] Keyboard navigable
- [ ] Help text available
- [ ] Autocomplete works

## Testing Workflow

### 1. Automated Testing
- Run automated tools
- Fix obvious issues
- Document findings
- Prioritize issues

### 2. Manual Testing
- Keyboard navigation
- Screen reader testing
- Color contrast
- Zoom testing
- Document issues

### 3. User Testing
- Test with real users
- Gather feedback
- Identify pain points
- Improve based on feedback

### 4. Continuous Testing
- Test during development
- Include in CI/CD
- Regular audits
- Monitor improvements

## CI/CD Integration

### Automated Checks
- Run accessibility tests
- Fail build on errors
- Generate reports
- Track metrics

### Tools
- axe-core
- Pa11y
- Lighthouse CI
- HTML_CodeSniffer

## Reporting Issues

### Issue Documentation
- Description of issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots/videos
- Priority level
- WCAG criteria

### Priority Levels
- Critical: Blocks users
- High: Significant impact
- Medium: Moderate impact
- Low: Minor impact

## Best Practices

### 1. Test Early and Often
- Test during development
- Catch issues early
- Reduce cost of fixes
- Improve quality

### 2. Use Multiple Tools
- Automated tools
- Manual testing
- User testing
- Comprehensive coverage

### 3. Test with Real Users
- Actual assistive technology users
- Real-world scenarios
- Valuable feedback
- Identify real issues

### 4. Document Everything
- Test results
- Issues found
- Fixes applied
- User feedback

### 5. Continuous Improvement
- Regular audits
- Monitor metrics
- Update testing
- Stay current

## Common Testing Mistakes

### 1. Relying Only on Automated Tools
- Automated tools miss issues
- Need manual testing
- Need user testing
- Comprehensive approach

### 2. Not Testing with Screen Readers
- Screen readers essential
- Test with multiple screen readers
- Verify announcements
- Check navigation

### 3. Ignoring Keyboard Navigation
- Many users rely on keyboard
- Test keyboard-only
- Verify all functions work
- Check tab order

### 4. Not Testing Forms
- Forms critical for users
- Test form completion
- Verify error handling
- Check help text

### 5. Not Testing on Mobile
- Mobile accessibility important
- Test touch targets
- Test zoom
- Test responsive design

## Testing Resources

### Tools
- axe DevTools
- WAVE
- Lighthouse
- Pa11y
- HTML_CodeSniffer

### Screen Readers
- NVDA
- JAWS
- VoiceOver
- TalkBack

### Documentation
- WCAG guidelines
- ARIA specification
- WebAIM resources
- A11y Project

## Best Practices Summary

1. **Multiple Approaches**: Automated, manual, user testing
2. **Test Early**: During development
3. **Screen Readers**: Test with multiple screen readers
4. **Keyboard Only**: Test keyboard navigation
5. **Real Users**: Test with actual users
6. **Document Issues**: Comprehensive documentation
7. **Continuous Testing**: Regular audits
8. **CI/CD Integration**: Automated checks
9. **Stay Current**: Follow latest standards
10. **User Feedback**: Gather and act on feedback

