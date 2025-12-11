# Color Contrast Requirements

## Overview

Color contrast is critical for accessibility. Sufficient contrast ensures that text and interactive elements are readable by users with low vision, color blindness, or in various lighting conditions.

## WCAG Contrast Requirements

### Level AA (Minimum)
- **Normal text**: 4.5:1 contrast ratio
- **Large text**: 3:1 contrast ratio (18pt+ or 14pt+ bold)
- **UI components**: 3:1 contrast ratio
- **Graphical objects**: 3:1 contrast ratio

### Level AAA (Enhanced)
- **Normal text**: 7:1 contrast ratio
- **Large text**: 4.5:1 contrast ratio
- **UI components**: 3:1 contrast ratio
- **Graphical objects**: 3:1 contrast ratio

## Contrast Ratio Calculation

### Formula
```
Contrast Ratio = (L1 + 0.05) / (L2 + 0.05)
```
Where:
- L1 = Relative luminance of lighter color
- L2 = Relative luminance of darker color

### Relative Luminance
- Calculated from RGB values
- Accounts for human perception
- Uses sRGB color space
- Standardized formula

## Text Contrast

### Normal Text
- Body text
- Paragraph text
- Form labels
- Button text
- Link text
- Minimum 4.5:1 (AA) or 7:1 (AAA)

### Large Text
- Headings (18pt+)
- Bold text (14pt+ bold)
- Minimum 3:1 (AA) or 4.5:1 (AAA)
- Easier to read at larger sizes

### Decorative Text
- Logos
- Decorative text
- Not required to meet contrast
- Must not convey information

## UI Component Contrast

### Interactive Elements
- Buttons
- Form controls
- Links
- Focus indicators
- Minimum 3:1 contrast

### States
- Hover states
- Focus states
- Active states
- Disabled states
- All must meet contrast

### Borders
- Form field borders
- Button borders
- Focus outlines
- Minimum 3:1 contrast

## Graphical Objects

### Icons
- Icon graphics
- UI icons
- Status indicators
- Minimum 3:1 contrast

### Charts and Graphs
- Data visualization
- Chart elements
- Graph lines
- Minimum 3:1 contrast

### Images of Text
- Text in images
- Screenshots with text
- Minimum 4.5:1 (AA) or 7:1 (AAA)
- Prefer actual text

## Non-Text Contrast (WCAG 2.1)

### UI Components
- Visual information required to identify components
- Icons
- Form controls
- Minimum 3:1 contrast

### Graphical Objects
- Parts of graphics required to understand content
- Charts
- Diagrams
- Minimum 3:1 contrast

## Color and Information

### Don't Rely on Color Alone
- Use color plus other indicators
- Icons with color
- Text labels
- Patterns or shapes
- Underlines for links

### Color Blindness
- Red-green color blindness (most common)
- Blue-yellow color blindness
- Complete color blindness (rare)
- Test with color blindness simulators

## Testing Contrast

### Tools
- **WebAIM Contrast Checker**: Online tool
- **Colour Contrast Analyser**: Desktop tool
- **Browser DevTools**: Built-in checkers
- **axe DevTools**: Automated testing
- **WAVE**: Web accessibility evaluation

### Manual Testing
- Visual inspection
- Use contrast checkers
- Test with color blindness simulators
- Test in different lighting
- Test on different displays

### Automated Testing
- Use accessibility testing tools
- Check during development
- Include in CI/CD
- Regular audits

## Common Issues

### Insufficient Text Contrast
- Light gray text on white
- Yellow text on white
- Low contrast combinations
- Not meeting 4.5:1 ratio

### Poor UI Contrast
- Light buttons on light backgrounds
- Low contrast borders
- Invisible focus indicators
- Not meeting 3:1 ratio

### Color-Only Information
- Red text for errors only
- Color-coded status only
- No additional indicators
- Inaccessible to color blind users

### Background Images
- Text over images
- Variable contrast
- Difficult to ensure contrast
- Need solid backgrounds

## Best Practices

### 1. Design with Contrast in Mind
- Choose high-contrast color schemes
- Test during design phase
- Use contrast checkers
- Consider all users

### 2. Test Regularly
- Test all text combinations
- Test UI components
- Test interactive states
- Use automated tools

### 3. Provide Alternatives
- Don't rely on color alone
- Use icons with color
- Provide text labels
- Use patterns or shapes

### 4. Consider Context
- Test in different lighting
- Test on different displays
- Consider user preferences
- Allow customization

### 5. Document Standards
- Define color palette
- Document contrast ratios
- Provide guidelines
- Share with team

## Color Palette Guidelines

### High Contrast Palette
- Dark text on light backgrounds
- Light text on dark backgrounds
- Avoid similar colors
- Test all combinations

### Accessible Colors
- Blue: Good for links
- Red: Use with caution
- Green: Use with caution
- Yellow: Low contrast, avoid

### Brand Colors
- Ensure brand colors meet contrast
- Provide alternative palettes
- Use brand colors for accents
- Don't sacrifice accessibility

## Implementation

### CSS Variables
```css
:root {
  --text-primary: #000000; /* 21:1 on white */
  --text-secondary: #333333; /* 12.6:1 on white */
  --bg-primary: #ffffff;
  --bg-secondary: #f5f5f5;
  --accent: #0066cc; /* 7:1 on white */
}
```

### Focus Indicators
```css
:focus {
  outline: 3px solid #0066cc; /* High contrast */
  outline-offset: 2px;
}
```

### Error States
```css
.error {
  color: #d32f2f; /* High contrast red */
  border-color: #d32f2f;
  /* Plus icon or text label */
}
```

## Testing Checklist

- [ ] All text meets 4.5:1 (AA) or 7:1 (AAA)
- [ ] Large text meets 3:1 (AA) or 4.5:1 (AAA)
- [ ] UI components meet 3:1
- [ ] Focus indicators meet 3:1
- [ ] Interactive states meet 3:1
- [ ] Icons meet 3:1
- [ ] Charts/graphs meet 3:1
- [ ] Don't rely on color alone
- [ ] Tested with color blindness simulators
- [ ] Tested in different conditions

## Best Practices Summary

1. **Meet WCAG Standards**: 4.5:1 for text, 3:1 for UI
2. **Test Regularly**: Use contrast checkers
3. **Don't Rely on Color**: Provide additional indicators
4. **Consider All Users**: Test with color blindness
5. **Design Accessibly**: Start with high contrast
6. **Document Standards**: Define accessible palette
7. **Test States**: All interactive states
8. **Automate Testing**: Include in CI/CD
9. **User Feedback**: Test with users
10. **Continuous Improvement**: Regular audits

