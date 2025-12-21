# Step 4: Design Specifications - User Guide HTML

## Design System

### Color Palette
Using existing CSS variables from `styles.css`:

```css
--primary: #6366f1
--primary-dark: #4f46e5
--primary-light: #818cf8
--secondary: #8b5cf6
--accent: #ec4899
--success: #10b981
--warning: #f59e0b
--error: #ef4444
--bg-primary: #0f172a
--bg-secondary: #1e293b
--bg-tertiary: #334155
--text-primary: #f1f5f9
--text-secondary: #cbd5e1
--text-muted: #94a3b8
--border: #475569
```

### Typography
- **Font Family**: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
- **Code Font**: 'JetBrains Mono', 'Courier New', monospace
- **Heading Sizes**:
  - h1: 2.5rem - 3rem (clamp for responsiveness)
  - h2: 2rem
  - h3: 1.5rem
  - h4: 1.25rem
- **Line Height**: 1.6 (body), 1.4 (headings)

### Spacing System
- **Base Unit**: 1rem (16px)
- **Spacing Scale**: 0.5rem, 1rem, 1.5rem, 2rem, 3rem, 4rem
- **Section Padding**: 3rem - 4rem vertical
- **Card Padding**: 2rem
- **Grid Gap**: 2rem

## Component Specifications

### 1. Navigation Bar

**Structure:**
```html
<nav class="navbar">
  <div class="nav-container">
    <div class="nav-brand">
      <h1>🤖 TappsCodingAgents</h1>
      <span class="version">v2.0.6</span>
    </div>
    <ul class="nav-menu">
      <li><a href="index.html">Home</a></li>
      <li><a href="user-guide-index.html" class="active">User Guide</a></li>
      <li><a href="technical-spec.html">Technical Spec</a></li>
      <li><a href="examples.html">Examples</a></li>
      <li><a href="api-reference.html">API Reference</a></li>
    </ul>
  </div>
</nav>
```

**Properties:**
- Sticky position (sticky top)
- Backdrop blur effect
- Border bottom
- Responsive (mobile: hamburger menu if needed)

**CSS Classes:** (from existing styles.css)
- `.navbar`
- `.nav-container`
- `.nav-brand`
- `.nav-menu`
- `.active` (for active nav item)

### 2. Hero/Overview Section

**Structure:**
```html
<section class="hero-section">
  <h1 class="hero-title">User Guide</h1>
  <p class="lead">Complete guide to using TappsCodingAgents...</p>
  <div class="key-features">
    <!-- Feature badges/icons -->
  </div>
</section>
```

**Design:**
- Center-aligned text
- Large gradient heading
- Lead paragraph (larger text, secondary color)
- Feature badges/icons grid

**CSS Classes:**
- `.hero-section` (extends `.hero` from styles.css)
- `.hero-title` (gradient text)
- `.lead` (larger paragraph)
- `.key-features` (badge grid)

### 3. Getting Started Section

**Structure:**
```html
<section id="getting-started">
  <h2>Getting Started</h2>
  <div class="steps-container">
    <div class="step-card">
      <div class="step-number">1</div>
      <h3>Installation</h3>
      <p>Description...</p>
      <div class="code-block">...</div>
    </div>
    <!-- More steps -->
  </div>
</section>
```

**Design:**
- Numbered steps
- Step cards with icons/numbers
- Code blocks for commands
- Alert boxes for important notes

**CSS Classes:**
- `.steps-container` (flex or grid)
- `.step-card` (extends `.doc-card`)
- `.step-number` (circular badge)
- `.code-block` (from styles.css)
- `.alert` (info, success, warning styles)

### 4. Simple Mode Section

**Structure:**
```html
<section id="simple-mode">
  <h2>Simple Mode</h2>
  <p class="section-intro">Simple Mode provides...</p>
  
  <div class="command-reference">
    <h3>Commands</h3>
    <table class="command-table">
      <thead>
        <tr>
          <th>Command</th>
          <th>Description</th>
          <th>Skills Invoked</th>
        </tr>
      </thead>
      <tbody>
        <!-- Command rows -->
      </tbody>
    </table>
  </div>
  
  <div class="workflow-section">
    <h3>Build Workflow (7 Steps)</h3>
    <div class="workflow-steps">
      <!-- Step cards -->
    </div>
  </div>
  
  <div class="examples-grid">
    <!-- Example cards -->
  </div>
</section>
```

**Design:**
- Command reference table
- Workflow visualization (step cards)
- Examples grid with code blocks

**CSS Classes:**
- `.command-table` (styled table)
- `.workflow-steps` (horizontal or vertical flow)
- `.workflow-step-card` (numbered step card)
- `.examples-grid` (grid layout)

### 5. Agent Reference Section

