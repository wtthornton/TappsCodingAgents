# Step 4: @designer - Component Design & Structure

## Design System Overview

### Design Philosophy
- **Modern & Futuristic:** Cutting-edge visual design with 2025 web technologies
- **Dark First:** Optimized for dark theme with multiple variants
- **Performance Focused:** Smooth 60fps animations and interactions
- **Accessible:** WCAG 2.1 AAA compliance
- **Interactive:** Delightful micro-interactions and animations
- **Creative:** Unique visual effects and creative implementations

## 1. Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│ Header (Sticky, Glassmorphism, Height: 80px)          │
│ ┌──────────────┐  ┌────────────┐  ┌─────────────┐    │
│ │ Logo/Gradient│  │ Navigation │  │Theme Switcher│    │
│ │     Text     │  │   Links    │  │  + Feature  │    │
│ └──────────────┘  └────────────┘  │  Detection  │    │
│                                    └─────────────┘    │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Hero Section (100vh, Centered Content)                 │
│                                                         │
│         [Animated Gradient Background]                 │
│                                                         │
│              Gradient Animated Title                    │
│                  (clamp 2.5-5rem)                      │
│                                                         │
│              Descriptive Subtitle                       │
│                  (clamp 1.1-1.5rem)                    │
│                                                         │
│              [Magnetic CTA Button]                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Feature Showcase Section (Padding: 6rem 2rem)         │
│                                                         │
│         Section Title (Centered)                       │
│                                                         │
│  ┌────────┐  ┌────────┐  ┌────────┐                  │
│  │Feature │  │Feature │  │Feature │                  │
│  │ Card 1 │  │ Card 2 │  │ Card 3 │                  │
│  │ (3D)   │  │ (3D)   │  │ (3D)   │                  │
│  └────────┘  └────────┘  └────────┘                  │
│  ┌────────┐  ┌────────┐  ┌────────┐                  │
│  │Feature │  │Feature │  │Feature │                  │
│  │ Card 4 │  │ Card 5 │  │ Card 6 │                  │
│  │ (3D)   │  │ (3D)   │  │ (3D)   │                  │
│  └────────┘  └────────┘  └────────┘                  │
│  (Container Queries for responsive grid)               │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Interactive Timeline Section                           │
│                                                         │
│  [Timeline with scrollable feature cards]              │
│  - Horizontal scrollable timeline                      │
│  - Feature cards with dates/categories                 │
│  - Smooth scroll animations                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Canvas Particle System Section (Full-width)            │
│                                                         │
│         [Canvas Element - 100vh]                       │
│                                                         │
│  - Interactive particle system                         │
│  - Mouse tracking influences particles                 │
│  - Click to create particle bursts                     │
│  - Connection lines between particles                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Live Feature Demos Section                             │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐                   │
│  │  Demo Card 1 │  │  Demo Card 2 │                   │
│  │  [Interactive│  │  [Interactive│                   │
│  │   Demo]      │  │   Demo]      │                   │
│  └──────────────┘  └──────────────┘                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Feature Detection Dashboard (Floating Widget)          │
│                                                         │
│  ┌──────────────────────────────────────┐             │
│  │ Feature Support Status               │             │
│  │ ✅ CSS Cascade Layers                │             │
│  │ ✅ Container Queries                 │             │
│  │ ✅ :has() Selector                   │             │
│  │ ❌ WebGPU (Not supported)            │             │
│  │ ...                                  │             │
│  └──────────────────────────────────────┘             │
│                                                         │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Performance Monitor (Optional, Toggle)                 │
│                                                         │
│  ┌──────────────────┐                                  │
│  │ FPS: 60          │                                  │
│  │ Load: 1.2s       │                                  │
│  │ Particles: 150   │                                  │
│  └──────────────────┘                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Footer                                                 │
│                                                         │
│  Copyright, Links, Credits                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 2. Color Palette Design

