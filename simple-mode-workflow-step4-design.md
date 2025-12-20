# Step 4: @designer - Component Design & Structure

## Component Design Specifications

### 1. Layout Structure

```
┌─────────────────────────────────────┐
│ Header (Sticky, Glassmorphism)     │
│ - Logo                              │
│ - Navigation Links                  │
│ - Theme Toggle                      │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Hero Section (100vh)                │
│ - Animated Background               │
│ - Centered Content                  │
│   - Gradient Title                  │
│   - Description                     │
│   - CTA Button                      │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Features Section                    │
│ - Section Title                     │
│ - Features Grid (Container Queries) │
│   ┌──────┐ ┌──────┐ ┌──────┐      │
│   │Card 1│ │Card 2│ │Card 3│      │
│   └──────┘ └──────┘ └──────┘      │
│   ┌──────┐ ┌──────┐ ┌──────┐      │
│   │Card 4│ │Card 5│ │Card 6│      │
│   └──────┘ └──────┘ └──────┘      │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Showcase Section                    │
│ - Section Title                     │
│ - Showcase Grid                     │
│   (8 showcase items)                │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ Demo Section                        │
│ - Canvas Animation                  │
│ - Interactive Box                   │
│ - 3D Card                           │
│ - Demo Buttons                      │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│ About Section                       │
│ - Feature List                      │
└─────────────────────────────────────┘
```

### 2. Color Palette Design

```css
/* Primary Colors */
--bg-primary: #0a0a0f (Deep Space Black)
--bg-secondary: color-mix(in srgb, #151520 90%, #6366f1 10%)
--bg-tertiary: #1e1e2e (Charcoal)

/* Accent Colors */
--accent-primary: #6366f1 (Indigo)
--accent-secondary: #8b5cf6 (Purple)
--accent-tertiary: #ec4899 (Pink)
--accent-quaternary: #4facfe (Blue)

/* Text Colors */
--text-primary: #f8fafc (Almost White)
--text-secondary: #cbd5e1 (Light Gray)
--text-muted: #94a3b8 (Gray)

/* Gradients */
--gradient-1: Indigo to Purple
--gradient-2: Pink to Red
--gradient-3: Blue to Cyan
--gradient-4: Green to Turquoise
```

### 3. Component Specifications

#### Feature Card Component
```
┌────────────────────────┐
│ 🎨 Icon (3rem)         │
│                        │
│ Feature Title          │
│ (1.5rem, bold)         │
│                        │
│ Description text       │
│ (secondary color)      │
│                        │
│ [Hover: Lift + Glow]   │
└────────────────────────┘

Properties:
- Container Query: @container (max-width: 350px)
- Hover: translateY(-10px), border-color change
- Animation: Fade-in on scroll
- Background: Gradient overlay on hover
```

#### Interactive Box Component
```
┌──────────────────────────────┐
│  [Animated Conic Border]     │
│                              │
│    Centered Content          │
│    - Title                   │
│    - Description             │
│    - Button                  │
│                              │
│  [Canvas Overlay]            │
│  [Particle System]           │
│                              │
│  Hover: 3D Perspective Tilt  │
└──────────────────────────────┘
```

#### Canvas Animation System
```
Canvas Element (100% width/height)
│
├── Particle System
│   ├── Particle Class
│   │   ├── Position (x, y)
│   │   ├── Velocity (vx, vy)
│   │   ├── Size
│   │   ├── Life
│   │   └── Color (HSL based on position)
│   │
│   └── Connection System
│       └── Draw lines between nearby particles
│
└── Animation Loop
    └── requestAnimationFrame
        ├── Update particles
        ├── Draw particles
        └── Draw connections
```

### 4. Typography Scale

```css
/* Headings */
h1: clamp(2.5rem, 8vw, 5rem) - Hero title
h2: clamp(2rem, 5vw, 3.5rem) - Section titles
h3: 1.5rem - Card titles

/* Body */
p: clamp(1.1rem, 2vw, 1.5rem) - Hero description
p: 1rem - Body text
small: 0.9rem - Secondary text
```

### 5. Spacing System

```css
/* Padding */
--padding-xs: 0.5rem
--padding-sm: 1rem
--padding-md: 1.5rem
--padding-lg: 2rem
--padding-xl: 2.5rem
--padding-section: 6rem

/* Gaps */
--gap-sm: 1rem
--gap-md: 1.5rem
--gap-lg: 2rem
```

### 6. Animation Specifications

#### Fade-In Animation
```css
Initial: opacity: 0, translateY(30px)
Final: opacity: 1, translateY(0)
Duration: 0.6s
Easing: ease
Trigger: Intersection Observer
```

#### Hover Lift Animation
```css
Initial: translateY(0)
Hover: translateY(-10px)
Duration: 0.4s
Easing: cubic-bezier(0.4, 0, 0.2, 1)
```

#### Scroll Progress Animation
```css
Animation: scroll-progress linear
Timeline: scroll()
Range: 0% 100%
Width: 0% to 100%
```

### 7. Responsive Breakpoints

```css
/* Mobile First */
Base: 0px (mobile)
Tablet: 768px
Desktop: 1024px
Large: 1400px (max-width container)

/* Container Queries */
Small Container: max-width: 350px
Medium Container: 350px - 600px
Large Container: 600px+
```

### 8. Accessibility Design

- **Focus Indicators:** 2px solid outline, 4px offset
- **Reduced Motion:** All animations respect prefers-reduced-motion
- **Keyboard Navigation:** All interactive elements focusable
- **Semantic HTML:** Proper heading hierarchy, landmark regions
- **ARIA Labels:** Theme toggle button labeled
- **Color Contrast:** WCAG AA compliant (4.5:1 for text)

### 9. Performance Targets

- **First Paint:** < 100ms
- **Interactive:** < 1s
- **Animation FPS:** 60fps
- **Lighthouse Score:** 90+ Performance
- **Canvas Particles:** Max 50 for smooth performance