**Structure:**
```html
<section id="agents">
  <h2>Agent Reference</h2>
  <p class="section-intro">TappsCodingAgents provides 13 specialized agents...</p>
  
  <div class="agent-categories">
    <div class="agent-category">
      <h3>Planning</h3>
      <div class="agent-grid">
        <div class="agent-card">
          <div class="agent-icon">📊</div>
          <h4>Analyst</h4>
          <p class="agent-description">Requirements gathering...</p>
          <div class="agent-details">
            <h5>When to Use</h5>
            <ul>...</ul>
            <h5>Commands</h5>
            <div class="code-block">...</div>
          </div>
        </div>
        <!-- More agents -->
      </div>
    </div>
    <!-- More categories -->
  </div>
</section>
```

**Design:**
- Organized by category (Planning, Design, Development, Testing, Quality, Operations, Orchestration, Enhancement)
- Agent cards in grid layout
- Expandable details (optional, or always visible)
- Icons for each agent
- Command examples

**CSS Classes:**
- `.agent-categories` (vertical sections)
- `.agent-category` (category container)
- `.agent-grid` (grid layout, 2-3 columns)
- `.agent-card` (extends `.doc-card`)
- `.agent-icon` (large emoji/icon)
- `.agent-details` (collapsible or always visible)

### 6. Features & Capabilities Section

**Structure:**
```html
<section id="features">
  <h2>Features & Capabilities</h2>
  <div class="features-grid">
    <div class="feature-card">
      <div class="feature-icon">🤖</div>
      <h3>13 Workflow Agents</h3>
      <p>Specialized agents covering...</p>
      <ul>
        <li>Planning: analyst, planner</li>
        <li>Design: architect, designer</li>
        <!-- More -->
      </ul>
    </div>
    <!-- More feature cards -->
  </div>
</section>
```

**Design:**
- Grid layout (3 columns desktop, 2 tablet, 1 mobile)
- Feature cards with icons
- Lists for sub-features
- Hover effects

**CSS Classes:**
- `.features-grid` (from styles.css)
- `.feature-card` (from styles.css)
- `.feature-icon` (from styles.css)

### 7. Command Reference Section

**Structure:**
```html
<section id="commands">
  <h2>Command Reference</h2>
  
  <div class="command-categories">
    <div class="command-category">
      <h3>CLI Commands</h3>
      <table class="command-table">
        <!-- Commands -->
      </table>
    </div>
    
    <div class="command-category">
      <h3>Cursor Skills</h3>
      <table class="command-table">
        <!-- Commands -->
      </table>
    </div>
    
    <div class="command-category">
      <h3>Simple Mode</h3>
      <table class="command-table">
        <!-- Commands -->
      </table>
    </div>
  </div>
  
  <div class="quick-reference">
    <h3>Quick Reference</h3>
    <div class="cheat-sheet">
      <!-- Command cheat sheet -->
    </div>
  </div>
</section>
```

**Design:**
- Organized by command type (CLI, Cursor Skills, Simple Mode)
- Tables for command reference
- Quick reference card/cheat sheet

**CSS Classes:**
- `.command-categories` (vertical sections)
- `.command-table` (styled table)
- `.quick-reference` (highlighted section)
- `.cheat-sheet` (compact grid or list)

### 8. Examples Section

**Structure:**
```html
<section id="examples">
  <h2>Examples</h2>
  
  <div class="examples-categories">
    <div class="example-category">
      <h3>Simple Mode Examples</h3>
      <div class="examples-grid">
        <div class="example-card">
          <h4>Build Feature</h4>
          <p class="example-description">Build a user authentication feature</p>
          <div class="code-block">
            <div class="code-header">
              <span>Command</span>
              <button class="copy-btn">Copy</button>
            </div>
            <pre><code>@simple-mode *build "Create JWT authentication..."</code></pre>
          </div>
          <div class="example-output">
            <h5>Expected Output:</h5>
            <p>Step 1: @enhancer...</p>
          </div>
        </div>
        <!-- More examples -->
      </div>
    </div>
    <!-- More example categories -->
  </div>
</section>
```

**Design:**
- Organized by category (Simple Mode, Individual Agents, Workflows)
- Example cards with:
  - Title and description
  - Command/code example
  - Expected output/result
- Code blocks with copy buttons

**CSS Classes:**
- `.examples-categories` (vertical sections)
- `.examples-grid` (grid layout)
- `.example-card` (extends `.doc-card`)
- `.example-description`
- `.example-output` (highlighted output section)

### 9. Footer

**Structure:**
```html
<footer class="footer">
  <div class="footer-content">
    <p>&copy; 2025 TappsCodingAgents. MIT License.</p>
    <p>Version 2.0.6 | Last Updated: January 2026</p>
  </div>
</footer>
```