### Theme 1: Deep Space (Default)
```css
/* Background Colors */
--bg-primary: #0a0a0f          /* Deep space black */
--bg-secondary: color-mix(in srgb, #151520 90%, #6366f1 10%)  /* Dark with indigo tint */
--bg-tertiary: #1e1e2e          /* Charcoal */
--bg-quaternary: #2a2a3e         /* Lighter charcoal */
--bg-glass: rgba(26, 26, 46, 0.7)  /* Glassmorphism background */

/* Accent Colors */
--accent-primary: #6366f1        /* Indigo */
--accent-secondary: #8b5cf6      /* Purple */
--accent-tertiary: #ec4899       /* Pink */
--accent-quaternary: #4facfe      /* Blue */
--accent-quinary: #43e97b         /* Green */

/* Text Colors */
--text-primary: #f8fafc          /* Almost white (WCAG AAA: 7:1) */
--text-secondary: #cbd5e1        /* Light gray */
--text-muted: #94a3b8            /* Gray */
--text-accent: #6366f1           /* Accent colored text */

/* Gradient Definitions */
--gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
--gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%)
--gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)
--gradient-4: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)
--gradient-hero: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)

/* Shadow & Glow */
--shadow-glow: 0 0 20px rgba(99, 102, 241, 0.3)
--shadow-glow-strong: 0 0 40px rgba(99, 102, 241, 0.5)
--shadow-card: 0 8px 32px rgba(0, 0, 0, 0.4)
--shadow-elevated: 0 16px 48px rgba(0, 0, 0, 0.6)

/* Border Colors */
--border-primary: rgba(255, 255, 255, 0.1)
--border-accent: rgba(99, 102, 241, 0.3)
--border-glow: rgba(99, 102, 241, 0.5)
```

### Theme 2: Cyberpunk
```css
/* Background Colors */
--bg-primary: #0a0a0a           /* Pure black */
--bg-secondary: color-mix(in srgb, #1a0a1a 85%, #00ff88 15%)  /* Dark with green tint */
--bg-tertiary: #1a1a2e          /* Dark blue-gray */
--bg-glass: rgba(26, 10, 26, 0.8)  /* Glassmorphism */

/* Accent Colors */
--accent-primary: #00ff88        /* Neon green */
--accent-secondary: #ff0080      /* Neon pink */
--accent-tertiary: #00ffff       /* Cyan */
--accent-quaternary: #ffaa00     /* Orange */

/* Text Colors */
--text-primary: #00ff88          /* Neon green text */
--text-secondary: #88ffaa        /* Light green */
--text-muted: #44aa66            /* Muted green */

/* Gradients */
--gradient-1: linear-gradient(135deg, #00ff88 0%, #00ffff 100%)
--gradient-2: linear-gradient(135deg, #ff0080 0%, #ffaa00 100%)
--gradient-hero: linear-gradient(135deg, #00ff88 0%, #00ffff 50%, #ff0080 100%)

/* Glow Effects (Stronger for cyberpunk) */
--shadow-glow: 0 0 30px rgba(0, 255, 136, 0.6)
--shadow-glow-strong: 0 0 60px rgba(0, 255, 136, 0.8)
```

### Theme 3: Elegant
```css
/* Background Colors */
--bg-primary: #0f0f14           /* Deep elegant black */
--bg-secondary: color-mix(in srgb, #1a1a20 90%, #d4af37 10%)  /* Dark with gold tint */
--bg-tertiary: #252530          /* Warm dark gray */
--bg-glass: rgba(37, 37, 48, 0.7)  /* Glassmorphism */

/* Accent Colors */
--accent-primary: #d4af37        /* Gold */
--accent-secondary: #c9a961      /* Light gold */
--accent-tertiary: #b8860b      /* Dark goldenrod */
--accent-quaternary: #f4e4bc     /* Cream */

/* Text Colors */
--text-primary: #f5f5f5          /* Off-white */
--text-secondary: #d4d4d4        /* Light gray */
--text-muted: #a0a0a0            /* Medium gray */

/* Gradients */
--gradient-1: linear-gradient(135deg, #d4af37 0%, #c9a961 100%)
--gradient-2: linear-gradient(135deg, #f4e4bc 0%, #d4af37 100%)
--gradient-hero: linear-gradient(135deg, #d4af37 0%, #c9a961 50%, #f4e4bc 100%)

/* Subtle Shadows */
--shadow-glow: 0 0 15px rgba(212, 175, 55, 0.2)
--shadow-glow-strong: 0 0 30px rgba(212, 175, 55, 0.3)
```

