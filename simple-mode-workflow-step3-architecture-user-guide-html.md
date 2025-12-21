# Step 3: Architecture Design - User Guide HTML

## System Architecture Overview

The user guide HTML will be a comprehensive, single-page or multi-section document that serves as the primary entry point for TappsCodingAgents documentation.

## Architecture Principles

1. **Single Source of Truth**: Content should be accurate and reflect the current state of the framework
2. **Progressive Disclosure**: Information organized from high-level to detailed
3. **Accessibility First**: WCAG 2.1 AA compliance from the start
4. **Design System Consistency**: Uses existing `docs/html/styles.css` patterns
5. **Mobile-First**: Responsive design that works on all devices

## Component Architecture

### 1. Document Structure

```
docs/html/user-guide-index.html (or user-guide.html)
├── <head>
│   ├── Meta tags (charset, viewport, description, title)
│   ├── Stylesheet link (styles.css)
│   └── Font imports (Inter, JetBrains Mono)
├── <body>
│   ├── Navigation Bar (navbar)
│   ├── Main Content (main-content)
│   │   ├── Hero/Overview Section
│   │   ├── Getting Started Section
│   │   ├── Simple Mode Section
│   │   ├── Agent Reference Section
│   │   ├── Features Section
│   │   ├── Command Reference Section
│   │   └── Examples Section
│   └── Footer
```

### 2. Navigation Architecture

**Top Navigation Bar:**
- Sticky position for constant access
- Links to: Home, User Guide (active), Technical Spec, Examples, API Reference
- Brand logo/name on left
- Version indicator

**Table of Contents (Optional):**
- For long single-page guides
- Sticky sidebar or inline
- Jump links to sections
- Progress indicator

### 3. Content Sections

#### Section 1: Hero/Overview
- **Purpose**: Introduce TappsCodingAgents
- **Components**: 
  - Heading with gradient text
  - Brief description
  - Key features list (icon cards)
  - Quick links to getting started

#### Section 2: Getting Started
- **Purpose**: Onboarding new users
- **Components**:
  - Installation steps
  - Setup instructions
  - First commands
  - Code examples with copy buttons

#### Section 3: Simple Mode
- **Purpose**: Complete Simple Mode documentation
- **Components**:
  - What is Simple Mode
  - Command reference table
  - Workflow diagrams (if possible) or descriptions
  - Examples for each command type
  - Configuration guide

#### Section 4: Agent Reference
- **Purpose**: Comprehensive agent documentation
- **Components**:
  - Agent grid (13 agents)
  - Individual agent cards with:
    - Agent name and icon
    - Purpose description
    - When to use
    - Commands (CLI + Cursor Skills)
    - Example usage
    - Link to detailed docs (if exists)

#### Section 5: Features & Capabilities
- **Purpose**: Showcase framework capabilities
- **Components**:
  - Feature cards grid
  - Detailed feature descriptions
  - Visual indicators/icons
  - Links to related sections

#### Section 6: Command Reference
- **Purpose**: Quick command lookup
- **Components**:
  - Organized by category (CLI, Cursor Skills, Simple Mode)
  - Command tables with descriptions
  - Syntax examples
  - Quick reference card/cheat sheet

#### Section 7: Examples
- **Purpose**: Practical usage examples
- **Components**:
  - Example cards
  - Code blocks with syntax highlighting
  - Expected output
  - Use case descriptions

### 4. Data Flow

```
Source Markdown Docs
    ↓
Content Extraction
    ↓
HTML Structure Creation
    ↓
Styling Application (styles.css)
    ↓
Link Integration
    ↓
Final HTML Document
```

### 5. Styling Architecture

**CSS Layer Structure:**
- Uses existing `styles.css` from `docs/html/`
- CSS Variables for theming:
  - `--primary`, `--primary-light`, `--primary-dark`
  - `--bg-primary`, `--bg-secondary`, `--bg-tertiary`
  - `--text-primary`, `--text-secondary`, `--text-muted`
  - Gradients: `--gradient-1`, `--gradient-2`, `--gradient-3`

**Component Classes:**
- `.doc-card` - Card component for sections/links
- `.code-block` - Syntax highlighted code blocks
- `.command-table` - Command reference tables
- `.agent-grid` - Grid layout for agents
- `.feature-card` - Feature showcase cards
- `.example-card` - Example display cards

**Responsive Breakpoints:**
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

### 6. Component Specifications

#### Navigation Component
```html
<nav class="navbar">
  <div class="nav-container">
    <div class="nav-brand">...</div>
    <ul class="nav-menu">...</ul>
  </div>
</nav>
```

**Properties:**
- Sticky positioning
- Backdrop blur effect
- Responsive menu (mobile hamburger if needed)

