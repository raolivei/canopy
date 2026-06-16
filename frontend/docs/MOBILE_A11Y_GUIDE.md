# Mobile & Accessibility (A11y) Guide

This document outlines the mobile responsiveness and accessibility improvements implemented in Canopy frontend (issue #57).

## Mobile Breakpoints (375px+ Support)

### Tailwind Configuration

Added a custom `sm:` breakpoint for 375px viewport (iPhone SE, small Android devices):

```javascript
theme: {
  screens: {
    'sm': '375px',   // Mobile-first: iPhone SE, small Android devices
    'md': '768px',   // Tablets
    'lg': '1024px',  // Desktops
    'xl': '1280px',  // Wide desktops
    '2xl': '1536px', // Ultra-wide
  },
}
```

### Mobile-First Approach

All components use mobile-first responsive design:
- Default styles apply to small (375px) viewports
- Use `sm:`, `md:`, `lg:` prefixes to override on larger screens
- Avoid `max-width` media queries; use mobile base + responsive increases

Example:
```tsx
// Mobile-first: 375px defaults, then scales up
<div className="px-4 sm:px-6 py-2 sm:py-4">
  <h1 className="text-base sm:text-lg md:text-xl">Heading</h1>
</div>
```

## Accessibility Features

### ARIA Attributes

All interactive components include proper ARIA attributes:

#### Button Component
- `aria-label`: Describe button action (required for icon buttons)
- `aria-busy="true"`: When loading state is active
- `aria-hidden="true"`: Decorative icons

```tsx
<Button 
  ariaLabel="Submit form" 
  loading 
  loadingText="Submitting..."
>
  Submit
</Button>
```

#### Input Component
- `aria-label` (or `label` prop): Associates input with description
- `aria-invalid="true"`: When input has validation error
- `aria-describedby`: Links to error/helper text IDs
- Required indicator (`*`) with `aria-label="required"`

```tsx
<Input 
  label="Email" 
  required 
  error="Invalid email"
  helperText="Use your corporate email"
/>
```

#### Modal Component
- `role="dialog"`: Semantic dialog element
- `aria-modal="true"`: Indicates modal overlay
- `aria-labelledby`: Links to modal title
- `aria-describedby`: Links to modal description
- Focus trap and escape key handling

```tsx
<Modal 
  isOpen={open} 
  onClose={closeModal}
  title="Confirm Action"
  description="This action cannot be undone"
>
  {/* Content */}
</Modal>
```

#### Card Component
- `focus-within:ring-2`: Visual indicator when focused
- Proper semantic heading levels (`<h1>`, `<h2>`, etc.)

### Focus Management

- **Visible focus indicators**: 2px ring outline on all interactive elements
- **Focus trap in modals**: Focus returns to trigger on close
- **Keyboard navigation**: All interactive elements are keyboard accessible

### Semantic HTML

- Use proper heading hierarchy (`<h1>`, `<h2>`, `<h3>`)
- Use `<label>` with `htmlFor` for form controls
- Use `<button>` for interactive elements (not `<div onClick>`)
- Use `<nav>`, `<main>`, `<section>` for page structure

## Dark Mode Accessibility

### Color Contrast

All colors meet WCAG AA standards (4.5:1 for text, 3:1 for UI components):
- **Light mode**: White backgrounds with dark text/colors
- **Dark mode**: Slate-900 (near-black) with light text/colors

### Dark Mode on Mobile

To test dark mode on mobile:

```bash
# Start dev server
cd frontend
npm run dev

# On iPhone/mobile:
1. Visit http://localhost:3001
2. Settings > Display & Brightness > Dark Mode
3. Verify component contrast and readability
```

### Media Query Support

```css
@media (prefers-color-scheme: dark) {
  /* Dark mode styles */
}
```

## Testing & Validation

### Unit Tests

Run accessibility tests with Axe:

```bash
npm test -- accessibility.test.tsx
```

Tests validate:
- ARIA attributes presence and correctness
- Semantic HTML structure
- Color contrast ratios
- Focus management
- Keyboard navigation

### Axe Audit

Automated accessibility audit using `axe-core`:

```bash
npm run test:a11y
```

This scans components for WCAG 2.1 Level AA violations:
- Missing ARIA labels
- Poor color contrast
- Broken semantic structure
- Keyboard traps
- Invalid ARIA usage

### Manual Testing

Test on real mobile devices:

```bash
# Expose dev server to network
npm run dev -- --hostname 0.0.0.0

# On mobile device browser:
http://<your-ip>:3001
```

Test scenarios:
1. **Portrait orientation**: 375-480px width
2. **Landscape orientation**: 667-812px width
3. **Dark mode**: Both light and dark themes
4. **Touch interactions**: All buttons/links with 44x44px min tap target
5. **Keyboard navigation**: Tab through all interactive elements
6. **Screen reader**: VoiceOver (iOS), TalkBack (Android)

### Smoke Test at localhost:3001

```bash
cd canopy
docker-compose up -d

# Frontend at http://localhost:3001
# API at http://localhost:8001
# PostgreSQL at localhost:5433
# Redis at localhost:6380
```

Verify:
- Page loads without errors
- Layout adapts to 375px viewport
- Dark mode toggle works
- All buttons and forms are accessible
- No JavaScript console errors

## Component-Specific Guidelines

### Responsive Padding & Margin

All UI components use mobile-first responsive spacing:

```tsx
// Card component example
<Card>
  <CardHeader className="sm:px-6 sm:py-4 px-4 py-3">
    {/* Smaller padding on mobile, larger on sm+ */}
  </CardHeader>
</Card>
```

### Button Sizing

Mobile-optimized touch targets:

```tsx
<Button size="md">
  {/* Mobile: 16px x 32px (38px height with padding) */}
  {/* sm+:  16px x 36px (44px height with padding) */}
</Button>
```

Ensures minimum 44x44px touch target on mobile.

### Input Fields

Mobile-friendly form inputs:

```tsx
<Input 
  label="Email"
  placeholder="you@example.com"
  inputSize="md"
  {/* Mobile: 16px text (prevents zoom on iOS) */}
  {/* sm+:   16px/base text */}
/>
```

### Modal Overflow

Modals handle small screens gracefully:

```tsx
<Modal isOpen={open} onClose={closeModal}>
  {/* Mobile: full viewport minus padding */}
  {/* sm+:   sized container with scrollable content */}
</Modal>
```

## Resources

### WCAG 2.1 Level AA
- https://www.w3.org/WAI/WCAG21/quickref/
- https://www.w3.org/WAI/fundamentals/

### Tailwind CSS Responsive Design
- https://tailwindcss.com/docs/responsive-design

### React Accessibility
- https://react.dev/learn/accessibility
- https://www.w3.org/WAI/tutorials/

### Testing Tools
- Axe DevTools: https://www.deque.com/axe/devtools/
- WAVE: https://wave.webaim.org/
- Lighthouse (Chrome DevTools)

## Checklist for New Components

When adding new components, ensure:

- [ ] Mobile responsive (375px+ tested)
- [ ] ARIA labels for all interactive elements
- [ ] Focus indicators visible (ring-2 on focus/focus-within)
- [ ] Color contrast meets WCAG AA (4.5:1 text)
- [ ] Dark mode styles verified
- [ ] Keyboard navigation functional
- [ ] Touch targets minimum 44x44px
- [ ] Semantic HTML used
- [ ] Tested with screen reader
- [ ] Unit tests with Axe audit

## Common Patterns

### Icon Buttons
```tsx
<Button ariaLabel="Delete item">
  <Trash2 size={20} />
</Button>
```

### Form Validation
```tsx
<Input
  label="Email"
  error={errors.email}
  helperText="Use your corporate email"
/>
```

### Loading States
```tsx
<Button loading loadingText="Saving...">
  Save
</Button>
```

### Responsive Text
```tsx
<h1 className="text-xl sm:text-2xl md:text-3xl font-bold">
  Responsive Heading
</h1>
```

---

**Last Updated**: June 13, 2026
**Issue**: #57 Mobile/A11y