## 3. Typography Scale

### Font Families
```css
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif
--font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace
```

### Type Scale (Responsive with clamp)
```css
/* Headings */
--font-size-h1: clamp(2.5rem, 8vw, 5rem)        /* Hero title */
--font-size-h2: clamp(2rem, 5vw, 3.5rem)        /* Section titles */
--font-size-h3: clamp(1.5rem, 3vw, 2.25rem)     /* Subsection titles */
--font-size-h4: clamp(1.25rem, 2vw, 1.75rem)    /* Card titles */
--font-size-h5: 1.25rem                         /* Small headings */
--font-size-h6: 1.125rem                        /* Smallest headings */

/* Body Text */
--font-size-body-lg: clamp(1.1rem, 2vw, 1.5rem)  /* Hero description, large body */
--font-size-body: 1rem                           /* Standard body text */
--font-size-body-sm: 0.9375rem                    /* Small body text */
--font-size-caption: 0.875rem                     /* Captions, labels */

/* Weights */
--font-weight-light: 300
--font-weight-normal: 400
--font-weight-medium: 500
--font-weight-semibold: 600
--font-weight-bold: 700
--font-weight-extrabold: 800

/* Line Heights */
--line-height-tight: 1.2
--line-height-normal: 1.5
--line-height-relaxed: 1.75
--line-height-loose: 2

/* Letter Spacing */
--letter-spacing-tight: -0.025em
--letter-spacing-normal: 0
--letter-spacing-wide: 0.025em
--letter-spacing-wider: 0.05em
```

### Typography Usage
```css
h1 {
  font-size: var(--font-size-h1);
  font-weight: var(--font-weight-extrabold);
  line-height: var(--line-height-tight);
  letter-spacing: var(--letter-spacing-tight);
  background: var(--gradient-hero);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

h2 {
  font-size: var(--font-size-h2);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
}

h3 {
  font-size: var(--font-size-h3);
  font-weight: var(--font-weight-semibold);
  line-height: var(--line-height-normal);
}

p {
  font-size: var(--font-size-body);
  line-height: var(--line-height-relaxed);
  color: var(--text-secondary);
}
```

## 4. Spacing System

### Spacing Scale (8px base unit)
```css
--spacing-xs: 0.25rem    /* 4px */
--spacing-sm: 0.5rem     /* 8px */
--spacing-md: 1rem       /* 16px */
--spacing-lg: 1.5rem     /* 24px */
--spacing-xl: 2rem       /* 32px */
--spacing-2xl: 3rem      /* 48px */
--spacing-3xl: 4rem      /* 64px */
--spacing-4xl: 6rem      /* 96px */
--spacing-5xl: 8rem      /* 128px */
```

