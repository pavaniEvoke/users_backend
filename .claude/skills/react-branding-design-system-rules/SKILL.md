---
name: react-branding-design-system-rules
description: Use brand design tokens, not hardcoded values; theme via the design system; dark-mode and accessibility by default. Read before writing or editing **/*.tsx, **/*.jsx, components/**.
---
## React branding & design system

- Use design tokens, never hardcoded values. No raw hex/rgb, no magic spacing —
  reference theme tokens (Tailwind `@theme` CSS variables / design-system
  classes). A literal `#3b82f6` in a component is a bug.
- Build from the shared component library (shadcn/ui + brand wrappers) before
  hand-rolling. Don't fork a primitive to restyle it — extend via tokens/variants.
- Support light and dark mode through tokens; don't branch on theme in component
  logic. Respect `prefers-reduced-motion` and `prefers-color-scheme`.
- Accessibility is part of branding: semantic elements, labelled controls,
  visible focus states, AA contrast. Don't remove focus outlines to "clean up" UI.
- Logo, typography, and spacing follow the brand scale — use the spacing/radius
  tokens, don't invent one-off values. Keep brand assets imported from the shared
  package, never copy-pasted.
