---
name: react-rules
description: Composable components, correct hooks usage, accessible markup. Read before writing or editing **/*.tsx, **/*.jsx.
---
## React

- Components are pure functions of props/state. Keep them small and composable.
- Follow the rules of hooks; list complete dependency arrays. Don't reach for
  `useEffect` when derived state or an event handler will do.
- Lift state only as far as needed; prefer local state and composition over
  global stores.
- Use semantic, accessible markup (labels, roles, keyboard support). Don't fix
  a11y with ARIA when native elements work.
- Keys must be stable and unique; never the array index for dynamic lists.