### Component Spacing
```css
/* Padding */
--padding-xs: var(--spacing-sm)      /* 0.5rem - Tight padding */
--padding-sm: var(--spacing-md)      /* 1rem - Small padding */
--padding-md: var(--spacing-lg)      /* 1.5rem - Medium padding */
--padding-lg: var(--spacing-xl)      /* 2rem - Large padding */
--padding-xl: var(--spacing-2xl)     /* 3rem - Extra large padding */
--padding-section: var(--spacing-4xl) /* 6rem - Section padding */

/* Gaps */
--gap-xs: var(--spacing-sm)          /* 0.5rem */
--gap-sm: var(--spacing-md)          /* 1rem */
--gap-md: var(--spacing-lg)          /* 1.5rem */
--gap-lg: var(--spacing-xl)          /* 2rem */
--gap-xl: var(--spacing-2xl)         /* 3rem */

/* Margins */
--margin-xs: var(--spacing-sm)
--margin-sm: var(--spacing-md)
--margin-md: var(--spacing-lg)
--margin-lg: var(--spacing-xl)
--margin-xl: var(--spacing-2xl)
--margin-section: var(--spacing-4xl)
```

## 5. Component Specifications

### Feature Showcase Card Component
```
┌─────────────────────────────────────┐
│                                     │
│         🎨 Icon (4rem)              │
│      (Gradient fill, animated)      │
│                                     │
│      Feature Title                  │
│      (1.5rem, semibold)            │
│                                     │
│   Description text here that        │
│   explains the feature in detail    │
│   (secondary color, 1rem)           │
│                                     │
│   ┌─────────────────────────────┐  │
│   │  Support: ✅ Supported      │  │
│   └─────────────────────────────┘  │
│                                     │
│   [Hover: Lift + Glow + 3D Tilt]   │
│                                     │
└─────────────────────────────────────┘

Properties:
- Container: @container (max-width: 400px) → stacked layout
- Container: @container (min-width: 400px) → side-by-side
- Background: Glassmorphism with backdrop-filter: blur(20px)
- Border: 1px solid rgba(255, 255, 255, 0.1)
- Border Radius: 1.5rem
- Padding: 2rem
- Hover: translateY(-12px) rotateX(5deg), box-shadow glow
- Animation: Fade-in on scroll (Intersection Observer)
- 3D Transform: transform-style: preserve-3d, perspective: 1000px
```

### Magnetic Button Component
```
┌────────────────────────────┐
│      Button Text           │
│   (Gradient background)    │
│                            │
│  [Magnetic Effect: Moves   │
│   toward cursor on hover]  │
│                            │
│  Hover: Scale 1.05, Glow   │
│  Active: Scale 0.95        │
│  Click: Ripple effect      │
└────────────────────────────┘

Properties:
- Padding: 1rem 2.5rem
- Border Radius: 50px (pill shape)
- Background: Gradient (primary gradient)
- Color: White text
- Font Weight: 600
- Magnetic Effect: Moves up to 10px toward cursor
- Transition: All 0.3s cubic-bezier(0.4, 0, 0.2, 1)
- Cursor: Pointer
```

### Glassmorphism Header Component
```
┌──────────────────────────────────────────────────────┐
│  backdrop-filter: blur(20px) saturate(180%)         │
│  background: rgba(26, 26, 46, 0.7)                  │
│  border-bottom: 1px solid rgba(255, 255, 255, 0.1)  │
│                                                      │
│  Height: 80px                                        │
│  Position: sticky, top: 0                           │
│  Z-index: 1000                                       │
│                                                      │
│  [Logo]  [Nav Links]  [Theme Switcher]              │
│                                                      │
│  Scrolled State:                                     │
│  background: rgba(10, 10, 15, 0.95)                 │
│  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3)          │
└──────────────────────────────────────────────────────┘
```

### Canvas Particle System Component
```
Canvas Element:
- Width: 100%
- Height: 100vh
- Position: Fixed or relative
- Background: Transparent or subtle gradient

Particle Properties:
- Size: 2-4px (random)
- Color: HSL based on position (gradient)
- Opacity: 0.5-1.0 (random)
- Speed: 0.5-2px/frame (random)
- Life: Infinite or fade out

Connection System:
- Distance threshold: 120px
- Line color: Gradient based on particles
- Line opacity: 0.1-0.3 (based on distance)
- Line width: 1px

Interaction:
- Mouse proximity: Particles move toward/away from cursor
- Click: Create particle burst (10-20 particles)
- Smooth 60fps animation loop
```