#### Agent Card Component
```html
<div class="agent-card">
  <div class="agent-icon">...</div>
  <h3 class="agent-name">...</h3>
  <p class="agent-description">...</p>
  <div class="agent-commands">...</div>
  <div class="agent-examples">...</div>
</div>
```

**Properties:**
- Hover effects
- Gradient borders
- Icon display
- Expandable details (optional)

#### Code Block Component
```html
<div class="code-block">
  <div class="code-header">
    <span class="code-language">bash</span>
    <button class="copy-button">Copy</button>
  </div>
  <pre><code>...</code></pre>
</div>
```

**Properties:**
- Syntax highlighting (via Prism.js or similar, if available)
- Copy to clipboard functionality
- Language indicator
- Scrollable for long code

### 7. Performance Considerations

**Optimization Strategies:**
1. **CSS**: Use existing styles.css (no additional CSS files)
2. **JavaScript**: Minimal JS needed (only for copy buttons, smooth scroll)
3. **Images**: Use SVG icons (inline or sprite) - no raster images
4. **Fonts**: Use existing font imports
5. **Lazy Loading**: Not applicable (single HTML file)

**Bundle Size Targets:**
- HTML: < 200KB (uncompressed)
- CSS: Uses existing styles.css (shared across docs)
- JS: < 10KB (minimal functionality)

### 8. Accessibility Architecture

**Semantic HTML:**
- Proper use of `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`
- Heading hierarchy (h1 → h2 → h3)
- List elements (`<ul>`, `<ol>`) for lists
- `<table>` for tabular data

**ARIA Labels:**
- Navigation landmarks
- Button labels
- Form labels (if any)
- Skip to content link

**Keyboard Navigation:**
- Tab order logical
- Focus indicators visible
- Skip links for navigation

**Screen Reader Support:**
- Descriptive alt text (if images)
- ARIA labels where needed
- Proper heading structure
- Landmark regions

### 9. Browser Compatibility

**Target Browsers:**
- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Opera (latest version)

**CSS Features Used:**
- CSS Variables (custom properties) - supported in all modern browsers
- Flexbox - fully supported
- Grid - fully supported
- Backdrop-filter - may need fallback for older browsers

### 10. Integration Points

**Internal Links:**
- Link to `index.html` (home)
- Link to `technical-spec.html`
- Link to `api-reference.html`
- Link to `examples.html`
- Link to other user guide pages if multi-page

**External Links:**
- GitHub repository
- Documentation repository
- Issue tracker (if applicable)

**Navigation Consistency:**
- Same navbar structure as other HTML docs
- Same footer structure
- Consistent styling

### 11. Maintenance Architecture

**Content Updates:**
- Single HTML file (easy to update)
- Source content from markdown docs (maintain source of truth)
- Version indicator in header/footer

**Future Extensibility:**
- Modular section structure (easy to add/remove sections)
- Component-based CSS classes (reusable)
- Clear documentation comments in HTML

## Technical Stack

- **HTML5**: Semantic markup
- **CSS3**: Existing styles.css (CSS Variables, Flexbox, Grid)
- **JavaScript**: Minimal (copy buttons, smooth scroll)
- **No Build Process**: Pure HTML/CSS/JS (no compilation needed)

## File Structure

```
docs/html/
├── user-guide-index.html (or user-guide.html) ← Target file
├── styles.css (existing, reuse)
├── index.html (existing)
├── technical-spec.html (existing)
├── api-reference.html (existing)
└── examples.html (existing)
```

## Design Patterns

1. **Card Pattern**: Used for agents, features, examples
2. **Grid Pattern**: Responsive grid for agent/feature display
3. **Code Block Pattern**: Consistent code display with copy functionality
4. **Table Pattern**: Command reference tables
5. **Navigation Pattern**: Consistent across all HTML docs

## Security Considerations

- No external scripts (except fonts)
- No user input forms
- Static content only
- XSS protection: Proper HTML escaping in content (if dynamically generated)

## Testing Strategy

1. **Visual Testing**: Cross-browser visual regression
2. **Accessibility Testing**: WCAG 2.1 AA validation
3. **Responsive Testing**: Mobile, tablet, desktop views
4. **Link Testing**: All links work correctly
5. **Code Copy Testing**: Copy buttons function correctly

---

## Architecture Summary

**Key Decisions:**
1. Single comprehensive HTML file (or well-organized multi-section)
2. Reuse existing styles.css (design system consistency)
3. Semantic HTML5 for accessibility
4. Minimal JavaScript (progressive enhancement)
5. Mobile-first responsive design
6. Component-based CSS architecture

**Success Criteria:**
- ✅ Comprehensive content coverage
- ✅ Accessible (WCAG 2.1 AA)
- ✅ Mobile responsive
- ✅ Fast loading
- ✅ Design system consistency
- ✅ Easy to maintain and update