**Design:**
- Simple footer
- Copyright and version info
- Consistent with other HTML docs

**CSS Classes:**
- `.footer` (from styles.css)
- `.footer-content` (from styles.css)

## Layout Structure

### Page Layout
```
┌─────────────────────────────────────┐
│         Navigation Bar              │
├─────────────────────────────────────┤
│                                     │
│      Hero/Overview Section          │
│                                     │
├─────────────────────────────────────┤
│                                     │
│      Getting Started Section        │
│                                     │
├─────────────────────────────────────┤
│                                     │
│      Simple Mode Section            │
│                                     │
├─────────────────────────────────────┤
│                                     │
│      Agent Reference Section        │
│                                     │
├─────────────────────────────────────┤
│                                     │
│      Features Section               │
│                                     │
├─────────────────────────────────────┤
│                                     │
│      Command Reference Section      │
│                                     │
├─────────────────────────────────────┤
│                                     │
│      Examples Section               │
│                                     │
├─────────────────────────────────────┤
│           Footer                    │
└─────────────────────────────────────┘
```

### Responsive Breakpoints

**Mobile (< 768px):**
- Single column layout
- Stacked cards
- Reduced padding (2rem)
- Smaller font sizes
- Hamburger menu (if needed)

**Tablet (768px - 1024px):**
- 2-column grids where appropriate
- Standard padding (3rem)
- Standard font sizes

**Desktop (> 1024px):**
- 3-column grids for features/agents
- Full padding (4rem)
- Larger font sizes
- Full navigation visible

## Interactive Elements

### Code Blocks
- Copy button in header
- Syntax highlighting (if JavaScript library added)
- Scrollable for long code
- Language indicator

### Cards
- Hover effects (lift, shadow, border highlight)
- Smooth transitions
- Clickable (if linking to other pages)

### Tables
- Alternating row colors
- Hover effects on rows
- Responsive (horizontal scroll on mobile if needed)

### Buttons
- Primary style (gradient background)
- Hover effects (darker shade)
- Active states
- Focus indicators for accessibility

## Accessibility Features

### Semantic HTML
- Proper heading hierarchy (h1 → h2 → h3)
- Landmark regions (`<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`)
- List elements for lists
- Table elements for tabular data

### ARIA Labels
- Navigation landmarks
- Button labels
- Table headers
- Section labels

### Keyboard Navigation
- Tab order logical
- Skip to content link
- Focus indicators (2px solid outline)
- Keyboard shortcuts (if applicable)

### Screen Reader Support
- Alt text for icons/images
- Descriptive link text
- Proper heading structure
- Landmark regions

## Animation & Transitions

### Hover Effects
- Cards: `transform: translateY(-4px)`, `box-shadow` increase, `border-color` change
- Buttons: Background color transition
- Links: Underline animation (if applicable)

### Transitions
- All interactive elements: `transition: 0.2s ease`
- Smooth scroll behavior: `scroll-behavior: smooth`

### Loading States
- Not applicable (static content)

## Typography Hierarchy

```
h1 (Hero Title)
  ├─ Large gradient text (3rem)
  └─ Center-aligned

h2 (Section Titles)
  ├─ 2rem, primary color
  └─ Margin-bottom: 2rem

h3 (Subsection Titles)
  ├─ 1.5rem, primary color
  └─ Margin-bottom: 1rem

h4 (Card Titles)
  ├─ 1.25rem, text-primary
  └─ Margin-bottom: 0.5rem

p (Body Text)
  ├─ 1rem, text-secondary
  └─ Line-height: 1.6

.lead (Intro Text)
  ├─ 1.25rem, text-secondary
  └─ Margin-bottom: 1.5rem
```

## Spacing System

### Vertical Rhythm
- Section spacing: 4rem
- Subsection spacing: 2rem
- Card internal padding: 2rem
- Grid gaps: 2rem
- Element spacing: 1rem - 1.5rem

### Horizontal Spacing
- Container max-width: 1400px
- Container padding: 2rem (mobile), 3rem (desktop)
- Grid gaps: 2rem

## Component Reusability

All components use existing CSS classes from `styles.css` where possible:
- `.doc-card` - Reusable card component
- `.code-block` - Code display
- `.alert` - Alert/info boxes
- `.features-grid` - Grid layout
- `.navbar`, `.footer` - Navigation and footer

New CSS classes should be minimal and follow existing patterns.

## Design Consistency Checklist

- ✅ Uses existing color palette (CSS variables)
- ✅ Matches typography system
- ✅ Consistent spacing (rem-based)
- ✅ Reuses existing component classes
- ✅ Same navigation structure
- ✅ Same footer structure
- ✅ Consistent card styles
- ✅ Consistent code block styles
- ✅ Same responsive breakpoints
- ✅ Consistent hover/transition effects