### Interactive Timeline Component
```
Horizontal Scrollable Timeline:
┌──────────────────────────────────────────────────────┐
│  [←]  Timeline Scroll  [→]                          │
│                                                      │
│  ┌────┐  ┌────┐  ┌────┐  ┌────┐  ┌────┐           │
│  │2020│  │2021│  │2022│  │2023│  │2024│           │
│  │Card│  │Card│  │Card│  │Card│  │Card│           │
│  └────┘  └────┘  └────┘  └────┘  └────┘           │
│                                                      │
│  Scroll Progress: ▓▓▓▓▓▓▓▓░░ 75%                   │
└──────────────────────────────────────────────────────┘

Properties:
- Container: Horizontal scrollable container
- Cards: Fixed width (300px), flex-shrink: 0
- Scroll: Smooth scroll behavior
- Progress Indicator: Visual progress bar
- Active Card: Highlighted with glow effect
```

## 6. Animation Specifications

### Fade-In on Scroll
```css
Initial State:
  opacity: 0
  transform: translateY(30px)

Final State:
  opacity: 1
  transform: translateY(0)

Duration: 0.6s
Easing: ease-out
Trigger: Intersection Observer (when element enters viewport)
```

### 3D Card Hover Effect
```css
Initial State:
  transform: translateY(0) rotateX(0) rotateY(0)

Hover State:
  transform: translateY(-12px) rotateX(5deg) rotateY(2deg)

Duration: 0.4s
Easing: cubic-bezier(0.4, 0, 0.2, 1)
Perspective: 1000px (on parent)
Transform-style: preserve-3d
```

### Magnetic Button Effect
```javascript
// Proximity-based movement
Distance from cursor: d
Movement threshold: 100px
Movement amount: (100 - d) / 10 pixels
Maximum movement: 10px

CSS Transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)
```

### Scroll Progress Animation
```css
Animation: scroll-progress linear
Timeline: scroll()
Range: 0% 100%
Width: 0% → 100% based on scroll position
Height: 4px
Background: Gradient (primary gradient)
Position: Fixed top, z-index: 9999
```

### Glitch Effect Animation
```css
@keyframes glitch {
  0%, 100% {
    transform: translate(0);
    filter: hue-rotate(0deg);
  }
  20% {
    transform: translate(-2px, 2px);
    filter: hue-rotate(90deg);
  }
  40% {
    transform: translate(-2px, -2px);
    filter: hue-rotate(180deg);
  }
  60% {
    transform: translate(2px, 2px);
    filter: hue-rotate(270deg);
  }
  80% {
    transform: translate(2px, -2px);
    filter: hue-rotate(360deg);
  }
}

Duration: 0.3s
Trigger: Random on hover, or on scroll
```

### Shimmer Loading Effect
```css
Background: linear-gradient(
  90deg,
  rgba(255, 255, 255, 0) 0%,
  rgba(255, 255, 255, 0.1) 50%,
  rgba(255, 255, 255, 0) 100%
)
Background-size: 200% 100%
Animation: shimmer 1.5s infinite
Transform: translateX(-100%) → translateX(100%)
```

### Gradient Text Animation
```css
Background: Gradient (animated)
Background-size: 200% 200%
Animation: gradientShift 5s ease infinite
Background-position: 0% 50% → 100% 50% → 0% 50%
-webkit-background-clip: text
-webkit-text-fill-color: transparent
```

## 7. Responsive Breakpoints

### Viewport Breakpoints
```css
/* Mobile First Approach */
Base: 0px (mobile)
  - Single column layout
  - Stacked cards
  - Full-width sections

Tablet: 768px
  - Two-column grid for cards
  - Adjusted spacing
  - Larger typography

Desktop: 1024px
  - Three-column grid for cards
  - Full navigation visible
  - Side-by-side layouts

Large Desktop: 1400px (max-width container)
  - Four-column grid possible
  - Optimal spacing
  - Maximum content width
```

### Container Query Breakpoints
```css
/* Container Queries for Component Responsiveness */
@container (max-width: 350px) {
  /* Stacked layout for small containers */
}

@container (min-width: 350px) and (max-width: 600px) {
  /* Medium container layout */
}

@container (min-width: 600px) {
  /* Large container layout */
}
```

## 8. Accessibility Design

### Focus Indicators
```css
Focus Outline:
  outline: 2px solid var(--accent-primary)
  outline-offset: 4px
  border-radius: 4px

Focus Visible:
  Use :focus-visible pseudo-class
  Only show outline on keyboard navigation
  Hide on mouse clicks
```

### Reduced Motion Support
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  .animated-bg {
    animation: none;
  }
}
```

### Keyboard Navigation
- **Tab Order:** Logical focus flow (header → hero → sections → footer)
- **Enter/Space:** Activate buttons and interactive elements
- **Arrow Keys:** Navigate within components (timeline, feature cards)
- **Escape:** Close modals/overlays
- **Skip Links:** Jump to main content (visually hidden until focused)

### Screen Reader Support
- Semantic HTML5 structure (header, nav, main, section, footer)
- ARIA labels for interactive elements
- ARIA live regions for dynamic content updates
- Proper heading hierarchy (h1 → h2 → h3)
- Alt text for icons (using aria-label)
- Role attributes where needed

### Color Contrast Ratios (WCAG AAA)
- **Normal Text:** 7:1 minimum (primary text: #f8fafc on #0a0a0f = 16.5:1 ✅)
- **Large Text (18pt+):** 4.5:1 minimum
- **UI Components:** 3:1 minimum for interactive elements
- **Focus Indicators:** 3:1 contrast with background

## 9. Performance Targets

### Loading Performance
- **First Contentful Paint (FCP):** < 1.0s
- **Largest Contentful Paint (LCP):** < 2.5s
- **Time to Interactive (TTI):** < 3.0s
- **Total Blocking Time (TBT):** < 200ms
- **Cumulative Layout Shift (CLS):** < 0.1

### Animation Performance
- **Target FPS:** 60fps
- **Minimum FPS:** 30fps (acceptable)
- **Frame Budget:** 16.67ms per frame
- **Animation Optimizations:** Use transform and opacity only

### Canvas Performance
- **Particle Count:** Maximum 150-200 particles
- **Connection Distance:** 120px threshold
- **Frame Skipping:** Reduce updates on low-end devices
- **Optimization:** Object pooling, efficient drawing methods

### Lighthouse Score Targets
- **Performance:** > 90
- **Accessibility:** > 95
- **Best Practices:** > 90
- **SEO:** > 90

## 10. Design Tokens

### Border Radius
```css
--radius-sm: 0.5rem      /* 8px - Small elements */
--radius-md: 1rem        /* 16px - Cards, buttons */
--radius-lg: 1.5rem      /* 24px - Large cards */
--radius-xl: 2rem        /* 32px - Extra large */
--radius-full: 9999px    /* Pill shape */
```

### Shadows
```css
--shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1)
--shadow-md: 0 4px 16px rgba(0, 0, 0, 0.2)
--shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.4)
--shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.6)
--shadow-glow: 0 0 20px rgba(99, 102, 241, 0.3)
--shadow-glow-strong: 0 0 40px rgba(99, 102, 241, 0.5)
```

### Transitions
```css
--transition-fast: 0.15s ease
--transition-base: 0.3s ease
--transition-slow: 0.5s ease
--transition-bounce: 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55)
```

### Z-Index Scale
```css
--z-base: 1
--z-dropdown: 100
--z-sticky: 200
--z-fixed: 300
--z-modal-backdrop: 400
--z-modal: 500
--z-popover: 600
--z-tooltip: 700
--z-scroll-progress: 9999
```


